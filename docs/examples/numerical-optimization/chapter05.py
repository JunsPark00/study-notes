#!/usr/bin/env python3
"""Original, self-contained teaching experiment. Not a production optimizer.
Run: python chapter05.py --output-dir ./output
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

def cg(A,b,precondition=False,tolerance=1e-10,maxiter=1000):
    x=np.zeros_like(b); r=b-A@x
    diagonal=np.diag(A) if precondition else np.ones_like(b)
    z=r/diagonal; p=z.copy(); rz=float(r@z)
    history=[float(np.linalg.norm(r)/np.linalg.norm(b))]; directions=[]
    for _ in range(maxiter):
        ap=A@p; denom=float(p@ap)
        if denom<=0: raise ValueError("CG needs SPD curvature")
        directions.append(p.copy())
        alpha=rz/denom; x=x+alpha*p; r=r-alpha*ap
        true=float(np.linalg.norm(b-A@x)/np.linalg.norm(b))
        history.append(true)
        if true<tolerance: break
        z=r/diagonal; next_rz=float(r@z)
        p=z+(next_rz/rz)*p; rz=next_rz
    else: raise RuntimeError("CG exhausted iterations")
    return x,np.array(history),np.array(directions)
small=np.array([[3.,1.],[1.,2.]]); rhs=np.array([1.,2.])
xs,hs,ps=cg(small,rhs,tolerance=1e-13)
assert len(hs)-1==2 and np.linalg.norm(xs-[0.,1.])<1e-12
normalized_conjugacy=abs(float(ps[0]@small@ps[1]))/np.sqrt(float(ps[0]@small@ps[0])*float(ps[1]@small@ps[1]))
assert normalized_conjugacy<1e-12
n=60; scale=np.geomspace(1.,30.,n)
T=np.diag(np.full(n,3.))+np.diag(np.full(n-1,-.6),1)+np.diag(np.full(n-1,-.6),-1)
A=scale[:,None]*T*scale[None,:]
rng=np.random.default_rng(20261001); b=rng.normal(size=n)
plain,hplain,_=cg(A,b)
pre,hpre,_=cg(A,b,True)
reference=np.linalg.solve(A,b)
assert hplain[-1]<1e-10 and hpre[-1]<1e-10
assert np.linalg.norm(pre-reference)/np.linalg.norm(reference)<1e-9
assert len(hpre)<len(hplain)
fig,ax=plt.subplots(1,2,figsize=(10,4.5),layout="constrained")
ax[0].semilogy(hplain,color="#e85d3f",lw=2,label=label("전처리 없음", "No preconditioner"))
ax[0].semilogy(hpre,color="#0f766e",lw=2,label=label("Jacobi 전처리", "Jacobi preconditioner"))
ax[0].axhline(1e-10,color="#94a3b8",ls="--",lw=1)
ax[0].set(xlabel=label("반복 번호", "Iteration"),ylabel=label("원래 계의 상대 잔차", "Original-system relative residual"),
          title=label("좌표 크기 차이를 줄인 효과", "Reducing coordinate scale imbalance"))
ax[0].legend(fontsize=8); ax[0].grid(alpha=.2,which="both")
eig_plain=np.linalg.eigvalsh(A)
scaled=A/np.sqrt(np.diag(A)[:,None]*np.diag(A)[None,:])
eig_pre=np.linalg.eigvalsh(scaled)
ax[1].semilogy(range(1,n+1),eig_plain,".",color="#e85d3f",label=label("원래 행렬", "Original matrix"))
ax[1].semilogy(range(1,n+1),eig_pre,".",color="#0f766e",label=label("대칭 전처리 행렬", "Symmetrically preconditioned"))
ax[1].set(xlabel=label("정렬한 고유값 번호", "Sorted eigenvalue index"),ylabel=label("고유값", "Eigenvalue"),
          title=label("조건수와 분포도 함께 보기", "Look at condition and spectrum"))
ax[1].legend(fontsize=8); ax[1].grid(alpha=.2,which="both")
finish(5,fig,{"small_solution":xs.tolist(),"small_iterations":len(hs)-1,"small_normalized_conjugacy_error":float(normalized_conjugacy),
              "dimension":n,"plain_iterations":len(hplain)-1,"jacobi_iterations":len(hpre)-1,
              "plain_relative_true_residual":float(hplain[-1]),"jacobi_relative_true_residual":float(hpre[-1]),
              "jacobi_relative_solution_error":float(np.linalg.norm(pre-reference)/np.linalg.norm(reference)),
              "plain_condition_number":float(eig_plain[-1]/eig_plain[0]),
              "preconditioned_condition_number":float(eig_pre[-1]/eig_pre[0])})
