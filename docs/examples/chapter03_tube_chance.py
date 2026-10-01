#!/usr/bin/env python3
"""3장: 유계 튜브 여유와 가우스 구간 위험 배분의 서로 다른 의미.

무차원 모델 x+=1.1*x+u+w, u=v-0.6*(x-z). 유계 부분에서는
|w|<=0.1, |e0|<=0.2, |x|<=3, |u|<=1을 가정합니다. 명목 입력은
v=-0.35*z인 허용 예시이며 MPC 최적화/종단 설계는 구현하지 않습니다.
가우스 부분은 별도의 영평균 오차 실험입니다. 시점별 분산이 정확히
알려졌다고 가정하고, 합집합 상계와 독립 표본의 검증 빈도를 구분합니다.
실행: python chapter03_tube_chance.py --output-dir output/chapter03
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

SEED = 202603


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("output/chapter03"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    a, k, wmax, xmax, umax = 1.1, -0.6, 0.1, 3.0, 1.0
    contraction = a + k
    radius = wmax / (1 - abs(contraction))
    zmax, vmax = xmax - radius, umax - abs(k) * radius
    # An affine scalar map reaches its extrema at interval corners.
    corners = [contraction * e + w for e in [-radius, radius] for w in [-wmax, wmax]]
    assert max(abs(np.asarray(corners))) <= radius + 1e-14
    np.testing.assert_allclose([radius, zmax, vmax], [0.2, 2.8, 0.88])
    traces, steps = 80, 50
    z = np.zeros(steps + 1)
    e = np.zeros((traces, steps + 1))
    actual_inputs = np.zeros((traces, steps))
    z[0] = 2.5
    e[:, 0] = np.linspace(-radius, radius, traces)
    for j in range(steps):
        v = -0.35 * z[j]
        assert abs(v) <= vmax + 1e-14
        actual_inputs[:, j] = v + k * e[:, j]
        noise = rng.uniform(-wmax, wmax, traces)
        e[:, j + 1] = contraction * e[:, j] + noise
        z[j + 1] = a * z[j] + v
    x = z[None, :] + e
    assert np.max(np.abs(e)) <= radius + 1e-12
    assert np.max(np.abs(z)) <= zmax + 1e-12
    assert np.max(np.abs(x)) <= xmax + 1e-12
    assert np.max(np.abs(actual_inputs)) <= umax + 1e-12
    # This is a separate Gaussian model, not the preceding bounded-noise system.
    horizon, total_risk, sigma, sample_count = 10, 0.05, 0.15, 100000
    step_risk = total_risk / horizon
    quantile_individual = float(norm.ppf(1 - total_risk / 2))
    quantile_allocated = float(norm.ppf(1 - step_risk / 2))
    margin = quantile_allocated * sigma
    assert abs(2 * norm.sf(quantile_allocated) - step_risk) < 1e-12
    independent_exact_risk = 1 - (1 - step_risk)**horizon
    assert independent_exact_risk <= total_risk
    gaussian_errors = rng.normal(0, sigma, size=(sample_count, horizon))
    observed_risk = float(np.mean(np.any(np.abs(gaussian_errors) > margin, axis=1)))
    standard_error = np.sqrt(independent_exact_risk * (1 - independent_exact_risk) / sample_count)
    assert abs(observed_risk - independent_exact_risk) < 5 * standard_error
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    time = np.arange(steps + 1)
    axes[0].fill_between(time, z - radius, z + radius, color="#0f766e", alpha=0.2, label="Invariant tube")
    axes[0].plot(time, x[:12].T, color="#94a3b8", alpha=0.4, linewidth=0.8)
    axes[0].plot(time, z, color="#2563eb", label="Nominal z")
    axes[0].set(xlabel="Sample k", ylabel="Dimensionless state", title="Bounded disturbance experiment")
    axes[0].legend()
    standardized = np.linspace(-4, 4, 500)
    axes[1].plot(standardized, norm.pdf(standardized), color="black")
    for q, label, color in [(quantile_individual, "One-step risk 5%", "#c65d13"),
                            (quantile_allocated, "Per-step risk 0.5%", "#7c3aed")]:
        axes[1].axvline(q, color=color, linestyle="--", label=f"{label}: {q:.3f} sigma")
        axes[1].axvline(-q, color=color, linestyle="--")
    axes[1].set(xlabel="Standardized Gaussian error", ylabel="Density", title="10-step risk budget <= 5%")
    axes[1].legend(fontsize=8)
    for ax in axes:
        ax.grid(True, alpha=0.25)
    fig.savefig(args.output_dir / "figure.png", dpi=160)
    plt.close(fig)
    result = {"chapter": 3, "status": "passed", "random_seed": SEED,
              "units": "dimensionless state, input, disturbances; sample index time",
              "scope": "Invariant scalar tube and a separate Gaussian risk illustration; no complete MPC design",
              "bounded": {"error_radius": radius, "nominal_state_limit": zmax, "nominal_input_limit": vmax,
                          "initial_error_assumption": "abs(e0)<=0.2", "checked_corner_images": corners,
                          "max_simulated_abs_state": float(np.max(np.abs(x))),
                          "max_simulated_abs_input": float(np.max(np.abs(actual_inputs)))},
              "gaussian": {"horizon": horizon, "total_union_bound": total_risk, "per_step_risk": step_risk,
                           "individual_5pct_quantile": quantile_individual,
                           "allocated_0_5pct_quantile": quantile_allocated,
                           "sigma": sigma, "two_sided_margin": margin,
                           "independent_exact_any_violation_probability": independent_exact_risk,
                           "monte_carlo_any_violation_frequency": observed_risk,
                           "monte_carlo_samples": sample_count, "monte_carlo_standard_error": float(standard_error)},
              "checks": ["Interval-corner invariance", "Analytic tightening 0.2 / 2.8 / 0.88",
                         "Finite bounded-noise trajectory constraints", "Gaussian two-sided tail equals budget",
                         "Union bound needs no temporal independence",
                         "Independent Gaussian simulation is within five standard errors; not a safety proof"]}
    (args.output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
