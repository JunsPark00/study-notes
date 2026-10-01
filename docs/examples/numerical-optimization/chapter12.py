"""Independent half-space projection and KKT experiment. Run: python chapter12.py --output-dir out"""
import argparse
import json
import os
import tempfile
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',tempfile.mkdtemp(prefix='opt-mpl-'))
os.environ.setdefault('XDG_CACHE_HOME', tempfile.mkdtemp(prefix='opt-cache-'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,default=Path('output'));args=p.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    a=np.array([2.,1.5]);normal=np.array([1.,2.]);b=3.
    def project(bound):
        lam=max(0.,float((normal@a-bound)/(normal@normal)));x=a-lam*normal
        return x,lam,float(.5*(x-a)@(x-a))
    x,lam,value=project(b);slack=float(b-normal@x);stationarity=float(np.linalg.norm(x-a+lam*normal));dual=float(lam*(normal@a-b)-.5*lam**2*(normal@normal));h=1e-5;derivative=(project(b+h)[2]-project(b-h)[2])/(2*h)
    assert np.allclose(x,[1.6,.7]) and abs(lam-.4)<1e-14
    assert stationarity<1e-14 and slack>=-1e-14 and abs(lam*slack)<1e-14
    assert abs(value-dual)<1e-14 and abs(derivative+lam)<1e-9
    results={'solution':x.tolist(),'multiplier':lam,'objective':value,'constraint_slack':slack,'stationarity_norm':stationarity,'complementarity_absolute':abs(lam*slack),'dual_value':dual,'duality_gap':abs(value-dual),'value_derivative_finite_difference':derivative,'sensitivity_error':abs(derivative+lam)}
    font=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    if font.exists():font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams.update({'axes.unicode_minus':False,'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(1,2,figsize=(11,5.2),layout='constrained');xx,yy=np.meshgrid(np.linspace(-.2,3,240),np.linspace(-.2,2.5,240));cost=.5*((xx-a[0])**2+(yy-a[1])**2)
    axs[0].contourf(xx,yy,(xx+2*yy<=b).astype(float),levels=[.5,1.5],colors=['#e5f2eb']);axs[0].contour(xx,yy,cost,levels=[.1,.4,.8,1.5,2.5],colors='#aebac7');line=np.linspace(-.2,3,100);axs[0].plot(line,(b-line)/2,color='#2d8b76',lw=2,label='활성 경계');axs[0].plot([a[0],x[0]],[a[1],x[1]],'--',color='#d67931');axs[0].scatter(*a,s=55,color='#d67931',label='무제약 최소점');axs[0].scatter(*x,s=100,marker='*',color='#3b6fb6',label='제약 최소점');axs[0].set(xlim=(-.2,3),ylim=(-.2,2.5),xlabel=r'$x_1$',ylabel=r'$x_2$',title='녹색 영역 안에서 가장 가까운 점');axs[0].legend(fontsize=8,loc='upper left')
    bs=np.linspace(.5,6,180);vals=np.array([project(bb)[2] for bb in bs]);axs[1].plot(bs,vals,color='#3b6fb6',lw=2,label='최적값 v(b)');near=np.linspace(2.2,3.8,50);axs[1].plot(near,value-lam*(near-b),'--',color='#d67931',label='b=3에서의 접선');axs[1].scatter(b,value,color='#d67931');axs[1].axvline(5,color='#aebac7',ls=':');axs[1].set(xlabel='허용 상한 b',ylabel='최적 목적함수값',title='상한을 풀어주면 비용이 감소한다');axs[1].legend(fontsize=9);axs[1].grid(alpha=.2)
    fig.suptitle('12장  KKT 승수와 최적값 민감도의 부호',fontsize=14)
    # English fallback when the optional local Korean font is absent.
    translations = {'활성 경계': 'Active boundary', '무제약 최소점': 'Unconstrained minimizer', '제약 최소점': 'Constrained minimizer', '녹색 영역 안에서 가장 가까운 점': 'Closest point inside the green feasible region', '최적값 v(b)': 'Optimal value v(b)', 'b=3에서의 접선': 'Tangent at b = 3', '허용 상한 b': 'Constraint upper bound b', '최적 목적함수값': 'Optimal objective value', '상한을 풀어주면 비용이 감소한다': 'Relaxing the bound lowers the cost', '12장  KKT 승수와 최적값 민감도의 부호': 'Chapter 12 · KKT multiplier and value sensitivity'}
    if not Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').exists():
        for artist in fig.findobj(matplotlib.text.Text):
            artist.set_text(translations.get(artist.get_text(), artist.get_text()))
    fig.savefig(args.output_dir/'chapter12.png',dpi=160);plt.close(fig)
    (args.output_dir/'chapter12.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(json.dumps(results,ensure_ascii=False))
if __name__=='__main__':main()
