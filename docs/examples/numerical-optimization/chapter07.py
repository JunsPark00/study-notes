"""Independent matrix-free CG experiment. Run: python chapter07.py --output-dir out"""
import argparse
import json
import os
import tempfile
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', tempfile.mkdtemp(prefix='opt-mpl-'))
os.environ.setdefault('XDG_CACHE_HOME', tempfile.mkdtemp(prefix='opt-cache-'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

def style():
    font = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    if font.exists():
        font_manager.fontManager.addfont(str(font))
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams.update({'axes.unicode_minus': False, 'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('output'))
    args = parser.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=True)
    n = 180; diagonal = np.geomspace(1.0, 1000.0, n)
    def matvec(v):
        out = diagonal * v
        diff = np.diff(v)
        out[:-1] -= 5 * diff; out[1:] += 5 * diff
        return out
    truth = np.sin(np.linspace(0, 2*np.pi, n))
    b = matvec(truth); jacobi = diagonal + 10; jacobi[[0,-1]] -= 5
    def cg(precondition):
        x = np.zeros(n); r = b.copy(); z = precondition(r); p = z.copy(); rz = r @ z
        hist = [float(np.linalg.norm(r)/np.linalg.norm(b))]
        for _ in range(1500):
            qp = matvec(p); curvature = p @ qp
            assert curvature > 0
            alpha = rz / curvature; x += alpha*p; r -= alpha*qp
            hist.append(float(np.linalg.norm(r)/np.linalg.norm(b)))
            if hist[-1] < 1e-11: break
            z = precondition(r); next_rz = r @ z; p = z+(next_rz/rz)*p; rz = next_rz
        actual = float(np.linalg.norm(matvec(x)-b)/np.linalg.norm(b))
        assert actual < 2e-11
        assert np.linalg.norm(x-truth)/np.linalg.norm(truth) < 1e-8
        return x, hist, actual
    x, h1, r1 = cg(lambda r:r)
    xp, h2, r2 = cg(lambda r:r/jacobi)
    results = {'n':n,'cg_iterations':len(h1)-1,'pcg_iterations':len(h2)-1,'cg_true_relative_residual':r1,'pcg_true_relative_residual':r2,'pcg_relative_solution_error':float(np.linalg.norm(xp-truth)/np.linalg.norm(truth)),'dense_hessian_bytes_n100000':8*100000**2,'lbfgs_pair_bytes_n100000_m7':8*2*100000*7}
    assert results['pcg_iterations'] < results['cg_iterations']
    style(); fig, ax = plt.subplots(figsize=(9.6,5.5),layout='constrained')
    ax.semilogy(h1,label='CG · 사전조건화 없음',color='#3b6fb6',lw=2)
    ax.semilogy(h2,label='PCG · 대각 사전조건화',color='#d67931',lw=2)
    ax.axhline(1e-11,color='#7d8791',ls=':',label='종료 기준')
    ax.set(xlabel='행렬 벡터 곱을 수행한 반복 수',ylabel='상대 선형계 잔차',title='7장  같은 이차문제, 서로 다른 내부 반복 비용')
    ax.grid(alpha=.22);ax.legend(loc='upper right')
    # English fallback when the optional local Korean font is absent.
    translations = {'CG · 사전조건화 없음': 'CG · no preconditioner', 'PCG · 대각 사전조건화': 'PCG · diagonal preconditioner', '종료 기준': 'Stopping tolerance', '행렬 벡터 곱을 수행한 반복 수': 'Iterations / matrix-vector products', '상대 선형계 잔차': 'Relative linear-system residual', '7장  같은 이차문제, 서로 다른 내부 반복 비용': 'Chapter 7 · One quadratic, different inner iteration costs'}
    if not Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').exists():
        for artist in fig.findobj(matplotlib.text.Text):
            artist.set_text(translations.get(artist.get_text(), artist.get_text()))
    fig.savefig(args.output_dir/'chapter07.png',dpi=160);plt.close(fig)
    (args.output_dir/'chapter07.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(results,ensure_ascii=False))
if __name__=='__main__': main()
