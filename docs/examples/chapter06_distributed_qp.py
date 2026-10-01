#!/usr/bin/env python3
"""Chapter 6: raw block updates, candidate averaging, and a box certificate.

All variables, costs, and iteration indices are dimensionless. Three agents
optimize a common strictly convex quadratic, each holding the other two scalar
blocks fixed at the SAME previous iterate. Equal averaging of complete feasible
candidate vectors is distinct from concatenating their updated components.
The unconstrained zero-linear-term divergence demonstration is separate from
a new bounded QP with q!=0 and |u_i|<=0.4. The latter uses a globally valid
convex box linearization gap as its stopping certificate and compares against
an independent centralized scipy optimizer. This is a static optimization
experiment, not a full distributed MPC, communications benchmark, stability
proof, or reproduction of an existing notebook.
Dependencies: numpy, scipy, matplotlib.
"""

import argparse
import json
import os
import tempfile
from pathlib import Path

_mpl_config = tempfile.TemporaryDirectory(prefix="mpc-ch06-mpl-")
os.environ["MPLCONFIGDIR"] = _mpl_config.name
os.environ["XDG_CACHE_HOME"] = _mpl_config.name
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("output/chapter06"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    H = np.full((3, 3), 0.8)
    np.fill_diagonal(H, 1.0)
    n = len(H)

    def candidates(u, q, limit=None):
        proposals = np.tile(u, (n, 1))
        for i in range(n):
            best_i = -(q[i] + H[i] @ u - H[i, i] * u[i]) / H[i, i]
            if limit is not None:
                best_i = np.clip(best_i, -limit, limit)
            proposals[i, i] = best_i
        return proposals

    raw = [np.ones(n)]
    averaged_fast = [np.ones(n)]
    averaged_slow = [np.array([1.0, -1.0, 0.0])]
    for _ in range(30):
        raw.append(np.diag(candidates(raw[-1], np.zeros(n))).copy())
        averaged_fast.append(candidates(averaged_fast[-1], np.zeros(n)).mean(axis=0))
        averaged_slow.append(candidates(averaged_slow[-1], np.zeros(n)).mean(axis=0))
    raw, averaged_fast, averaged_slow = map(np.asarray, (raw, averaged_fast, averaged_slow))
    T_raw, T_avg = np.eye(n) - H, np.eye(n) - H / n
    rho_raw = float(max(abs(np.linalg.eigvals(T_raw))))
    rho_avg = float(max(abs(np.linalg.eigvals(T_avg))))
    assert rho_raw > 1.0 and rho_avg < 1.0
    assert np.allclose(raw[1], -1.6 * np.ones(n))
    assert np.allclose(averaged_fast[1], np.ones(n) * (1 - 2.6 / 3))

    # A different QP: its optimum is nonzero and includes active box constraints.
    q, limit, tolerance = np.array([-0.9, 0.2, -0.1]), 0.4, 1e-10

    def objective(u):
        return float(0.5 * u @ H @ u + q @ u)

    def gradient(u):
        return H @ u + q

    def box_gap(u):
        # Convexity: f(v)>=f(u)+g'(v-u), all v in box.
        # min_v g'v = -limit*||g||_1, hence f(u)-f* <= this gap.
        g = gradient(u)
        return float(g @ u + limit * np.linalg.norm(g, 1))

    iterates = [np.zeros(n)]
    values, gaps = [objective(iterates[0])], [box_gap(iterates[0])]
    for _ in range(20000):
        old = iterates[-1]
        proposals = candidates(old, q, limit)
        assert np.max(np.abs(proposals)) <= limit + 1e-14
        candidate_values = np.array([objective(v) for v in proposals])
        assert np.all(candidate_values <= values[-1] + 1e-13)
        new = proposals.mean(axis=0)
        assert objective(new) <= candidate_values.mean() + 1e-13
        iterates.append(new)
        values.append(objective(new))
        gaps.append(box_gap(new))
        if gaps[-1] <= tolerance:
            break
    else:
        raise AssertionError("Bounded cooperative QP did not reach its certificate tolerance")
    iterates, values, gaps = np.asarray(iterates), np.asarray(values), np.asarray(gaps)
    central = minimize(objective, np.zeros(n), jac=gradient, method="SLSQP",
                       bounds=[(-limit, limit)] * n,
                       options={"ftol": 1e-14, "maxiter": 1000})
    assert central.success, central.message
    optimum = central.x
    central_projected_residual = float(np.max(np.abs(
        optimum - np.clip(optimum - gradient(optimum), -limit, limit))))
    true_cost_gap = float(values[-1] - objective(optimum))
    # The analytic certificate does not depend on the central solve. That solve
    # only tests it numerically, with explicit floating-point allowances.
    assert np.all(np.diff(values) <= 1e-13)
    assert np.all(gaps >= -1e-13)
    assert central_projected_residual < 1e-9
    assert -1e-12 <= true_cost_gap <= gaps[-1] + 1e-12
    assert np.max(np.abs(iterates[-1] - optimum)) < 1e-7
    assert np.all(values - objective(optimum) <= gaps + 1e-12)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2), constrained_layout=True)
    for curve, label in [(raw, "raw simultaneous"),
                         (averaged_fast, "average: fast initial mode"),
                         (averaged_slow, "average: slow initial mode")]:
        axes[0].semilogy(np.linalg.norm(curve, axis=1), label=label)
    axes[0].set(title="Unconstrained iteration, q=0", xlabel="iteration p",
                ylabel="norm of u (dimensionless)")
    axes[0].legend(fontsize=8)
    for i in range(n):
        axes[1].plot(iterates[:, i], label=f"u{i+1}")
    axes[1].axhline(limit, color="gray", ls="--")
    axes[1].axhline(-limit, color="gray", ls="--")
    axes[1].set(title="Separate box QP, q != 0", xlabel="iteration p", ylabel="input")
    axes[1].legend(fontsize=8)
    axes[2].semilogy(np.maximum(gaps, 1e-16), label="rigorous box gap upper bound")
    axes[2].semilogy(np.maximum(values - objective(optimum), 1e-16),
                     label="cost gap vs centralized solve")
    axes[2].axhline(tolerance, color="gray", ls="--", label="stopping tolerance")
    axes[2].set(title="Objective gap certificate", xlabel="iteration p",
                ylabel="dimensionless cost gap")
    axes[2].legend(fontsize=8)
    fig.savefig(args.output_dir / "figure.png", dpi=170)
    plt.close(fig)

    result = {
        "chapter": 6, "example": "cooperative candidate averaging and bounded QP",
        "status": "passed", "random_seed": None,
        "checks": ["raw iteration spectral radius above 1 and averaged radius below 1",
                   "candidate feasibility and cost descent at every iteration",
                   "box dual gap below 1e-10", "central SLSQP success and projected stationarity",
                   "central cost difference within certificate at every iterate",
                   "final centralized input agreement below 1e-7"],
        "units": "all quantities dimensionless; p is optimization iteration, not plant time",
        "H": H.tolist(), "hessian_eigenvalues": np.linalg.eigvalsh(H).tolist(),
        "unconstrained_demo": {
            "linear_term": [0.0] * n, "initial_input": [1.0] * n,
            "raw_spectral_radius": rho_raw, "averaged_spectral_radius": rho_avg,
            "raw_first_input": raw[1].tolist(),
            "averaged_first_input": averaged_fast[1].tolist(),
            "initial_cost": float(0.5 * raw[0] @ H @ raw[0]),
            "raw_first_cost": float(0.5 * raw[1] @ H @ raw[1]),
            "averaged_first_cost": float(0.5 * averaged_fast[1] @ H @ averaged_fast[1])},
        "bounded_qp": {
            "linear_term": q.tolist(), "absolute_input_limit": limit,
            "iterations": int(len(iterates) - 1), "stopping_tolerance": tolerance,
            "cooperative_solution": iterates[-1].tolist(),
            "central_solution": optimum.tolist(), "central_success": bool(central.success),
            "central_method": "scipy.optimize.minimize, SLSQP",
            "cooperative_cost": float(values[-1]), "central_cost": objective(optimum),
            "box_gap_certificate": float(gaps[-1]), "actual_cost_gap": true_cost_gap,
            "central_projected_gradient_residual_inf": central_projected_residual,
            "max_input_difference": float(np.max(np.abs(iterates[-1] - optimum))),
            "raw_gradient_at_central_solution": gradient(optimum).tolist()},
        "checks_passed": True,
        "limitations": ["This is fixed-state optimization, with no plant or MPC horizon.",
                        "The box certificate is an objective-gap bound, not a stability claim.",
                        "Independent box constraints and shared synchronous iterates are assumed.",
                        "Serial Python candidate calculations do not measure distributed speedup."],
    }
    encoded = json.dumps(result, indent=2, allow_nan=False)
    (args.output_dir / "result.json").write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
