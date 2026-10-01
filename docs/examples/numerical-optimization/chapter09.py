"""Independent coordinate polling experiment. Run: python chapter09.py --output-dir out"""
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
    def f(x):return (x[0]+2*x[1]-.7)**2+.2*(2*x[0]-x[1]+1.1)**2
    x=np.array([2.,-1.5]);step=1.;value=f(x);evaluations=1;history=[value];counts=[1];path=[x.copy()];failed_polls=0
    directions=np.array([[1.,0.],[-1.,0.],[0.,1.],[0.,-1.]])
    while step>=1e-6:
        candidates=x+step*directions;values=np.array([f(z) for z in candidates]);evaluations+=4;j=int(values.argmin())
        if values[j] < value-1e-4*step**2:
            x=candidates[j];value=float(values[j]);path.append(x.copy())
        else:step*=.5;failed_polls+=1
        history.append(value);counts.append(evaluations)
        assert evaluations<100000
    truth=np.array([-.3,.5]);error=float(np.linalg.norm(x-truth))
    assert error<1e-5 and value<1e-10
    assert np.all(np.diff(history)<=1e-15)
    results={'solution':x.tolist(),'objective':value,'solution_error':error,'function_evaluations':evaluations,'accepted_moves':len(path)-1,'failed_polls':failed_polls,'final_poll_radius':step}
    font=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    if font.exists():font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams.update({'axes.unicode_minus':False,'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(1,2,figsize=(11,5.1),layout='constrained');xx,yy=np.meshgrid(np.linspace(-1,2.4,260),np.linspace(-1.9,1.1,260));zz=f(np.array([xx,yy]));path=np.array(path)
    axs[0].contour(xx,yy,zz,levels=[.01,.1,.5,1,2,4,8,16],colors='#ccd4dd');axs[0].plot(path[:,0],path[:,1],'-o',color='#3b6fb6',ms=3,lw=1.4,label='수락된 이동');axs[0].scatter(*truth,marker='*',s=130,color='#d67931',label='해석적 최소점',zorder=5)
    axs[0].set(xlabel=r'$x_1$',ylabel=r'$x_2$',title='좌표 방향만 조사한 경로');axs[0].legend(fontsize=9)
    axs[1].semilogy(counts,np.maximum(history,1e-16),color='#3b6fb6',lw=2);axs[1].set(xlabel='누적 함수 평가 수',ylabel='목적함수값',title='수락되지 않은 탐색도 평가 비용');axs[1].grid(alpha=.22)
    fig.suptitle('9장  기울기 없이 움직이는 좌표 폴링',fontsize=14)
    # English fallback when the optional local Korean font is absent.
    translations = {'수락된 이동': 'Accepted moves', '해석적 최소점': 'Analytical minimizer', '좌표 방향만 조사한 경로': 'Coordinate polling trajectory', '누적 함수 평가 수': 'Cumulative function evaluations', '목적함수값': 'Objective value', '수락되지 않은 탐색도 평가 비용': 'Rejected polls also cost evaluations', '9장  기울기 없이 움직이는 좌표 폴링': 'Chapter 9 · Coordinate polling without gradients'}
    if not Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').exists():
        for artist in fig.findobj(matplotlib.text.Text):
            artist.set_text(translations.get(artist.get_text(), artist.get_text()))
    fig.savefig(args.output_dir/'chapter09.png',dpi=160);plt.close(fig)
    (args.output_dir/'chapter09.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(json.dumps(results,ensure_ascii=False))
if __name__=='__main__':main()
