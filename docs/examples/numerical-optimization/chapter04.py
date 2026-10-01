#!/usr/bin/env python3
"""Original, self-contained teaching experiment. Not a production optimizer.
Run: python chapter04.py --output-dir ./output
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

B=np.diag([-1.,3.]); g=np.array([0.,2.]); delta=1.
def model(p): return float(g@p+.5*p@B@p)
def actual(p): return model(p)+.2*p[0]**4
lam=1.; solution=np.array([np.sqrt(.75),-.5])
cauchy=np.array([0.,-2/3])
stationarity=float(np.linalg.norm((B+lam*np.eye(2))@solution+g))
minimum_eigenvalue=float(np.linalg.eigvalsh(B+lam*np.eye(2))[0])
predicted=-model(solution); observed=-actual(solution); rho=observed/predicted
# Independent dense boundary check, plus the global optimality certificate.
theta=np.linspace(0,2*np.pi,200001)
boundary=np.stack([np.cos(theta),np.sin(theta)],axis=1)
values=boundary@g+.5*np.einsum("ni,ij,nj->n",boundary,B,boundary)
assert stationarity<1e-12 and minimum_eigenvalue>=-1e-12
assert abs(np.linalg.norm(solution)-delta)<1e-12
assert abs(model(solution)+1)<1e-12
assert abs(values.min()-model(solution))<1e-8
assert predicted>0 and abs(rho-.8875)<1e-12
assert model(solution)<model(cauchy)
# A separate positive-definite dogleg subproblem.
C=np.array([[4.,1.],[1.,2.]]); h=np.ones(2); radius=.4
pu=-(h@h)/(h@C@h)*h; pn=-np.linalg.solve(C,h)
d=pn-pu
roots=np.roots([d@d,2*pu@d,pu@pu-radius**2])
t=float(next(r.real for r in roots if abs(r.imag)<1e-12 and 0<=r.real<=1))
pdog=pu+t*d
assert abs(np.linalg.norm(pdog)-radius)<1e-12
fig,ax=plt.subplots(1,2,figsize=(10,4.5),layout="constrained")
a,b=np.meshgrid(np.linspace(-1.15,1.15,300),np.linspace(-1.15,1.15,300))
z=2*b+.5*(-a*a+3*b*b)
ax[0].contour(a,b,z,levels=[-1,-.9,-2/3,-.4,0,.5,1,2,3],colors="#a5b4fc",linewidths=.8)
theta_plot=np.linspace(0,2*np.pi,600)
ax[0].plot(np.cos(theta_plot),np.sin(theta_plot),color="#64748b",lw=1.5)
ax[0].scatter(*cauchy,color="#2563eb",s=55,label=label("Cauchy 점", "Cauchy point"),zorder=5)
ax[0].scatter([solution[0],-solution[0]],[solution[1],solution[1]],color="#e85d3f",s=65,
              label=label("두 전역 해", "Two global solutions"),zorder=5)
ax[0].set(aspect="equal",xlabel=r"$p_1$",ylabel=r"$p_2$",title=label("부정 곡률을 놓치지 않기", "Do not miss negative curvature"))
ax[0].legend(fontsize=8,loc="upper right")
t=np.linspace(0,1,300)
ax[1].plot(t,[model(v*solution) for v in t],color="#1d4ed8",lw=2,label=label("이차 모델", "Quadratic model"))
ax[1].plot(t,[actual(v*solution) for v in t],color="#0f766e",lw=2,label=label("실제 함수", "Actual function"))
ax[1].set(xlabel=label("선택한 단계의 비율 t", "Fraction of chosen step t"),ylabel=label("시작점 대비 함수값", "Change from starting value"),
          title=label("수락 비율 = 0.8875", "Acceptance ratio = 0.8875"))
ax[1].legend(fontsize=8); ax[1].grid(alpha=.2)
finish(4,fig,{"hard_case_solution":solution.tolist(),"model_value":model(solution),
              "cauchy_model_value":model(cauchy),"multiplier":lam,"stationarity_residual":stationarity,
              "shifted_minimum_eigenvalue":minimum_eigenvalue,"boundary_norm_error":abs(float(np.linalg.norm(solution))-1),
              "dense_boundary_value_gap":float(values.min()-model(solution)),"actual_reduction":observed,
              "predicted_reduction":predicted,"acceptance_ratio":rho,"dogleg_step":pdog.tolist(),
              "dogleg_boundary_error":abs(float(np.linalg.norm(pdog))-radius)})
