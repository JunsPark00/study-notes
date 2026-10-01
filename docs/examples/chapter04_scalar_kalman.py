#!/usr/bin/env python3
"""4장: 스칼라 칼만 필터의 정보 시점, 평균과 공분산.

무차원 랜덤 워크 x[k+1]=x[k]+w[k], y[k]=x[k]+v[k].
초기 사전 N(0,1), Q=0.04, R=0.25, 독립 영평균 가우스 잡음.
현재 측정 y[k]로 필터링한 뒤 다음 시각을 예측합니다. 칼만 필터만
구현하며 제약 MHE, 평활화, MPC 결합은 구현하지 않습니다.
실행: python chapter04_scalar_kalman.py --output-dir output/chapter04
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
from scipy.stats import norm

SEED = 202604


def update(prior_mean, prior_variance, measurement, measurement_variance):
    innovation_variance = prior_variance + measurement_variance
    gain = prior_variance / innovation_variance
    mean = prior_mean + gain * (measurement - prior_mean)
    # Joseph form remains nonnegative despite floating-point roundoff.
    variance = (1 - gain)**2 * prior_variance + gain**2 * measurement_variance
    assert innovation_variance > 0 and variance >= 0
    return mean, variance, gain, innovation_variance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("output/chapter04"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    q, r = 0.04, 0.25
    mean, variance, gain, innovation_variance = update(0.0, 1.0, 1.0, r)
    np.testing.assert_allclose([mean, variance, gain, innovation_variance, variance + q],
                               [0.8, 0.2, 0.8, 1.25, 0.24], atol=1e-14)
    # Independent Gaussian conditioning formula is a cross-check of the update.
    precision_variance = 1 / (1 / 1.0 + 1 / r)
    precision_mean = precision_variance * (0.0 / 1.0 + 1.0 / r)
    assert np.isclose(variance, precision_variance) and np.isclose(mean, precision_mean)
    repetitions, steps = 20000, 50
    x = rng.normal(0.0, 1.0, repetitions)
    prior = np.zeros(repetitions)
    prior_var = 1.0
    time, true_trace, measurement_trace, mean_trace, variance_trace = [], [], [], [], []
    standardized_errors = None
    for k in range(steps):
        y = x + rng.normal(0, np.sqrt(r), repetitions)
        filtered, filtered_var, _, _ = update(prior, prior_var, y, r)
        assert filtered_var <= prior_var + 1e-14
        time.append(k)
        true_trace.append(float(x[0]))
        measurement_trace.append(float(y[0]))
        mean_trace.append(float(filtered[0]))
        variance_trace.append(filtered_var)
        if k == steps - 1:
            standardized_errors = (x - filtered) / np.sqrt(filtered_var)
        # Future process noise is used only to evolve the truth, never in filtering.
        x = x + rng.normal(0, np.sqrt(q), repetitions)
        prior = filtered
        prior_var = filtered_var + q
    normalized_mse = float(np.mean(standardized_errors**2))
    nominal_coverage = 0.95
    observed_coverage = float(np.mean(np.abs(standardized_errors) <= norm.ppf(0.975)))
    mse_se = np.sqrt(2 / repetitions)
    coverage_se = np.sqrt(nominal_coverage * (1 - nominal_coverage) / repetitions)
    assert abs(normalized_mse - 1) < 5 * mse_se
    assert abs(observed_coverage - nominal_coverage) < 5 * coverage_se
    steady_filtered_var = (-q + np.sqrt(q**2 + 4 * q * r)) / 2
    assert abs(variance_trace[-1] - steady_filtered_var) < 1e-12
    means = np.asarray(mean_trace)
    half_width = norm.ppf(0.975) * np.sqrt(variance_trace)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    axes[0].fill_between(time, means - half_width, means + half_width, alpha=0.2, label="Conditional 95% interval")
    axes[0].plot(time, true_trace, color="black", label="True x")
    axes[0].plot(time, means, label="Filtered mean")
    axes[0].scatter(time, measurement_trace, s=10, alpha=0.4, label="Measurement y")
    axes[0].set(xlabel="Sample k", ylabel="Dimensionless state", title="One realization of 20,000")
    axes[0].legend(fontsize=8)
    axes[1].plot(time, variance_trace, label="Filtered variance")
    axes[1].plot(time, np.array(variance_trace) + q, label="Next-prior variance")
    axes[1].axhline(steady_filtered_var, color="black", linestyle="--", label="Steady filtered variance")
    axes[1].set(xlabel="Sample k", ylabel="Variance [state unit squared]", title="Measurement contracts; prediction expands")
    axes[1].legend(fontsize=8)
    for ax in axes:
        ax.grid(True, alpha=0.25)
    fig.savefig(args.output_dir / "figure.png", dpi=160)
    plt.close(fig)
    result = {"chapter": 4, "status": "passed", "random_seed": SEED,
              "units": "dimensionless state and measurement; variances in squared state units",
              "scope": "Exact linear-Gaussian filtering; no MHE or MPC implementation",
              "single_update": {"innovation_variance": innovation_variance, "gain": gain,
                                "posterior_mean": mean, "posterior_variance": variance,
                                "next_prior_variance": variance + q},
              "monte_carlo": {"independent_trajectories": repetitions, "steps": steps,
                              "final_normalized_mean_squared_error": normalized_mse,
                              "final_95pct_coverage": observed_coverage,
                              "coverage_standard_error": float(coverage_se)},
              "steady_filtered_variance": steady_filtered_var,
              "checks": ["Hand calculation 0.8 / 0.2 / 0.24", "Independent precision-form check",
                         "Nonnegative covariance; measurement contraction", "Stationary Riccati variance",
                         "Finite Monte Carlo calibration within five standard errors; no pathwise guarantee"]}
    (args.output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
