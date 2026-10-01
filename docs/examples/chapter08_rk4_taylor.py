#!/usr/bin/env python3
"""Chapter 8: fixed-time integration errors and an independent Taylor check.

Time t, interval h, and the final time T are measured in seconds; normalized
states, inputs and costs are dimensionless. In dx/dt=-x+u the coefficients
implicitly have units 1/second. Input u=-1 is constant on the entire horizon,
x(0)=1, and the exact exponential solution supplies an independent reference.
Global errors at the SAME final time, not one-step errors at changing times,
are used to estimate Euler/RK4 convergence orders. The separate Taylor test is
the study guide's scalar quadratic J(u)=0.405+0.09*u+0.01*u^2 at u=0; correct
0.09 and deliberately wrong 0.08 gradients produce different residual orders.
This is neither nonlinear optimal-control transcription nor a full MPC solver,
AD demonstration, adjoint implementation, or legacy notebook reproduction.
Dependencies: numpy and matplotlib (scipy is not required by this script).
"""

import argparse
import json
import os
import tempfile
from pathlib import Path

_mpl_config = tempfile.TemporaryDirectory(prefix="mpc-ch08-mpl-")
os.environ["MPLCONFIGDIR"] = _mpl_config.name
os.environ["XDG_CACHE_HOME"] = _mpl_config.name
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def rhs(x, u):
    return -x + u


def euler_step(x, u, h):
    return x + h * rhs(x, u)


def rk4_step(x, u, h):
    k1 = rhs(x, u)
    k2 = rhs(x + 0.5*h*k1, u)
    k3 = rhs(x + 0.5*h*k2, u)
    k4 = rhs(x + h*k3, u)
    return x + (h/6.0)*(k1 + 2*k2 + 2*k3 + k4)


def exact_state(t, x0=1.0, u=-1.0):
    return u + (x0 - u) * np.exp(-t)


def integrate(step, x0, u, T, n):
    h = T / n
    states = [x0]
    for _ in range(n):
        states.append(step(states[-1], u, h))
    return np.asarray(states)


