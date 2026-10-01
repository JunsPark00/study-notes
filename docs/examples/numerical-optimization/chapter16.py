"""Original, self-contained numerical experiment. No network or external data.
Run: python chapter16.py --output-dir ./results
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

ENGLISH_LABELS = {'활성집합 이동': 'Active-set steps', '유일 최적점': 'Unique optimum', '면 위의 QP와 작업집합 교체': 'QP steps and working sets', '상한 x+y≤2': 'x+y <= 2', '하한 x≥0': 'x >= 0', '하한 y≥0': 'y >= 0', 'KKT 승수': 'KKT multiplier', '활성 제약이 갖는 한계 비용': 'Marginal value of an active constraint'}
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
from scipy.optimize import minimize

H=np.array([[4.,1.],[1.,2.]]); g=np.array([-8.,-3.])
A=np.array([[-1.,-1.],[1.,0.],[0.,1.]])
b=np.array([2.,0.,0.])  # c(x)=A x+b >=0; L=q-lambda.T c.
def f(x): return .5*x@H@x+g@x
x=np.zeros(2); active=[1,2]; path=[x.copy()]
for iteration in range(20):
    W=A[active]; k=len(active)
    K=np.block([[H,-W.T],[W,np.zeros((k,k))]])
    sol=np.linalg.solve(K,np.r_[-(H@x+g),np.zeros(k)])
    p,lam=sol[:2],sol[2:]
    if np.linalg.norm(p,np.inf)<1e-11:
        if k==0 or lam.min()>=-1e-10:
            break
        active.pop(int(np.argmin(lam)))
        continue
    alpha=1.; blocker=None
    for j in range(3):
        if j not in active and A[j]@p < -1e-12:
            bound=-(A[j]@x+b[j])/(A[j]@p)
            if bound < alpha-1e-12:
                alpha=bound; blocker=j
            elif abs(bound-alpha)<1e-12 and blocker is None:
                blocker=j
    x=x+alpha*p; path.append(x.copy())
    assert min(A@x+b)>-1e-10
    if blocker is not None: active.append(blocker)
else: raise RuntimeError("Active-set iteration limit")
full_lam=np.zeros(3); full_lam[active]=lam
candidates=[]
for k in range(3):
    for ids in combinations(range(3),k):
        W=A[list(ids)]; K=np.block([[H,-W.T],[W,np.zeros((k,k))]])
        try: sol=np.linalg.solve(K,np.r_[-g,-b[list(ids)]])
        except np.linalg.LinAlgError: continue
        if np.min(A@sol[:2]+b)>=-1e-10 and (k==0 or np.min(sol[2:])>=-1e-10): candidates.append(sol[:2])
ref=minimize(f,[.5,.5],jac=lambda z:H@z+g,method="SLSQP",
             constraints={"type":"ineq","fun":lambda z:A@z+b,"jac":lambda z:A},
             options={"ftol":1e-13,"maxiter":100})
assert ref.success and candidates
metrics={"objective":float(f(x)),"solution_error":float(np.linalg.norm(x-[1.75,.25],np.inf)),
         "primal_violation":float(max(0.,-np.min(A@x+b))),
         "stationarity":float(np.linalg.norm(H@x+g-A.T@full_lam,np.inf)),
         "complementarity":float(np.linalg.norm(full_lam*(A@x+b),np.inf)),
         "multiplier_error":float(np.linalg.norm(full_lam-[.75,0,0],np.inf)),
         "enumeration_error":float(np.linalg.norm(x-candidates[0],np.inf)),
         "slsqp_error":float(np.linalg.norm(x-ref.x,np.inf)),"working_set_iterations":iteration+1}
assert max(metrics[k] for k in metrics if k not in ("objective","working_set_iterations"))<1e-7
fig,ax=plt.subplots(1,2,figsize=(10,4.6),layout="constrained")
u=np.linspace(-.1,2.25,160); X,Y=np.meshgrid(u,u)
Z=.5*(4*X*X+2*X*Y+2*Y*Y)-8*X-3*Y
ax[0].contour(X,Y,Z,levels=[-8.4,-8.125,-7.5,-6,-4,-1],colors="#b3bcc9",linewidths=1)
ax[0].fill([0,2,0],[0,0,2],color="#dceef0",alpha=.6)
p=np.array(path); ax[0].plot(p[:,0],p[:,1],"o-",lw=2,label=tr("활성집합 이동"))
ax[0].scatter([1.75],[.25],marker="*",s=140,color="#e07945",label=tr("유일 최적점"))
ax[0].set(xlabel="x",ylabel="y",title=tr("면 위의 QP와 작업집합 교체"),xlim=(-.1,2.25),ylim=(-.1,2.25))
ax[0].legend(fontsize=9)
ax[1].bar([tr("상한 x+y≤2"),tr("하한 x≥0"),tr("하한 y≥0")],full_lam,color=["#e07945","#156f87","#7661a9"])
ax[1].set(ylabel=tr("KKT 승수"),title=tr("활성 제약이 갖는 한계 비용"),ylim=(0,1))
finish(16,fig,metrics)
