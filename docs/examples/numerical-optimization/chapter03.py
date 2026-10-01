#!/usr/bin/env python3
"""Original, self-contained teaching experiment. Not a production optimizer.
Run: python chapter03.py --output-dir ./output
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

from scipy.optimize import line_search
Q=np.array([[5.,1.],[1.,2.]])
x=np.array([1.5,-1.])
def f(v): return .5*float(v@Q@v)
def grad(v): return Q@v
g=grad(x); p=-g
slope=float(g@p); curvature=float(p@Q@p)
c1,c2=.1,.2
assert slope<0 and curvature>0
trials=[]; alpha=1.
for _ in range(50):
    ok=f(x+alpha*p)<=f(x)+c1*alpha*slope
    trials.append((alpha,ok))
    if ok: break
    alpha*=.5
else: raise RuntimeError("Armijo search exhausted")
wolfe=line_search(f,grad,x,p,gfk=g,c1=c1,c2=c2,maxiter=50)[0]
assert wolfe is not None and np.isfinite(wolfe)
armijo=lambda a: f(x+a*p)<=f(x)+c1*a*slope+1e-12
strong=lambda a: abs(float(grad(x+a*p)@p))<=c2*abs(slope)+1e-12
exact=-slope/curvature
assert armijo(alpha) and armijo(wolfe) and strong(wolfe)
assert abs(alpha-.25)<1e-14 and not strong(alpha)
assert abs(wolfe-exact)<1e-10
fig,ax=plt.subplots(1,2,figsize=(10,4.5),layout="constrained")
a=np.linspace(0,.5,500)
phi=np.array([f(x+t*p) for t in a]); derivative=slope+a*curvature
low=(1-c2)*exact; high=(1+c2)*exact
ax[0].axvspan(low,high,color="#a7f3d0",alpha=.75,label=label("강한 Wolfe 허용 구간","Strong Wolfe interval"))
ax[0].plot(a,phi,color="#1d4ed8",lw=2,label=r"$\phi(\alpha)$")
ax[0].plot(a,f(x)+c1*a*slope,"--",color="#64748b",label="Armijo")
ax[0].scatter([alpha,wolfe],[f(x+alpha*p),f(x+wolfe*p)],color=["#e85d3f","#0f766e"],s=55,zorder=5)
ax[0].set(xlabel=r"$\alpha$",ylabel=label("함수값", "Function value"),title=label("감소만 검사할 때의 선택", "Sufficient decrease alone"))
ax[0].legend(fontsize=8,loc="upper center")
ax[1].axhspan(c2*slope,-c2*slope,color="#a7f3d0",alpha=.75)
ax[1].plot(a,derivative,color="#7c3aed",lw=2)
ax[1].axhline(0,color="#94a3b8",lw=.8)
ax[1].scatter([alpha,wolfe],[slope+alpha*curvature,slope+wolfe*curvature],color=["#e85d3f","#0f766e"],s=55,zorder=5)
ax[1].set(xlabel=r"$\alpha$",ylabel=label("방향미분", "Directional derivative"),title=label("곡률 조건을 따로 확인", "Check curvature separately"))
finish(3,fig,{"initial_slope":slope,"directional_curvature":curvature,
              "armijo_alpha":alpha,"armijo_trials":[{"alpha":a,"accepted":bool(ok)} for a,ok in trials],
              "armijo_step_satisfies_strong_wolfe":bool(strong(alpha)),"strong_wolfe_alpha":float(wolfe),
              "exact_alpha":float(exact),"strong_wolfe_derivative":float(grad(x+wolfe*p)@p),
              "strong_wolfe_conditions_verified":True})