def objective(u):
    return 0.405 + 0.09*u + 0.01*u*u


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("output/chapter08"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    x0, u, T = 1.0, -1.0, 1.0
    step_counts = np.array([5, 10, 20, 40, 80])
    hs = T / step_counts
    exact_final = float(exact_state(T, x0, u))
    euler_final = np.array([integrate(euler_step, x0, u, T, n)[-1] for n in step_counts])
    rk4_final = np.array([integrate(rk4_step, x0, u, T, n)[-1] for n in step_counts])
    euler_errors, rk4_errors = np.abs(euler_final - exact_final), np.abs(rk4_final - exact_final)
    euler_orders = np.log2(euler_errors[:-1] / euler_errors[1:])
    rk4_orders = np.log2(rk4_errors[:-1] / rk4_errors[1:])
    assert np.all(np.diff(euler_errors) < 0) and np.all(np.diff(rk4_errors) < 0)
    assert 0.98 < euler_orders[-1] < 1.05
    assert 3.95 < rk4_orders[-1] < 4.1
    assert np.all(rk4_errors < euler_errors)

    # One interval from the guide connects the cost algebra to integration.
    one_h = 0.1
    one_euler = float(euler_step(x0, u, one_h))
    one_exact = float(exact_state(one_h, x0, u))
    one_rk4 = float(rk4_step(x0, u, one_h))
    # J=0.5*(0.9+0.1*u)^2+0.005*u^2; constrained minimum u=-1.
    assert np.isclose(one_euler, 0.8)
    assert np.isclose(objective(-1.0), 0.5*one_euler**2 + 0.005)
    assert abs(one_rk4 - one_exact) < abs(one_euler - one_exact)
    assert 0.09 + 0.02 * (-1.0) > 0  # Cost increases throughout [-1,1].

    # Derivative validation away from an optimum. Use moderate h to avoid
    # floating-point cancellation; include both positive and negative directions.
    taylor_h = np.logspace(-1, -4, 13)
    w, correct_gradient, wrong_gradient = 0.0, 0.09, 0.08
    taylor_results = []
    plotted = None
    for direction in [1.0, -0.7]:
        differences = objective(w + taylor_h * direction) - objective(w)
        R0 = np.abs(differences)
        R1_correct = np.abs(differences - taylor_h * correct_gradient * direction)
        R1_wrong = np.abs(differences - taylor_h * wrong_gradient * direction)
        correct_order = float(np.polyfit(np.log(taylor_h), np.log(R1_correct), 1)[0])
        wrong_order = float(np.polyfit(np.log(taylor_h), np.log(R1_wrong), 1)[0])
        assert 1.995 < correct_order < 2.005
        assert 0.97 < wrong_order < 1.03
        assert np.allclose(R1_correct, 0.01*(taylor_h*direction)**2,
                           rtol=1e-5, atol=1e-16)
        taylor_results.append({"direction": direction, "correct_order": correct_order,
                               "wrong_order": wrong_order,
                               "uncorrected_residuals": R0.tolist(),
                               "correct_residuals": R1_correct.tolist(),
                               "wrong_residuals": R1_wrong.tolist()})
        if plotted is None:
            plotted = (R0, R1_correct, R1_wrong)
    fd_h = 1e-5
    central_difference = float((objective(w + fd_h) - objective(w - fd_h)) / (2*fd_h))
    assert abs(central_difference - correct_gradient) < 1e-9
    assert abs(central_difference - wrong_gradient) > 0.009

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.1), constrained_layout=True)
    times = np.linspace(0, T, 11)
    dense_times = np.linspace(0, T, 300)
    axes[0].plot(dense_times, exact_state(dense_times), label="exact continuous solution")
    axes[0].plot(times, integrate(euler_step, x0, u, T, 10), "o--", label="Euler h=0.1 s")
    axes[0].plot(times, integrate(rk4_step, x0, u, T, 10), ".", label="RK4 h=0.1 s")
    axes[0].set(xlabel="time (s)", ylabel="normalized state", title="Constant u=-1, x(0)=1")
    axes[0].legend(fontsize=8)
    axes[1].loglog(hs, euler_errors, "o-", label=f"Euler final order {euler_orders[-1]:.3f}")
    axes[1].loglog(hs, rk4_errors, "s-", label=f"RK4 final order {rk4_orders[-1]:.3f}")
    axes[1].set(xlabel="step size h (s)", ylabel="absolute error at T=1 s",
                title="Global fixed-time error")
    axes[1].legend(fontsize=8)
    for residual, label in zip(plotted, ["R0: no derivative", "R1: correct derivative 0.09",
                                        "R1: wrong derivative 0.08"]):
        axes[2].loglog(taylor_h, residual, "o-", label=label)
    axes[2].set(xlabel="dimensionless perturbation h", ylabel="Taylor residual",
                title="A separate scalar quadratic test")
    axes[2].legend(fontsize=8)
    for ax in axes:
        ax.grid(alpha=0.2)
    fig.savefig(args.output_dir / "figure.png", dpi=170)
    plt.close(fig)

    result = {
        "chapter": 8, "example": "Euler/RK4 fixed-time error and quadratic Taylor check",
        "status": "passed", "random_seed": None,
        "checks": ["Euler and RK4 fixed-time errors decrease under mesh refinement",
                   "final Euler order between 0.98 and 1.05",
                   "final RK4 order between 3.95 and 4.1",
                   "one-interval Euler state and quadratic objective agree with direct algebra",
                   "correct Taylor residual order near 2 in two directions",
                   "deliberately wrong Taylor residual order near 1 in two directions",
                   "independent central difference agrees with correct gradient"],
        "units": {"time": "seconds", "state_input_cost": "dimensionless normalized quantities",
                  "taylor_h": "dimensionless input perturbation; not the integration time step"},
        "integration": {"model": "dx/dt=-x+u", "initial_state": x0,
                        "constant_input": u, "final_time_seconds": T,
                        "step_counts": step_counts.tolist(), "step_sizes_seconds": hs.tolist(),
                        "exact_final_state": exact_final, "euler_final_states": euler_final.tolist(),
                        "rk4_final_states": rk4_final.tolist(), "euler_errors": euler_errors.tolist(),
                        "rk4_errors": rk4_errors.tolist(), "euler_orders": euler_orders.tolist(),
                        "rk4_orders": rk4_orders.tolist()},
        "one_interval_example": {"h_seconds": one_h, "euler_state": one_euler,
                                 "exact_state": one_exact, "rk4_state": one_rk4,
                                 "euler_absolute_error": abs(one_euler - one_exact),
                                 "constrained_quadratic_optimal_input": -1.0,
                                 "discrete_optimal_cost": float(objective(-1.0))},
        "taylor": {"cost": "0.405+0.09*u+0.01*u^2", "test_point": w,
                   "correct_gradient": correct_gradient, "deliberately_wrong_gradient": wrong_gradient,
                   "central_difference_gradient": central_difference,
                   "central_difference_step": fd_h, "perturbations": taylor_h.tolist(),
                   "directions": taylor_results},
        "checks_passed": True,
        "limitations": ["Observed orders apply to this smooth constant-input scalar ODE.",
                        "Accurate optimization cannot remove integration/model errors.",
                        "Taylor checks validate this quadratic derivative, not a nonlinear adjoint or Hessian.",
                        "No optimal-control solver or complete MPC controller is implemented."],
    }
    encoded = json.dumps(result, indent=2, allow_nan=False)
    (args.output_dir / "result.json").write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
