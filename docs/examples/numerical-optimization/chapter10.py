"""Independent nonlinear least-squares experiment. Run: python chapter10.py --output-dir out"""
import argparse
import json
import os
import tempfile
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',tempfile.mkdtemp(prefix='opt-mpl-'))
os.environ.setdefault('XDG_CACHE_HOME', tempfile.mkdtemp(prefix='opt-cache-'))
import numpy as np
from scipy.optimize import least_squares
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,default=Path('output'));args=p.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(2026);t=np.linspace(0,4,25);truth=np.array([1.7,.65,.25]);initial=np.array([.8,.3,.1])
    def model(theta,t):return theta[0]*np.exp(-theta[1]*t)+theta[2]
    y=model(truth,t)+rng.normal(0,.025,t.size)
    def residual(theta):return model(theta,t)-y
    def jacobian(theta):
        e=np.exp(-theta[1]*t);return np.column_stack((e,-theta[0]*t*e,np.ones_like(t)))
    result=least_squares(residual,initial,jac=jacobian,method='trf',xtol=1e-13,ftol=1e-13,gtol=1e-13,max_nfev=200)
    residuals=residual(result.x);J=jacobian(result.x);stationarity=float(np.linalg.norm(J.T@residuals,np.inf));cost=float(.5*residuals@residuals)
    h=1e-6;numeric=np.column_stack([(residual(result.x+h*np.eye(3)[j])-residual(result.x-h*np.eye(3)[j]))/(2*h) for j in range(3)])
    jerror=float(np.max(np.abs(numeric-J)))
    assert result.success and stationarity<1e-8 and jerror<1e-8
    assert cost < .5*residual(initial)@residual(initial)
    assert np.linalg.matrix_rank(J)==3
    results={'seed':2026,'fitted_parameters':result.x.tolist(),'true_parameters':truth.tolist(),'half_sum_squared_residuals':cost,'residual_norm':float(np.linalg.norm(residuals)),'stationarity_inf_norm':stationarity,'jacobian_check_max_error':jerror,'jacobian_condition_number':float(np.linalg.cond(J)),'function_evaluations':result.nfev,'jacobian_evaluations':result.njev}
    font=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    if font.exists():font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams.update({'axes.unicode_minus':False,'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(1,2,figsize=(11,5.1),layout='constrained');grid=np.linspace(0,4,300)
    axs[0].scatter(t,y,s=26,color='#3b6fb6',label='합성 관측값');axs[0].plot(grid,model(result.x,grid),color='#d67931',lw=2,label='최소제곱 적합');axs[0].plot(grid,model(truth,grid),color='#2d8b76',ls='--',label='데이터 생성 곡선');axs[0].set(xlabel='시간 t',ylabel='측정 신호',title='지수 감쇠 모형');axs[0].legend(fontsize=9)
    axs[1].axhline(0,color='#9aa6b2',lw=1);axs[1].stem(t,residuals,basefmt=' ',linefmt='#3b6fb6',markerfmt='o');axs[1].set(xlabel='시간 t',ylabel='모형값 − 관측값',title='정상점에도 잔차는 남는다');axs[1].grid(alpha=.2)
    fig.suptitle('10장  모형 오차와 최적화 오차를 구분하기',fontsize=14)
    # English fallback when the optional local Korean font is absent.
    translations = {'합성 관측값': 'Synthetic observations', '최소제곱 적합': 'Least-squares fit', '데이터 생성 곡선': 'Data-generating curve', '시간 t': 'Time t', '측정 신호': 'Measured signal', '지수 감쇠 모형': 'Exponential decay model', '모형값 − 관측값': 'Model minus observation', '정상점에도 잔차는 남는다': 'Residuals remain at a stationary point', '10장  모형 오차와 최적화 오차를 구분하기': 'Chapter 10 · Separating model error from optimization error'}
    if not Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').exists():
        for artist in fig.findobj(matplotlib.text.Text):
            artist.set_text(translations.get(artist.get_text(), artist.get_text()))
    fig.savefig(args.output_dir/'chapter10.png',dpi=160);plt.close(fig)
    (args.output_dir/'chapter10.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(json.dumps(results,ensure_ascii=False))
if __name__=='__main__':main()
