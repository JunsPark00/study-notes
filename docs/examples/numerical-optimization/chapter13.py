"""Original, self-contained numerical experiment. No network or external data.
Run: python chapter13.py --output-dir ./results
Requires NumPy, SciPy and Matplotlib. An installed Korean font is optional.
If unavailable, all plot labels fall back to English; --english forces this mode.
"""
import argparse
import json
import platform
from pathlib import Path
import numpy as np
import scipy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", type=Path, default=Path("."))
parser.add_argument("--english", action="store_true", help="Use English plot labels")
args = parser.parse_args()
args.output_dir.mkdir(parents=True, exist_ok=True)
font_paths = [Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")]
font_paths += [Path(f.fname) for f in font_manager.fontManager.ttflist
               if any(s in f.name for s in ("Noto Sans CJK", "Nanum", "Malgun", "AppleGothic"))]
font_path = next((p for p in font_paths if p.exists()), None)
if args.english:
    font_path = None
if font_path is not None:
    font_manager.fontManager.addfont(str(font_path))
font_family = font_manager.FontProperties(fname=str(font_path)).get_name() if font_path else "DejaVu Sans"
plt.rcParams.update({"font.family": font_family,
                     "axes.unicode_minus": False, "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": "#f7f9fc", "axes.facecolor": "#f7f9fc",
                     "axes.prop_cycle": matplotlib.cycler(color=["#156f87", "#e07945", "#7661a9", "#278169"])})

ENGLISH_LABELS = {'실행 가능 영역': 'Feasible region', '직접 구현한 피벗': 'Implemented pivots', '최적점': 'Optimum', '생산량 x': 'Production x', '생산량 y': 'Production y', '기저를 바꾸며 경계를 이동': 'Moving between bases', '독립 계산한 최적 비용': 'Independent optimum', '피벗 단계': 'Pivot step', '최소화 목적값': 'Objective value', '감소 비용이 이동을 결정': 'Reduced costs guide the move'}
def tr(label):
    return label if font_path else ENGLISH_LABELS[label]

def finish(chapter, fig, metrics):
    fig.savefig(args.output_dir / f"chapter{chapter:02d}.png", dpi=160)
    plt.close(fig)
    report = {"chapter": chapter, "plot_language": "ko" if font_path else "en",
              "versions": {"python": platform.python_version(), "numpy": np.__version__,
                           "scipy": scipy.__version__, "matplotlib": matplotlib.__version__},
              "metrics": metrics}
    serialized = json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2)
    (args.output_dir / f"chapter{chapter:02d}-results.json").write_text(serialized + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, allow_nan=False))

from itertools import combinations
from scipy.optimize import linprog

# Standard form: min c.T x, A x = b, x >= 0.
A = np.array([[2.,1.,1.,0.,0.], [1.,2.,0.,1.,0.], [1.,0.,0.,0.,1.]])
b = np.array([8.,8.,3.])
c = np.array([-4.,-3.,0.,0.,0.])
basis = [2,3,4]
path = []
for iteration in range(20):
    B = A[:, basis]
    xb = np.linalg.solve(B, b)
    y = np.linalg.solve(B.T, c[basis])
    reduced = c - A.T @ y
    x = np.zeros(5); x[basis] = xb
    path.append(x.copy())
    candidates = [j for j in range(5) if j not in basis and reduced[j] < -1e-10]
    if not candidates:
        break
    entering = min(candidates)  # Bland entering rule.
    direction = np.linalg.solve(B, A[:, entering])
    eligible = np.where(direction > 1e-12)[0]
    if eligible.size == 0:
        raise RuntimeError("Unbounded along the selected edge")
    ratios = xb[eligible] / direction[eligible]
    theta = ratios.min()
    tied = eligible[np.abs(ratios-theta) < 1e-10]
    leaving = min(tied, key=lambda i: basis[i])
    basis[leaving] = entering
else:
    raise RuntimeError("Iteration limit")

# Independent small-problem certificate by enumerating every nonsingular basis.
vertices = []
for inds in combinations(range(5),3):
    if abs(np.linalg.det(A[:,inds])) < 1e-10:
        continue
    v = np.zeros(5); v[list(inds)] = np.linalg.solve(A[:,inds], b)
    if np.min(v) >= -1e-10:
        vertices.append(v)
reference = linprog(c, A_eq=A, b_eq=b, method="highs-ds")
assert reference.success
expected = np.array([8/3,8/3,0,0,1/3])
metrics = {"objective": float(c@x), "solution_error": float(np.linalg.norm(x-expected,np.inf)),
           "primal_residual": float(np.linalg.norm(A@x-b,np.inf)),
           "dual_violation": float(max(0.,-reduced.min())),
           "duality_gap": float(abs(c@x-b@y)), "pivots": len(path)-1,
           "basis_enumeration_gap": float(abs(c@x-min(c@v for v in vertices))),
           "highs_objective_gap": float(abs(reference.fun-c@x))}
assert metrics["solution_error"] < 1e-9
assert max(metrics[k] for k in ("primal_residual","dual_violation","duality_gap","basis_enumeration_gap","highs_objective_gap")) < 1e-9
fig, ax = plt.subplots(1,2, figsize=(10,4.6), layout="constrained")
poly = np.array([[0,0],[3,0],[3,2],[8/3,8/3],[0,4],[0,0]])
ax[0].fill(poly[:,0],poly[:,1],color="#dceef0",label=tr("실행 가능 영역"))
q=np.array(path)
ax[0].plot(q[:,0],q[:,1],"o-",lw=2,label=tr("직접 구현한 피벗"))
for k,pt in enumerate(q): ax[0].annotate(str(k),(pt[0]+.05,pt[1]+.08))
ax[0].scatter([8/3],[8/3],marker="*",s=150,color="#e07945",label=tr("최적점"))
ax[0].set(xlabel=tr("생산량 x"),ylabel=tr("생산량 y"),title=tr("기저를 바꾸며 경계를 이동"),xlim=(-.15,3.7),ylim=(-.2,4.6))
ax[0].legend(fontsize=9,loc="upper right")
ax[1].plot(np.arange(len(path)),q@c,"o-",lw=2)
ax[1].axhline(-56/3,color="#e07945",ls="--",label=tr("독립 계산한 최적 비용"))
ax[1].set(xlabel=tr("피벗 단계"),ylabel=tr("최소화 목적값"),title=tr("감소 비용이 이동을 결정"))
ax[1].set_xticks(np.arange(len(path))); ax[1].legend(fontsize=9)
finish(13,fig,metrics)
