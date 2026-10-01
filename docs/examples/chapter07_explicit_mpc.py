#!/usr/bin/env python3
"""Chapter 7: a scalar parametric QP with three explicit regions.

All quantities are dimensionless. The problem is min_u x^2+x*u+0.5*u^2,
-1<=u<=1, with fixed parameter x and scalar decision u. Strict convexity in u
makes the optimizer unique for every real x. The explicit piecewise law is
checked against independently called derivative-free scalar optimization,
including exact endpoint candidates because a bounded search can stop just
inside an active constraint. KKT stationarity, primal/dual feasibility and
complementarity are checked independently of optimizer success.
Region-boundary distances describe local measurement sensitivity only. They
are not robust state-constraint guarantees. There is no multi-step model,
full MPC solver, general mpQP region enumeration, or notebook reproduction.
Dependencies: numpy, scipy, matplotlib.
"""

import argparse
import json
import os
import tempfile
from pathlib import Path

_mpl_config = tempfile.TemporaryDirectory(prefix="mpc-ch07-mpl-")
os.environ["MPLCONFIGDIR"] = _mpl_config.name
os.environ["XDG_CACHE_HOME"] = _mpl_config.name
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize_scalar


def explicit_input(x):
    x = np.asarray(x, dtype=float)
    return np.where(x < -1.0, 1.0, np.where(x > 1.0, -1.0, -x))


def explicit_value(x):
    x = np.asarray(x, dtype=float)
    return np.where(x < -1.0, x*x + x + 0.5,
                    np.where(x > 1.0, x*x - x + 0.5, 0.5*x*x))


