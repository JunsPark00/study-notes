#!/usr/bin/env python3
"""Original, self-contained teaching experiment. Not a production optimizer.
Run: python chapter02.py --output-dir ./output
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

Q = np.diag([1.0, 16.0])
star = np.array([1.0, -0.5])
x0 = np.array([-2.0, 1.5])
def f(x):
    d = x-star
    return 0.5*float(d @ Q @ d)
path=[x0.copy()]
for _ in range(100):
    x=path[-1]
    g=Q@(x-star)
    if np.linalg.norm(g) < 1e-10:
        break
    alpha=float(g@g)/float(g@Q@g)
    path.append(x-alpha*g)
path=np.array(path)
g0=Q@(x0-star)
newton=x0-np.linalg.solve(Q,g0)
D=np.diag([1.0, 0.25])
transformed=D.T@Q@D
assert np.linalg.norm(newton-star) < 1e-12
assert np.linalg.norm(transformed-np.eye(2)) < 1e-12
assert np.max(np.diff([f(x) for x in path])) <= 1e-12
assert np.linalg.norm(Q@(path[-1]-star)) < 1e-8
fig, ax=plt.subplots(1,2,figsize=(10,4.5),layout="constrained")
u,v=np.meshgrid(np.linspace(-2.4,2.4,300),np.linspace(-1.6,1.8,250))
z=.5*((u-1)**2+16*(v+.5)**2)
ax[0].contour(u,v,z,levels=[.1,.5,1,2,4,8,16,32],colors="#a5b4fc",linewidths=.8)
ax[0].plot(path[:,0],path[:,1],"o-",ms=3,color="#0f766e",label=label("최급강하 · 정확 선 탐색","Steepest descent"))
ax[0].plot([x0[0],newton[0]],[x0[1],newton[1]],"--",color="#ea580c",label=label("뉴턴 한 단계", "One Newton step"))
ax[0].scatter(*star,s=80,marker="*",color="#0f172a",zorder=6)
ax[0].set(xlabel="u",ylabel="v",title=label("방향 선택이 바꾸는 경로","Direction changes the path"),aspect="equal")
ax[0].legend(fontsize=8,loc="upper right")
errors=np.linalg.norm(path-star,axis=1)
ax[1].semilogy(range(len(errors)),np.maximum(errors,1e-16),"o-",ms=3,color="#0f766e")
ax[1].set(xlabel=label("반복 번호", "Iteration"),ylabel=label("해까지의 거리", "Distance to solution"),
          title=label("작은 기울기와 알려진 해를 대조", "Check gradient and known solution"))
ax[1].grid(alpha=.2,which="both")
finish(2,fig,{"minimizer":star.tolist(),"initial_gradient":g0.tolist(),
              "newton_solution_error":float(np.linalg.norm(newton-star)),
              "steepest_iterations":len(path)-1,"steepest_gradient_norm":float(np.linalg.norm(Q@(path[-1]-star))),
              "original_condition_number":float(np.linalg.cond(Q)),"scaled_condition_number":float(np.linalg.cond(transformed)),
              "all_objectives_nonincreasing":True})
