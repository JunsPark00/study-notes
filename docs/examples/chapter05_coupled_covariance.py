#!/usr/bin/env python3
"""Chapter 5: coupled predictor-observer errors, covariance, and bounds.

Standalone supplemental example, newly computed from the study guide's small
model. All quantities and discrete time indices are dimensionless. With
zeta=(epsilon,e), zeta[k+1]=F*zeta[k]+G*[w[k],eta[k]], w and eta are
independent across time and from each other, zero-mean uniform random variables
on [-0.02,0.02] and [-0.03,0.03]. Simulation starts at zeta=0; the stationary
covariance is an infinite-time result, while the seeded simulation is finite.
RMS is NOT a worst-case bound or a Gaussian confidence guarantee. The coupled
bound below is valid for zero initial error (or the associated invariant set),
not arbitrary points in the product of the two individual error intervals.
This script is neither a full output-feedback MPC controller nor a reproduction
of a pre-existing notebook. Dependencies: numpy, scipy, matplotlib.
"""

import argparse
import json
import os
import tempfile
from pathlib import Path

_mpl_config = tempfile.TemporaryDirectory(prefix="mpc-ch05-mpl-")
os.environ["MPLCONFIGDIR"] = _mpl_config.name
os.environ["XDG_CACHE_HOME"] = _mpl_config.name
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import solve_discrete_lyapunov


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("output/chapter05"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    F = np.array([[0.4, 0.0], [0.7, 0.6]])
    G = np.array([[1.0, -0.7], [0.0, 0.7]])
    noise_bounds = np.array([0.02, 0.03])
    Q_noise = np.diag(noise_bounds**2 / 3.0)  # Uniform, not Gaussian noise.
    Q = G @ Q_noise @ G.T
    P = solve_discrete_lyapunov(F, Q)
    residual = float(np.linalg.norm(P - F @ P @ F.T - Q, ord=np.inf))
    c = np.ones(2)  # x-z=epsilon+e
    variance = float(c @ P @ c)
    rms = float(np.sqrt(variance))
    rms_without_cross = float(np.sqrt(np.trace(P)))

    # The product interval radius solves r=|F|r+|G|b. It is conservative.
    individual_radii = np.linalg.solve(np.eye(2) - np.abs(F),
                                      np.abs(G) @ noise_bounds)
    interval_sum_bound = float(individual_radii.sum())
    # Directional support of sum_{j>=0} F^j G W. Each j has its own bounded
    # independent disturbance vector, but its two state contributions correlate.
    # F is nonnegative: the resolvent expression rigorously bounds the omitted
    # absolute-value tail (up to floating point rounding).
    terms = 80
    F_power = np.eye(2)
    support_partial = 0.0
    for _ in range(terms):
        support_partial += float(np.abs(c @ F_power @ G) @ noise_bounds)
        F_power = F_power @ F
    tail_bound = float(np.abs(c) @ np.abs(F_power) @ individual_radii)
    coupled_bound = support_partial + tail_bound

    seed, samples, burn_in = 20261005, 160000, 2000
    rng = np.random.default_rng(seed)
    noise = rng.uniform(-noise_bounds, noise_bounds, size=(samples + burn_in, 2))
    trajectory = np.zeros((samples + burn_in + 1, 2))
    for k in range(noise.shape[0]):
        trajectory[k + 1] = F @ trajectory[k] + G @ noise[k]
    steady = trajectory[burn_in + 1:]
    empirical_P = np.cov(steady, rowvar=False, ddof=0)
    sum_error = steady @ c
    empirical_rms = float(np.sqrt(np.mean(sum_error**2)))
    covariance_relative_error = float(np.linalg.norm(empirical_P - P) /
                                      np.linalg.norm(P))
    all_sum_errors = trajectory @ c

    assert max(abs(np.linalg.eigvals(F))) < 1.0
    assert residual < 1e-14
    assert min(np.linalg.eigvalsh(P)) > 0.0
    assert covariance_relative_error < 0.035  # Finite seeded empirical check.
    assert abs(empirical_rms / rms - 1.0) < 0.02
    assert np.all(np.abs(trajectory) <= individual_radii + 1e-12)
    assert np.max(np.abs(all_sum_errors)) <= coupled_bound + 1e-12
    assert coupled_bound < interval_sum_bound
    assert abs(P[0, 1]) > 1e-6  # Shared eta makes independence inappropriate.

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2), constrained_layout=True)
    axes[0].plot(np.arange(400), sum_error[:400], lw=1, label="seeded x-z")
    for bound, color, label in [(coupled_bound, "tab:orange", "coupled bound"),
                                (interval_sum_bound, "tab:red", "interval sum")]:
        axes[0].axhline(bound, ls="--", color=color, label=label)
        axes[0].axhline(-bound, ls="--", color=color)
    axes[0].set(xlabel="sample index after burn-in", ylabel="x-z (dimensionless)",
                title="A finite path is not a worst-case guarantee")
    axes[0].legend(fontsize=8)
    axes[1].hist(sum_error, bins=65, density=True, alpha=0.7,
                 color="tab:blue", label="finite uniform-noise simulation")
    axes[1].axvline(rms, color="tab:green", label=f"analytic RMS = {rms:.5f}")
    axes[1].axvline(-rms, color="tab:green")
    axes[1].set(xlabel="x-z (dimensionless)", ylabel="empirical density",
                title="RMS includes 2 Cov(epsilon,e)")
    axes[1].legend(fontsize=8)
    fig.savefig(args.output_dir / "figure.png", dpi=170)
    plt.close(fig)

    result = {
        "chapter": 5,
        "status": "passed",
        "random_seed": seed,
        "checks": ["Schur stable error dynamics", "discrete Lyapunov residual below 1e-14",
                   "positive definite covariance", "seeded covariance relative error below 3.5%",
                   "seeded RMS relative error below 2%", "individual and coupled bounds contain trajectory",
                   "cross covariance is nonzero"],
        "example": "coupled predictor-observer error covariance",
        "units": "dimensionless; k is a discrete sample index",
        "F": F.tolist(), "G": G.tolist(),
        "noise": {"distribution": "independent zero-mean uniform, iid in time",
                  "absolute_bounds_w_eta": noise_bounds.tolist(), "seed": seed},
        "simulation": {"retained_samples": samples, "burn_in": burn_in,
                       "initial_epsilon_e": [0.0, 0.0],
                       "empirical_mean": steady.mean(axis=0).tolist(),
                       "empirical_covariance": empirical_P.tolist(),
                       "empirical_rms_x_minus_z": empirical_rms,
                       "covariance_relative_frobenius_error": covariance_relative_error,
                       "max_observed_abs_x_minus_z": float(np.max(np.abs(all_sum_errors)))},
        "stationary_covariance": P.tolist(),
        "lyapunov_residual_inf": residual,
        "variance_x_minus_z": variance,
        "cross_covariance_contribution": float(2 * P[0, 1]),
        "analytic_rms_x_minus_z": rms,
        "incorrect_rms_if_cross_covariance_ignored": rms_without_cross,
        "bounds": {"individual_epsilon_e": individual_radii.tolist(),
                   "interval_sum": interval_sum_bound,
                   "coupled_directional_bound": coupled_bound,
                   "finite_support_terms": terms, "tail_upper_bound": tail_bound},
        "checks_passed": True,
        "limitations": ["No controller or full MPC optimization is implemented.",
                        "RMS is not a robust bound or Gaussian confidence interval.",
                        "Coupled bound requires zero initial errors or initialization in its invariant set.",
                        "Finite simulation is an empirical check, not a proof of all noise paths."],
    }
    encoded = json.dumps(result, indent=2, allow_nan=False)
    (args.output_dir / "result.json").write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