def cost(u, x):
    return x*x + x*u + 0.5*u*u


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("output/chapter07"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # Include both region boundaries and points immediately to either side.
    x_grid = np.unique(np.r_[np.linspace(-2.5, 2.5, 401),
                            [-1 - 1e-7, -1, -1 + 1e-7, 1 - 1e-7, 1, 1 + 1e-7,
                             -1.4, 0.4, 1.6]])
    u_explicit = explicit_input(x_grid)
    v_explicit = explicit_value(x_grid)
    numerical_inputs = []
    for x in x_grid:
        solution = minimize_scalar(lambda u: cost(u, x), bounds=(-1.0, 1.0),
                                   method="bounded", options={"xatol": 1e-12})
        assert solution.success, solution.message
        candidates = [-1.0, float(solution.x), 1.0]
        numerical_inputs.append(min(candidates, key=lambda u: cost(u, x)))
    u_numerical = np.asarray(numerical_inputs)
    # Multipliers for u-1<=0 and -u-1<=0, respectively.
    lam_upper = np.maximum(-x_grid - 1.0, 0.0)
    lam_lower = np.maximum(x_grid - 1.0, 0.0)
    stationarity = x_grid + u_explicit + lam_upper - lam_lower
    complementarity = np.r_[lam_upper * (u_explicit - 1.0),
                             lam_lower * (-u_explicit - 1.0)]
    input_error = float(np.max(np.abs(u_explicit - u_numerical)))
    value_error = float(np.max(np.abs(v_explicit - cost(u_numerical, x_grid))))
    assert input_error < 1e-6
    assert value_error < 1e-11
    assert np.max(np.abs(stationarity)) < 1e-14
    assert np.max(np.abs(complementarity)) < 1e-14
    assert np.max(np.abs(u_explicit)) <= 1.0
    assert np.min(np.r_[lam_upper, lam_lower]) >= 0.0
    assert np.allclose(v_explicit, cost(u_explicit, x_grid), atol=1e-14)

    sensitivity_examples = []
    for x in [-1.6, 0.4, 1.6, 1.0]:
        radius = float(min(abs(x + 1.0), abs(x - 1.0)))
        slope = -1.0 if -1.0 <= x <= 1.0 else 0.0
        errors = np.linspace(-radius, radius, 21)
        changes = explicit_input(x + errors) - explicit_input(x)
        local_residual = float(np.max(np.abs(changes - slope * errors)))
        assert local_residual < 1e-14
        assert np.all(np.abs(changes) <= abs(slope) * np.abs(errors) + 1e-14)
        sensitivity_examples.append({"x": x, "closed_region_boundary_distance": radius,
                                     "regional_input_slope": slope,
                                     "max_affine_prediction_residual": local_residual})
    delta = 1e-6
    boundary_slopes = []
    for x in [-1.0, 1.0]:
        left = float((explicit_input(x) - explicit_input(x - delta)) / delta)
        right = float((explicit_input(x + delta) - explicit_input(x)) / delta)
        boundary_slopes.append({"x": x, "left_input_slope": left,
                                "right_input_slope": right})
        assert abs(left - right) > 0.99
        # The value function is differentiable for this particular QP.
        value_left = float((explicit_value(x) - explicit_value(x - delta)) / delta)
        value_right = float((explicit_value(x + delta) - explicit_value(x)) / delta)
        assert abs(value_left - value_right) < 2e-6

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.0), constrained_layout=True)
    axes[0].plot(x_grid, u_explicit, lw=2, label="explicit law")
    axes[0].plot(x_grid[::16], u_numerical[::16], "x", label="independent scalar solve")
    axes[0].set(xlabel="parameter x", ylabel="optimal u", title="Three affine regions")
    axes[0].legend(fontsize=8)
    axes[1].plot(x_grid, v_explicit)
    axes[1].set(xlabel="parameter x", ylabel="optimal cost V", title="Piecewise quadratic value")
    region_distance = np.minimum(np.abs(x_grid + 1), np.abs(x_grid - 1))
    axes[2].plot(x_grid, region_distance, color="tab:green")
    axes[2].set(xlabel="parameter x", ylabel="distance r", title="Distance to a region boundary")
    for ax in axes:
        for boundary in [-1, 1]:
            ax.axvline(boundary, color="gray", ls="--", lw=0.8)
        ax.grid(alpha=0.2)
    fig.savefig(args.output_dir / "figure.png", dpi=170)
    plt.close(fig)

    result = {
        "chapter": 7, "example": "scalar explicit parametric QP",
        "status": "passed", "random_seed": None,
        "checks": ["independent scalar optimizer agreement on 407 sample parameters",
                   "primal and dual feasibility", "KKT stationarity and complementarity",
                   "piecewise value equals objective at explicit input",
                   "closed-region perturbations follow regional affine law",
                   "one-sided input slopes change at both boundaries",
                   "value derivative remains continuous at both boundaries in this example"],
        "units": "dimensionless", "cost": "J(u,x)=x^2+x*u+0.5*u^2",
        "input_bounds": [-1.0, 1.0], "feasible_parameter_set": "all real x",
        "regions": [{"condition": "x < -1", "u": "1", "value": "x^2+x+0.5"},
                    {"condition": "-1 <= x <= 1", "u": "-x", "value": "0.5*x^2"},
                    {"condition": "x > 1", "u": "-1", "value": "x^2-x+0.5"}],
        "sample_count": int(len(x_grid)),
        "max_input_difference_vs_scalar_optimizer": input_error,
        "max_value_difference_vs_scalar_optimizer": value_error,
        "kkt_stationarity_residual_inf": float(np.max(np.abs(stationarity))),
        "kkt_complementarity_residual_inf": float(np.max(np.abs(complementarity))),
        "sensitivity_examples": sensitivity_examples, "boundary_one_sided_slopes": boundary_slopes,
        "sample_solutions": [{"x": x, "u": float(explicit_input(x)),
                              "value": float(explicit_value(x))} for x in [-1.4, 0.4, 1.6]],
        "checks_passed": True,
        "limitations": ["No multi-step dynamics or general explicit MPC region solver is implemented.",
                        "Input clipping is exact here but is not generally a constrained MPC solution.",
                        "Region distance concerns the selected law, not robust closed-loop safety.",
                        "The grid is an implementation check, not a substitute for the analytic KKT argument."],
    }
    encoded = json.dumps(result, indent=2, allow_nan=False)
    (args.output_dir / "result.json").write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
