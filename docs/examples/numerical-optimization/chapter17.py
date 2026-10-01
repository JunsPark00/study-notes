"""Original, self-contained numerical experiment. No network or external data.
Run: python chapter17.py --output-dir ./results
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

ENGLISH_LABELS = {'이차 벌점': 'Quadratic penalty', '절댓값 벌점': 'Absolute-value penalty', '임계값 0.4': 'Threshold 0.4', '벌점 계수': 'Penalty parameter', '등식 제약 위반': 'Equality violation', '정확성의 차이': 'Penalty exactness', '헤시안 조건수': 'Hessian condition number', '이차 벌점의 대가': 'Conditioning cost', '제약 위반': 'Constraint violation', '승수 오차': 'Multiplier error', '바깥 반복': 'Outer iteration', '오차': 'Error', '고정 계수의 증강 라그랑지안': 'Augmented Lagrangian, fixed penalty'}
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

a=np.array([2.,-1.]); A=np.array([2.,1.]); b=1.
truth=a-A*(A@a-b)/(A@A); lam_star=-(A@a-b)/(A@A)
rhos=np.logspace(-3,5,100)
penalty=[]; condition=[]; exact=[]
for rho in rhos:
    xp=np.linalg.solve(np.eye(2)+rho*np.outer(A,A),a+rho*b*A)
    penalty.append(abs(A@xp-b)); condition.append(np.linalg.cond(np.eye(2)+rho*np.outer(A,A)))
    residual=max(float(A@a-b)-rho*(A@A),0.)
    xe=a+A*(residual-(A@a-b))/(A@A)
    exact.append(abs(A@xe-b))
lam=0.; rho=1.; al=[]
for k in range(18):
    x=np.linalg.solve(np.eye(2)+rho*np.outer(A,A),a+(lam+rho*b)*A)
    residual=float(A@x-b)
    lam=lam-rho*residual
    al.append([abs(residual),abs(lam-lam_star),np.linalg.norm(x-truth,np.inf)])
metrics={"solution_x":float(x[0]),"solution_y":float(x[1]),"multiplier":float(lam),
         "al_constraint_violation":float(abs(A@x-b)),
         "al_solution_error":float(np.linalg.norm(x-truth,np.inf)),
         "al_multiplier_error":float(abs(lam-lam_star)),
         "al_stationarity":float(np.linalg.norm(x-a-lam*A,np.inf)),
         "largest_penalty_residual":float(penalty[-1]),"largest_penalty_condition":float(condition[-1]),
         "exact_penalty_threshold":float(abs(lam_star)),
         "exact_penalty_error_above_threshold":float(max(v for r,v in zip(rhos,exact) if r>=.4))}
assert max(metrics[k] for k in ("al_constraint_violation","al_solution_error","al_multiplier_error","al_stationarity","exact_penalty_error_above_threshold"))<1e-10
assert abs(penalty[-1]-2/(1+5*rhos[-1]))<1e-10
fig,ax=plt.subplots(1,3,figsize=(10,4.6),layout="constrained")
ax[0].loglog(rhos,penalty,label=tr("이차 벌점"))
ax[0].loglog(rhos,np.maximum(exact,1e-15),label=tr("절댓값 벌점"))
ax[0].axvline(.4,color="#7661a9",ls=":",label=tr("임계값 0.4"))
ax[0].set(xlabel=tr("벌점 계수"),ylabel=tr("등식 제약 위반"),title=tr("정확성의 차이")); ax[0].legend(fontsize=8)
ax[1].loglog(rhos,condition,color="#e07945")
ax[1].set(xlabel=tr("벌점 계수"),ylabel=tr("헤시안 조건수"),title=tr("이차 벌점의 대가"))
al=np.maximum(np.array(al),1e-16)
ax[2].semilogy(np.arange(1,len(al)+1),al[:,0],"o-",ms=3,label=tr("제약 위반"))
ax[2].semilogy(np.arange(1,len(al)+1),al[:,1],"s--",ms=3,label=tr("승수 오차"))
ax[2].set(xlabel=tr("바깥 반복"),ylabel=tr("오차"),title=tr("고정 계수의 증강 라그랑지안")); ax[2].legend(fontsize=8)
finish(17,fig,metrics)
