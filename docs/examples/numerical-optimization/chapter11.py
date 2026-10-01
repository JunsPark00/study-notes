"""Independent damped Newton and Broyden experiment. Run: python chapter11.py --output-dir out"""
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
    def F(x):return np.array([np.exp(x[0])+x[1]-2,x[0]+x[1]**2-1])
    def J(x):return np.array([[np.exp(x[0]),1.],[1.,2*x[1]]])
    def solve(broyden=False):
        x=np.array([.5,.7]);B=J(x);values=[float(np.linalg.norm(F(x)))];path=[x.copy()];secant_errors=[];evals=1
        for _ in range(80):
            fx=F(x)
            if values[-1]<1e-12:break
            if not broyden:B=J(x)
            direction=np.linalg.solve(B,-fx);alpha=1.;merit=.5*fx@fx
            for _ in range(40):
                new=x+alpha*direction;fn=F(new);evals+=1
                if .5*fn@fn <= (1-1e-4*alpha)*merit:break
                alpha*=.5
            else:raise AssertionError('Backtracking did not find an accepted step')
            s=new-x;y=fn-fx
            if broyden:
                B=B+np.outer(y-B@s,s)/(s@s)
                secant_errors.append(float(np.linalg.norm(B@s-y)))
            x=new;values.append(float(np.linalg.norm(fn)));path.append(x.copy())
        assert values[-1]<1e-12 and np.linalg.norm(x-np.array([0.,1.]))<1e-10
        return x,values,path,secant_errors,evals
    nx,nh,npth,_,ne=solve();bx,bh,bpth,se,be=solve(True)
    assert max(se,default=0)<1e-12
    results={'newton_iterations':len(nh)-1,'broyden_iterations':len(bh)-1,'newton_residual_norm':nh[-1],'broyden_residual_norm':bh[-1],'newton_solution':nx.tolist(),'broyden_solution':bx.tolist(),'maximum_broyden_secant_error':max(se),'newton_trial_evaluations':ne,'broyden_trial_evaluations':be}
    font=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    if font.exists():font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams.update({'axes.unicode_minus':False,'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(1,2,figsize=(11,5.1),layout='constrained');u,v=np.meshgrid(np.linspace(-.15,.6,250),np.linspace(.6,1.12,250));ff=F(np.array([u,v]));axs[0].contour(u,v,ff[0],levels=[0],colors=['#3b6fb6']);axs[0].contour(u,v,ff[1],levels=[0],colors=['#2d8b76'])
    for path,label,color in [(npth,'Newton','#d67931'),(bpth,'Broyden','#875cb8')]:
        path=np.array(path);axs[0].plot(path[:,0],path[:,1],'-o',ms=4,lw=1.2,label=label,color=color)
    axs[0].scatter(0,1,s=110,marker='*',color='#253647',zorder=6);axs[0].set(xlabel=r'$x_1$',ylabel=r'$x_2$',title='두 영점 곡선의 교점으로 접근');axs[0].legend()
    axs[1].semilogy(nh,'-o',label='Newton',color='#d67931');axs[1].semilogy(bh,'-o',label='Broyden',color='#875cb8');axs[1].set(xlabel='수락한 반복 수',ylabel='방정식 잔차의 2 노름',title='종료 판정은 F 자체의 크기');axs[1].grid(alpha=.22);axs[1].legend()
    fig.suptitle('11장  같은 국소 해, 서로 다른 야코비안 비용',fontsize=14)
    # English fallback when the optional local Korean font is absent.
    translations = {'두 영점 곡선의 교점으로 접근': 'Approaching intersecting zero-level curves', '수락한 반복 수': 'Accepted iterations', '방정식 잔차의 2 노름': 'Euclidean norm of equation residual', '종료 판정은 F 자체의 크기': 'Check F itself before declaring a root', '11장  같은 국소 해, 서로 다른 야코비안 비용': 'Chapter 11 · One local root, different Jacobian costs'}
    if not Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').exists():
        for artist in fig.findobj(matplotlib.text.Text):
            artist.set_text(translations.get(artist.get_text(), artist.get_text()))
    fig.savefig(args.output_dir/'chapter11.png',dpi=160);plt.close(fig)
    (args.output_dir/'chapter11.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(json.dumps(results,ensure_ascii=False))
if __name__=='__main__':main()
