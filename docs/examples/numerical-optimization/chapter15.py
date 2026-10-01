"""Original, self-contained numerical experiment. No network or external data.
Run: python chapter15.py --output-dir ./results
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

ENGLISH_LABELS = {'비선형 실행 가능 곡선': 'Nonlinear feasible curve', 'SLSQP 관측 경로': 'Observed SLSQP path', '무제약 목표점': 'Unconstrained target', '제약 최소점': 'Constrained optimum', '목적값과 실행 가능성의 두 목표': 'Objective and feasibility', '접선 이동 뒤 위반': 'Tangent-step violation', '2차 보정 뒤 위반': 'After second-order correction', '접선 이동 크기 h': 'Tangent displacement h', '원래 제약의 절댓값': 'Absolute original constraint', '선형화는 곡률을 지우지 못함': 'Curvature remains after linearization'}
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

from scipy.optimize import minimize, brentq

a=np.array([1.,.25])
def f(x): return .5*np.sum((x-a)**2)
def g(x): return x-a
def con(x): return x[1]-x[0]**2
def jac(x): return np.array([-2*x[0],1.])
t=brentq(lambda z: 2*z**3+.5*z-1,0,1,xtol=1e-14)
truth=np.array([t,t*t]); path=[np.array([.1,.8])]
result=minimize(f,path[0],jac=g,method="SLSQP",
                constraints={"type":"eq","fun":con,"jac":jac},
                callback=lambda x: path.append(x.copy()),
                options={"ftol":1e-13,"maxiter":100})
assert result.success
x=result.x; lam=float(jac(x)@g(x)/(jac(x)@jac(x)))
steps=np.logspace(-4,-.3,30)
raw=[]; corrected=[]
for h in steps:
    trial=truth+np.array([h,2*t*h])
    fix=trial+np.array([0,h*h])
    raw.append(abs(con(trial))); corrected.append(abs(con(fix)))
metrics={"solution_x":float(x[0]),"solution_y":float(x[1]),"objective":float(f(x)),
         "solution_error":float(np.linalg.norm(x-truth,np.inf)),
         "constraint_violation":float(abs(con(x))),
         "stationarity":float(np.linalg.norm(g(x)-lam*jac(x),np.inf)),
         "tangent_curvature_error":float(np.max(np.abs(np.array(raw)-steps**2))),
         "corrected_violation":float(max(corrected)),"iterations":int(result.nit)}
assert metrics["solution_error"]<1e-6
assert metrics["constraint_violation"]<1e-10 and metrics["stationarity"]<1e-6
assert metrics["corrected_violation"]<1e-12
fig,ax=plt.subplots(1,2,figsize=(10,4.6),layout="constrained")
z=np.linspace(-.05,1.3,300)
ax[0].plot(z,z*z,label=tr("비선형 실행 가능 곡선"))
p=np.array(path); ax[0].plot(p[:,0],p[:,1],"o--",ms=4,label=tr("SLSQP 관측 경로"))
ax[0].scatter([a[0]],[a[1]],marker="x",s=70,label=tr("무제약 목표점"))
ax[0].scatter([t],[t*t],marker="*",s=140,color="#e07945",label=tr("제약 최소점"))
ax[0].set(xlabel="x",ylabel="y",title=tr("목적값과 실행 가능성의 두 목표"))
ax[0].legend(fontsize=9)
ax[1].loglog(steps,raw,"o-",ms=3,label=tr("접선 이동 뒤 위반"))
ax[1].loglog(steps,np.maximum(corrected,1e-16),".-",label=tr("2차 보정 뒤 위반"))
ax[1].set(xlabel=tr("접선 이동 크기 h"),ylabel=tr("원래 제약의 절댓값"),title=tr("선형화는 곡률을 지우지 못함"))
ax[1].legend(fontsize=9)
finish(15,fig,metrics)
