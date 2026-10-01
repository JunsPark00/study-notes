"""Original, self-contained numerical experiment. No network or external data.
Run: python chapter18.py --output-dir ./results
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

ENGLISH_LABELS = {'실행 가능 쌍곡선': 'Feasible hyperbola', '국소 등식 SQP 직접 구현': 'Implemented local equality SQP', '목표점': 'Target', '독립 계산한 해': 'Independent solution', '곡선 위 투영을 QP로 근사': 'QP models for projection', 'SQP 반복': 'SQP iteration', '최대 KKT 잔차': 'Maximum KKT residual', '제약과 정상성을 동시에 확인': 'Feasibility and stationarity'}
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

# New example: projection onto the positive hyperbola x*y=1.
a=np.array([2.,1.])
def f(x): return .5*np.sum((x-a)**2)
def c(x): return x[0]*x[1]-1.
def j(x): return np.array([x[1],x[0]])
Hc=np.array([[0.,1.],[1.,0.]])
t=brentq(lambda z:z-2-(1/z-1)/z**2,1,3,xtol=1e-14)
truth=np.array([t,1/t]); x=np.array([1.6,.7]); lam=0.
path=[x.copy()]; residuals=[]
for k in range(30):
    grad=x-a; J=j(x)
    residual=max(abs(c(x)),np.linalg.norm(grad-lam*J,np.inf))
    residuals.append(residual)
    if residual<1e-11: break
    B=np.eye(2)-lam*Hc  # Exact Lagrangian Hessian for L=f-lambda*c.
    assert np.linalg.eigvalsh(B).min()>0
    K=np.block([[B,-J[:,None]],[J[None,:],np.zeros((1,1))]])
    sol=np.linalg.solve(K,np.r_[-grad,-c(x)])
    p=sol[:2]; lam_qp=float(sol[2])
    rho=max(2.,abs(lam_qp)+1.)
    merit=lambda z:f(z)+rho*abs(c(z))
    slope=float(grad@p-rho*abs(c(x)))
    alpha=1.
    while (np.min(x+alpha*p)<=0 or merit(x+alpha*p)>merit(x)+1e-4*alpha*slope):
        alpha*=.5
        if alpha<1e-10: raise RuntimeError("Merit line search failed")
    x=x+alpha*p; lam=lam+alpha*(lam_qp-lam); path.append(x.copy())
else: raise RuntimeError("SQP iteration limit")
ref=minimize(f,[1.6,.7],jac=lambda z:z-a,method="SLSQP",bounds=[(.05,None),(.05,None)],
             constraints={"type":"eq","fun":c,"jac":j},options={"ftol":1e-13,"maxiter":100})
assert ref.success
metrics={"solution_x":float(x[0]),"solution_y":float(x[1]),"objective":float(f(x)),
         "solution_error":float(np.linalg.norm(x-truth,np.inf)),"constraint_violation":float(abs(c(x))),
         "stationarity":float(np.linalg.norm(x-a-lam*j(x),np.inf)),"multiplier":float(lam),
         "slsqp_solution_error":float(np.linalg.norm(ref.x-truth,np.inf)),"iterations":k}
assert max(metrics[t] for t in ("solution_error","constraint_violation","stationarity","slsqp_solution_error"))<1e-7
fig,ax=plt.subplots(1,2,figsize=(10,4.6),layout="constrained")
u=np.linspace(1.25,2.2,300); ax[0].plot(u,1/u,label=tr("실행 가능 쌍곡선"))
p=np.array(path); ax[0].plot(p[:,0],p[:,1],"o--",ms=5,label=tr("국소 등식 SQP 직접 구현"))
ax[0].scatter([2],[1],marker="x",s=80,label=tr("목표점"))
ax[0].scatter([t],[1/t],marker="*",s=150,color="#e07945",label=tr("독립 계산한 해"))
ax[0].set(xlabel="x",ylabel="y",title=tr("곡선 위 투영을 QP로 근사")); ax[0].legend(fontsize=9)
ax[1].semilogy(np.maximum(residuals,1e-16),"o-",lw=2)
ax[1].set(xlabel=tr("SQP 반복"),ylabel=tr("최대 KKT 잔차"),title=tr("제약과 정상성을 동시에 확인"))
ax[1].set_xticks(np.arange(len(residuals)))
finish(18,fig,metrics)
