#!/usr/bin/env python3
"""2장: 명목 스칼라 MPC QP, 종단 집합, 이동 후보의 직접 계산.

무차원 모델 x+=1.1*x+u, |x|<=4, |u|<=1, |x_N|<=0.5.
Q=1, R=0.2, N=5; DARE 종단 비용과 LQR 종단 제어를 사용합니다.
현재 상태는 정확히 알고, 모델 오차/외란은 없습니다. SLSQP로 푼
작은 볼록 QP의 수치 검사이며 임의 시스템의 안정성 증명은 아닙니다.
실행: python chapter02_constrained_mpc.py --output-dir output/chapter02
"""
import argparse
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mpc-example-mpl"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "mpc-example-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import solve_discrete_are
from scipy.optimize import Bounds, LinearConstraint, linprog, minimize

A, B, Q, R, N = 1.1, 1.0, 1.0, 0.2, 5
XMAX, UMAX, XF = 4.0, 1.0, 0.5
P = float(solve_discrete_are([[A]], [[B]], [[Q]], [[R]])[0, 0])
K = -B * P * A / (R + B * P * B)


def prediction(horizon):
    sx = A ** np.arange(1, horizon + 1)
    su = np.zeros((horizon, horizon))
    for i in range(horizon):
        for j in range(i + 1):
            su[i, j] = A ** (i - j) * B
    return sx, su


def trajectory(x0, inputs):
    states = [float(x0)]
    for u in inputs:
        states.append(A * states[-1] + B * u)
    return np.asarray(states)


def cost(x0, inputs):
    states = trajectory(x0, inputs)
    return float(Q * states[:-1] @ states[:-1] + R * inputs @ inputs + P * states[-1]**2)


def solve_mpc(x0, horizon=N):
    sx, su = prediction(horizon)
    limits = np.full(horizon, XMAX)
    limits[-1] = XF
    lower, upper = -limits - sx * x0, limits - sx * x0
    feasibility = linprog(np.zeros(horizon), A_ub=np.vstack((su, -su)),
                          b_ub=np.concatenate((upper, -lower)),
                          bounds=[(-UMAX, UMAX)] * horizon, method="highs")
    if not feasibility.success or abs(x0) > XMAX:
        return None
    weights = np.diag([Q] * (horizon - 1) + [P])
    hessian = 2 * (R * np.eye(horizon) + su.T @ weights @ su)
    linear = 2 * su.T @ weights @ (sx * x0)
    answer = minimize(lambda u: cost(x0, u), feasibility.x,
                      jac=lambda u: hessian @ u + linear,
                      method="SLSQP", bounds=Bounds(-UMAX, UMAX),
                      constraints=[LinearConstraint(su, lower, upper)],
                      options={"ftol": 1e-12, "maxiter": 200})
    assert answer.success, answer.message
    states = trajectory(x0, answer.x)
    assert np.max(np.abs(answer.x)) <= UMAX + 2e-8
    assert np.max(np.abs(states)) <= XMAX + 2e-8
    assert abs(states[-1]) <= XF + 2e-8
    return answer.x, states, cost(x0, answer.x)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("output/chapter02"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    radii = [XF]
    for _ in range(N):
        radii.append(min(XMAX, (radii[-1] + B * UMAX) / abs(A)))
    assert solve_mpc(1.3, 1) is not None
    assert solve_mpc(1.4, 1) is None
    assert abs(K) * XF <= UMAX
    assert abs(A + B * K) * XF <= XF
    terminal_residual = P * (A + B * K)**2 - P + Q + R * K**2
    assert abs(terminal_residual) < 1e-12
    states, inputs, values, margins = [3.0], [], [], []
    for _ in range(20):
        u, predicted, value = solve_mpc(states[-1])
        shifted = np.r_[u[1:], K * predicted[-1]]
        next_x = A * states[-1] + B * u[0]
        shifted_states = trajectory(next_x, shifted)
        assert np.max(np.abs(shifted)) <= UMAX + 2e-8
        assert np.max(np.abs(shifted_states)) <= XMAX + 2e-8
        assert abs(shifted_states[-1]) <= XF + 2e-8
        stage = Q * states[-1]**2 + R * u[0]**2
        shifted_cost = cost(next_x, shifted)
        _, _, next_value = solve_mpc(next_x)
        # The shifted candidate proves an upper bound on next optimal value.
        assert shifted_cost <= value - stage + 2e-7
        assert next_value <= shifted_cost + 2e-7
        margins.append(float(value - stage - next_value))
        values.append(value)
        inputs.append(float(u[0]))
        states.append(float(next_x))
    assert abs(states[-1]) < 1e-5
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), constrained_layout=True)
    axes[0].plot(states, "o-", markersize=3)
    axes[0].axhspan(-XF, XF, color="green", alpha=0.1, label="Terminal set")
    axes[0].set(xlabel="Sample k", ylabel="State x", title="Nominal closed loop")
    axes[0].legend()
    axes[1].step(np.arange(len(inputs)), inputs, where="post")
    axes[1].axhline(UMAX, color="red", linestyle="--")
    axes[1].axhline(-UMAX, color="red", linestyle="--")
    axes[1].set(xlabel="Sample k", ylabel="Input u", title="Input limits")
    axes[2].plot(np.arange(N + 1), radii, "o-")
    axes[2].set(xlabel="Horizon N", ylabel="Feasible-set radius", title="Backward predecessor sets")
    for ax in axes:
        ax.grid(True, alpha=0.25)
    fig.savefig(args.output_dir / "figure.png", dpi=160)
    plt.close(fig)
    result = {"chapter": 2, "status": "passed", "random_seed": None,
              "units": "dimensionless state, input, and cost; sample index time",
              "scope": "Exact-state, disturbance-free scalar constrained MPC",
              "parameters": {"A": A, "B": B, "Q": Q, "R": R, "N": N, "P": P, "K": K},
              "feasible_radii": radii, "terminal_dare_residual": terminal_residual,
              "closed_loop_states": states, "closed_loop_inputs": inputs,
              "optimal_values": values, "minimum_value_decrease_margin": min(margins),
              "checks": ["One-step feasibility separates x=1.3 and x=1.4",
                         "Terminal feedback is admissible and invariant",
                         "Terminal DARE decrease identity", "Every QP reports success",
                         "All state, input, and terminal constraints",
                         "Shifted candidates remain feasible", "Optimal value decrease along the tested trajectory"]}
    (args.output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
