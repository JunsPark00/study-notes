"""Original, self-contained numerical experiment. No network or external data.
Run: python chapter14.py --output-dir ./results
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

ENGLISH_LABELS = {'원시 변수의 첫 두 성분': 'First two primal variables', 'LP 최적점': 'LP optimum', '불능 시작 원시·쌍대 경로': 'Infeasible-start primal-dual path', '원시 잔차': 'Primal residual', '쌍대 잔차': 'Dual residual', '평균 상보성': 'Mean complementarity', '반복': 'Iteration', '잔차 / 평균 상보성': 'Residual / mean complementarity', '양수성과 방정식 잔차를 함께 관리': 'Residuals and complementarity'}
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

from scipy.optimize import linprog

A=np.array([[2.,1.,1.,0.,0.],[1.,2.,0.,1.,0.],[1.,0.,0.,0.,1.]])
b=np.array([8.,8.,3.]); c=np.array([-4.,-3.,0.,0.,0.])
m,n=A.shape
x=np.ones(n); s=np.ones(n); y=np.zeros(m)
history=[]; path=[]
def boundary(v,d):
    neg=d<0
    return min(1., .995*np.min(-v[neg]/d[neg])) if np.any(neg) else 1.
for k in range(80):
    rp=A@x-b; rd=A.T@y+s-c; mu=x@s/n
    history.append([np.linalg.norm(rp,np.inf),np.linalg.norm(rd,np.inf),mu])
    path.append(x.copy())
    if max(history[-1]) < 1e-10:
        break
    K=np.block([[np.zeros((n,n)),A.T,np.eye(n)],
                [A,np.zeros((m,m)),np.zeros((m,n))],
                [np.diag(s),np.zeros((n,m)),np.diag(x)]])
    rhs=np.r_[-rd,-rp,.15*mu*np.ones(n)-x*s]
    step=np.linalg.solve(K,rhs)
    dx,dy,ds=step[:n],step[n:n+m],step[n+m:]
    ap=boundary(x,dx); ad=boundary(s,ds)
    x+=ap*dx; y+=ad*dy; s+=ad*ds
    assert min(x.min(),s.min()) > 0
else: raise RuntimeError("No convergence")
reference=linprog(c,A_eq=A,b_eq=b,method="highs-ipm")
assert reference.success
metrics={"objective":float(c@x),"primal_residual":float(np.linalg.norm(A@x-b,np.inf)),
         "dual_residual":float(np.linalg.norm(A.T@y+s-c,np.inf)),
         "mean_complementarity":float(x@s/n),"duality_gap":float(abs(c@x-b@y)),
         "solution_error":float(np.linalg.norm(x[:2]-8/3,np.inf)),
         "highs_objective_gap":float(abs(c@x-reference.fun)),"iterations":k}
assert metrics["solution_error"] < 1e-7
assert max(metrics[t] for t in ("primal_residual","dual_residual","duality_gap","highs_objective_gap")) < 1e-7
fig,ax=plt.subplots(1,2,figsize=(10,4.6),layout="constrained")
poly=np.array([[0,0],[3,0],[3,2],[8/3,8/3],[0,4],[0,0]])
ax[0].fill(poly[:,0],poly[:,1],color="#dceef0")
p=np.array(path); ax[0].plot(p[:,0],p[:,1],"o-",ms=4,label=tr("원시 변수의 첫 두 성분"))
ax[0].scatter([8/3],[8/3],s=130,marker="*",color="#e07945",label=tr("LP 최적점"))
ax[0].set(xlabel="x",ylabel="y",title=tr("불능 시작 원시·쌍대 경로"),xlim=(-.15,3.7),ylim=(-.15,4.5))
ax[0].legend(fontsize=9)
h=np.maximum(np.array(history),1e-16)
for j,label in enumerate([tr("원시 잔차"),tr("쌍대 잔차"),tr("평균 상보성")]): ax[1].semilogy(h[:,j],"o-",ms=3,label=label)
ax[1].set(xlabel=tr("반복"),ylabel=tr("잔차 / 평균 상보성"),title=tr("양수성과 방정식 잔차를 함께 관리"))
ax[1].legend(fontsize=9)
finish(14,fig,metrics)
