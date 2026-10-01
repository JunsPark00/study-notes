#!/usr/bin/env python3
"""1장: 일정 가속도 이중 적분기의 Euler / 정확한 ZOH 비교.

모델: p_dot=v, v_dot=u; p [m], v [m/s], u [m/s^2], 시간 [s].
입력은 각 샘플 구간에서 일정하고 초기 상태는 [0, 0]입니다.
총 시간 4초를 고정하고 격자를 바꿉니다. MPC 최적화 예제는 아닙니다.
NumPy/SciPy/Matplotlib 외의 코드나 데이터를 사용하지 않습니다.
실행: python chapter01_double_integrator.py --output-dir output/chapter01
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
from scipy.linalg import expm


def simulate(dt, final_time=4.0, acceleration=1.0):
    """Compute both discretizations by repeated matrix-vector transitions."""
    steps = round(final_time / dt)
    assert np.isclose(steps * dt, final_time), "The time grid must end at T."
    ac = np.array([[0.0, 1.0], [0.0, 0.0]])
    bc = np.array([[0.0], [1.0]])
    augmented = np.block([[ac, bc], [np.zeros((1, 3))]])
    block = expm(augmented * dt)
    az, bz = block[:2, :2], block[:2, 2]
    ae, be = np.eye(2) + dt * ac, dt * bc[:, 0]
    assert np.allclose(az, [[1.0, dt], [0.0, 1.0]])
    assert np.allclose(bz, [dt**2 / 2, dt])
    zoh = np.zeros((steps + 1, 2))
    euler = np.zeros_like(zoh)
    for k in range(steps):
        zoh[k + 1] = az @ zoh[k] + bz * acceleration
        euler[k + 1] = ae @ euler[k] + be * acceleration
    time = np.arange(steps + 1) * dt
    exact = np.column_stack((acceleration * time**2 / 2, acceleration * time))
    np.testing.assert_allclose(zoh, exact, atol=2e-13)
    np.testing.assert_allclose(euler[:, 1], exact[:, 1], atol=2e-13)
    expected_error = acceleration * final_time * dt / 2
    assert np.isclose(exact[-1, 0] - euler[-1, 0], expected_error)
    return time, zoh, euler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("output/chapter01"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    grid = np.array([0.8, 0.4, 0.2, 0.1, 0.05])
    errors, rows = [], []
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    fine_t = np.linspace(0, 4, 301)
    axes[0].plot(fine_t, fine_t**2 / 2, color="black", label="Exact / ZOH")
    for dt in grid:
        t, zoh, euler = simulate(float(dt))
        err = zoh[-1, 0] - euler[-1, 0]
        errors.append(err)
        rows.append({"dt_s": float(dt), "steps": len(t) - 1,
                     "zoh_final_position_m": float(zoh[-1, 0]),
                     "euler_final_position_m": float(euler[-1, 0]),
                     "position_error_m": float(err)})
        if np.isclose(dt, 0.4) or np.isclose(dt, 0.2):
            axes[0].plot(t, euler[:, 0], "o--", markersize=3, label=f"Euler dt={dt:g} s")
    ratios = np.array(errors[:-1]) / np.array(errors[1:])
    np.testing.assert_allclose(ratios, 2.0, atol=1e-11)
    axes[0].set(xlabel="Time [s]", ylabel="Position [m]", title="Same physical time interval")
    axes[0].legend()
    axes[1].loglog(grid, errors, "o-", label="Euler final position error")
    axes[1].set(xlabel="Step dt [s]", ylabel="Error at T=4 s [m]", title="First-order convergence")
    for ax in axes:
        ax.grid(True, alpha=0.25)
    fig.savefig(args.output_dir / "figure.png", dpi=160)
    plt.close(fig)
    result = {"chapter": 1, "status": "passed", "random_seed": None,
              "scope": "Constant-input discretization comparison; no MPC optimization",
              "final_time_s": 4.0, "acceleration_m_s2": 1.0,
              "rows": rows, "error_halving_ratios": ratios.tolist(),
              "checks": ["ZOH equals the continuous analytic trajectory",
                         "Euler velocity is exact for constant acceleration",
                         "Euler position error is T*dt*u/2", "Fixed-time error halves with dt"]}
    (args.output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
