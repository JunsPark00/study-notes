"""Original, self-contained numerical experiment. No network or external data.
Run: python chapter19.py --output-dir ./results
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

ENGLISH_LABELS = {'타원 내부': 'Ellipse interior', '직접 계산한 장벽 중심점': 'Computed barrier centers', '원문제의 경계 해': 'Original boundary solution', '중심 경로가 활성 경계로 접근': 'Central path approaches the boundary', '여유 c(x)': 'Slack c(x)', '승수 λ=μ/c(x)': 'Multiplier lambda = mu/c(x)', '상보성 λc(x)': 'Complementarity lambda*c(x)', '감소하는 장벽 계수 μ': 'Decreasing barrier parameter mu', '값': 'Value', '작은 여유와 유한 승수의 곱': 'Slack, multiplier and their product'}
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

from scipy.optimize import brentq

a=np.array([3.,1.]); Hc=np.diag([-.5,-2.])
def f(x): return .5*np.sum((x-a)**2)
def c(x): return 1-x[0]**2/4-x[1]**2
def j(x): return np.array([-x[0]/2,-2*x[1]])
def at_multiplier(lam): return np.array([3/(1+lam/2),1/(1+2*lam)])
lam_star=brentq(lambda z:c(at_multiplier(z)),0,10,xtol=1e-14)
truth=at_multiplier(lam_star)
mus=np.logspace(0,-6,19); x=np.zeros(2); path=[]; records=[]; inner_counts=[]
for mu in mus:
    for inner in range(100):
        slack=c(x); J=j(x); lam=mu/slack
        grad=x-a-lam*J
        if np.linalg.norm(grad,np.inf)<1e-8: break
        H=np.eye(2)-lam*Hc+(mu/slack**2)*np.outer(J,J)
        p=np.linalg.solve(H,-grad)
        old=f(x)-mu*np.log(slack); slope=grad@p; alpha=1.
        while c(x+alpha*p)<=0 or f(x+alpha*p)-mu*np.log(c(x+alpha*p))>old+1e-4*alpha*slope:
            alpha*=.5
            if alpha<1e-12: raise RuntimeError("Barrier line search stalled")
        x=x+alpha*p
    else: raise RuntimeError("Barrier Newton iteration limit")
    slack=c(x); lam=mu/slack
    # Independent scalar equation for the finite-mu central point.
    exact_lam=brentq(lambda z:z*c(at_multiplier(z))-mu,lam_star,lam_star+10,xtol=1e-14)
    exact=at_multiplier(exact_lam)
    path.append(x.copy()); inner_counts.append(inner)
    records.append([slack,lam,np.linalg.norm(x-a-lam*j(x),np.inf),np.linalg.norm(x-exact,np.inf)])
rec=np.array(records)
metrics={"solution_x":float(x[0]),"solution_y":float(x[1]),"objective":float(f(x)),
         "final_barrier_parameter":float(mus[-1]),"final_slack":float(c(x)),
         "original_solution_error":float(np.linalg.norm(x-truth,np.inf)),
         "maximum_barrier_stationarity":float(rec[:,2].max()),
         "maximum_central_path_error":float(rec[:,3].max()),
         "final_complementarity":float(lam*c(x)),"reference_multiplier":float(lam_star),
         "outer_steps":len(mus),"newton_steps":sum(inner_counts)}
assert c(x)>0 and lam>0
assert metrics["original_solution_error"]<3e-6
assert metrics["maximum_barrier_stationarity"]<1e-7
assert metrics["maximum_central_path_error"]<1e-7
assert abs(metrics["final_complementarity"]-mus[-1])<1e-12
fig,ax=plt.subplots(1,2,figsize=(10,4.6),layout="constrained")
angle=np.linspace(0,2*np.pi,500)
ax[0].fill(2*np.cos(angle),np.sin(angle),color="#dceef0",label=tr("타원 내부"))
p=np.array(path); ax[0].plot(p[:,0],p[:,1],"o-",ms=4,label=tr("직접 계산한 장벽 중심점"))
ax[0].scatter([truth[0]],[truth[1]],marker="*",s=150,color="#e07945",label=tr("원문제의 경계 해"))
ax[0].set(xlabel="x",ylabel="y",title=tr("중심 경로가 활성 경계로 접근"),xlim=(.7,2.15),ylim=(.05,.95))
ax[0].legend(fontsize=8,loc="upper right")
ax[1].loglog(mus,rec[:,0],"o-",ms=4,label=tr("여유 c(x)"))
ax[1].loglog(mus,rec[:,1],"s-",ms=4,label=tr("승수 λ=μ/c(x)"))
ax[1].loglog(mus,rec[:,0]*rec[:,1],"--",label=tr("상보성 λc(x)"))
ax[1].invert_xaxis(); ax[1].set(xlabel=tr("감소하는 장벽 계수 μ"),ylabel=tr("값"),title=tr("작은 여유와 유한 승수의 곱"))
ax[1].legend(fontsize=9)
finish(19,fig,metrics)
