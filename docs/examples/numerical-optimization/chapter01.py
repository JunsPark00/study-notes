#!/usr/bin/env python3
"""Original, self-contained teaching experiment. Not a production optimizer.
Run: python chapter01.py --output-dir ./output
Only NumPy, SciPy and Matplotlib are required. No network or private data.
"""
from pathlib import Path
import argparse, json, os, platform, tempfile
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "optimization-learning-mpl"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "optimization-learning-cache"))
Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)
import numpy as np
import scipy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output-dir", type=Path, default=Path("."))
args = parser.parse_args()
args.output_dir.mkdir(parents=True, exist_ok=True)
font_paths = [Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
              Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf")]
korean = False
for font_path in font_paths:
    if font_path.exists():
        font_manager.fontManager.addfont(str(font_path))
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(font_path)).get_name()
        korean = True
        break
plt.rcParams.update({"axes.unicode_minus": False, "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": "#f8fafc", "axes.facecolor": "#f8fafc"})
def label(ko, en):
    return ko if korean else en

def finish(chapter, fig, results):
    fig.savefig(args.output_dir / f"chapter{chapter:02d}.png", dpi=160, bbox_inches=None)
    plt.close(fig)
    results.update({"chapter": chapter, "seed": 20261001,
                    "python": platform.python_version(), "numpy": np.__version__,
                    "scipy": scipy.__version__, "matplotlib": matplotlib.__version__,
                    "korean_labels": korean, "checks_passed": True})
    output = json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False)
    (args.output_dir / f"chapter{chapter:02d}-results.json").write_text(output + "\n", encoding="utf-8")
    print(output)

from scipy.optimize import linprog
# Evening demand is 6 kWh; 1 kWh is supplied by previously stored solar.
# x = off-peak charge, y = peak-time grid purchase, both in kWh.
c = np.array([0.18, 0.40])
A = np.array([[-0.8, -1.0]])
b = np.array([-5.0])
result = linprog(c, A_ub=A, b_ub=b, bounds=[(0, 4), (0, 5)], method="highs")
assert result.success, result.message
reference = np.array([4.0, 1.8])
violation = max(0.0, float(np.max(A @ result.x - b)),
                float(np.max(-result.x)), float(result.x[0]-4), float(result.x[1]-5))
assert np.linalg.norm(result.x-reference, np.inf) < 1e-9
assert violation < 1e-9 and abs(result.fun-1.44) < 1e-9
# Independent 1-D elimination and a finite grid check, not another LP call.
xs = np.linspace(0, 4, 1001)
ys = 5-0.8*xs
costs = .18*xs + .4*ys
assert np.argmin(costs) == len(xs)-1
fig, ax = plt.subplots(1, 2, figsize=(10, 4.5), layout="constrained")
grid_x, grid_y = np.meshgrid(np.linspace(0, 4, 200), np.linspace(0, 5, 200))
cont = ax[0].contour(grid_x, grid_y, .18*grid_x+.4*grid_y, levels=np.arange(.4, 3, .4),
                     colors="#94a3b8", linewidths=.8)
ax[0].clabel(cont, fontsize=8)
ax[0].fill_between(xs, ys, 5, color="#99e4d5", alpha=.7, label=label("실행 가능 영역", "Feasible set"))
ax[0].plot(xs, ys, color="#0f766e", lw=2)
ax[0].scatter(*result.x, s=70, color="#e85d3f", zorder=5, label=label("최적점 (4, 1.8)", "Optimum (4, 1.8)"))
ax[0].set(xlim=(-.1, 4.2), ylim=(-.1, 5.2), xlabel=label("저가 시간 충전 x (kWh)", "Off-peak charge x (kWh)"),
          ylabel=label("고가 시간 구매 y (kWh)", "Peak purchase y (kWh)"), title=label("제약이 허용하는 선택", "Choices allowed by constraints"))
ax[0].legend(loc="lower left", fontsize=8)
ax[1].plot(xs, costs, color="#1d4ed8", lw=2.5)
ax[1].scatter([4], [1.44], color="#e85d3f", s=65)
ax[1].annotate("2 - 0.14 x", xy=(1.8, 1.748), xytext=(.4, 1.56),
                arrowprops={"arrowstyle":"->", "color":"#64748b"}, fontsize=11)
ax[1].set(xlabel=label("저가 시간 충전 x (kWh)", "Off-peak charge x (kWh)"),
          ylabel=label("비용 (가상 화폐 단위)", "Cost (illustrative units)"),
          title=label("수요 경계 위에서 독립 검산", "Independent check on demand boundary"))
ax[1].grid(alpha=.2)
finish(1, fig, {"x": result.x.tolist(), "objective": float(result.fun),
                "max_constraint_violation": violation,
                "analytic_solution_error_inf": float(np.linalg.norm(result.x-reference, np.inf)),
                "boundary_cost_slope": -0.14})
