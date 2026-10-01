#!/usr/bin/env python3
"""Original, self-contained teaching experiment. Not a production optimizer.
Run: python chapter06.py --output-dir ./output
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

Q=np.array([[3.,.8],[.8,1.5]]); b=np.array([1.,-2.]); star=np.linalg.solve(Q,b)
def f(x): return .5*float(x@Q@x)-float(b@x)
def grad(x): return Q@x-b
H=np.eye(2); x=np.array([-2.,2.]); path=[x.copy()]; inverse_models=[H.copy()]
secant=[]; minimum_eigenvalues=[]
for _ in range(5):
    g=grad(x)
    if np.linalg.norm(g)<1e-11: break
    p=-H@g; assert float(g@p)<0
    alpha=-float(g@p)/float(p@Q@p)
    new=x+alpha*p; s=new-x; y=grad(new)-g; sy=float(s@y)
    assert sy>1e-12*np.linalg.norm(s)*np.linalg.norm(y)
    rho=1/sy; V=np.eye(2)-rho*np.outer(s,y)
    H=V@H@V.T+rho*np.outer(s,s)
    H=(H+H.T)/2
    secant.append(float(np.linalg.norm(H@y-s)))
    minimum_eigenvalues.append(float(np.linalg.eigvalsh(H)[0]))
    x=new; path.append(x.copy()); inverse_models.append(H.copy())
assert len(path)-1==2 and np.linalg.norm(x-star)<1e-10
assert max(secant)<1e-10 and min(minimum_eigenvalues)>0
assert np.linalg.norm(H-np.linalg.inv(Q))<1e-10
# Independent one-update BFGS/DFP and indefinite SR1 checks.
s=np.array([1.,0.]); y=np.array([4.,1.]); initial=np.eye(2)
rho=1/float(s@y); V=np.eye(2)-rho*np.outer(s,y)
hb=V@initial@V.T+rho*np.outer(s,s)
hd=initial-np.outer(y,y)/float(y@y)+np.outer(s,s)/float(s@y)
assert np.linalg.norm(hb@y-s)<1e-12 and np.linalg.norm(hd@y-s)<1e-12
ys=np.array([-2.,.5]); v=ys-initial@s; denom=float(v@s)
assert abs(denom)>=1e-8*np.linalg.norm(v)*np.linalg.norm(s)
bs=initial+np.outer(v,v)/denom
assert np.linalg.norm(bs@s-ys)<1e-12 and np.linalg.eigvalsh(bs)[0]<0
path=np.array(path)
sd=[path[0].copy()]
for _ in range(30):
    gg=grad(sd[-1])
    if np.linalg.norm(gg)<1e-10: break
    aa=float(gg@gg)/float(gg@Q@gg); sd.append(sd[-1]-aa*gg)
sd=np.array(sd)
fig,ax=plt.subplots(1,2,figsize=(10,4.5),layout="constrained")
u,vv=np.meshgrid(np.linspace(-2.5,2.6,300),np.linspace(-2.8,2.5,300))
du=u-star[0]; dv=vv-star[1]
z=.5*(Q[0,0]*du**2+2*Q[0,1]*du*dv+Q[1,1]*dv**2)
ax[0].contour(u,vv,z,levels=[.05,.2,.5,1,2,4,8,16],colors="#a5b4fc",linewidths=.8)
ax[0].plot(sd[:,0],sd[:,1],"o-",color="#94a3b8",ms=3,label=label("최급강하", "Steepest descent"))
ax[0].plot(path[:,0],path[:,1],"o-",color="#0f766e",ms=5,label="BFGS")
ax[0].scatter(*star,marker="*",s=90,color="#e85d3f",zorder=5)
ax[0].set(xlabel=r"$x_1$",ylabel=r"$x_2$",aspect="equal",title=label("곡률 정보를 기억하는 두 단계", "Two steps that remember curvature"))
ax[0].legend(fontsize=8)
angles=np.linspace(0,2*np.pi,500); unit=np.stack([np.cos(angles),np.sin(angles)])
for k,hh in enumerate(inverse_models):
    vals,vecs=np.linalg.eigh(hh)
    points=vecs@np.diag(np.sqrt(vals))@unit
    ax[1].plot(points[0],points[1],lw=2,label=f"B{k}" + (label(" (정확)", " (exact)") if k==2 else ""))
ax[1].set(xlabel=r"$d_1$",ylabel=r"$d_2$",aspect="equal",title=label("단위 모델 등고선의 변화", "Changing unit model contours"))
ax[1].legend(fontsize=8); ax[1].grid(alpha=.2)
finish(6,fig,{"minimizer":star.tolist(),"bfgs_iterations":len(path)-1,"solution_error":float(np.linalg.norm(x-star)),
              "gradient_norm":float(np.linalg.norm(grad(x))),"max_inverse_secant_residual":max(secant),
              "minimum_inverse_eigenvalue":min(minimum_eigenvalues),"inverse_hessian_error":float(np.linalg.norm(H-np.linalg.inv(Q))),
              "worked_bfgs_inverse":hb.tolist(),"bfgs_dfp_matrix_difference":float(np.linalg.norm(hb-hd)),
              "sr1_minimum_eigenvalue":float(np.linalg.eigvalsh(bs)[0]),"sr1_secant_residual":float(np.linalg.norm(bs@s-ys))})
