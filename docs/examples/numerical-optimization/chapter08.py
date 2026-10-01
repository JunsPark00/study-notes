"""Independent derivative error experiment. Run: python chapter08.py --output-dir out"""
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

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,default=Path('output'))
    args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    def f(x): return np.exp(x)+np.sin(3*x)
    x=.37; exact=np.exp(x)+3*np.cos(3*x);h=np.logspace(-16,-1,151)
    forward=np.abs((f(x+h)-f(x))/h-exact)
    central=np.abs((f(x+h)-f(x-h))/(2*h)-exact)
    complex_step=np.abs(np.imag(f(x+1j*h))/h-exact)
    assert central.min() < 1e-8
    assert abs(np.imag(f(x+1e-20j))/1e-20-exact) < 1e-12
    assert forward[0] > forward.min()*1e4
    results={'point':x,'exact_derivative':float(exact),'best_forward_error':float(forward.min()),'best_forward_h':float(h[forward.argmin()]),'best_central_error':float(central.min()),'best_central_h':float(h[central.argmin()]),'complex_step_error_h1e20':float(abs(np.imag(f(x+1e-20j))/1e-20-exact))}
    font=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    if font.exists():
        font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams.update({'axes.unicode_minus':False,'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(9.6,5.5),layout='constrained')
    floor=1e-16
    for error,label,color in [(forward,'전진차분','#3b6fb6'),(central,'중앙차분','#d67931'),(complex_step,'복소 스텝','#2d8b76')]:
        ax.loglog(h,np.maximum(error,floor),label=label,color=color,lw=2)
    ax.set(xlabel='스텝 크기 h',ylabel='미분값의 절대오차 · 표시 하한 1e−16',title='8장  차분 간격을 계속 줄이면 정확해질까')
    ax.grid(alpha=.22,which='both');ax.legend()
    # English fallback when the optional local Korean font is absent.
    translations = {'전진차분': 'Forward difference', '중앙차분': 'Central difference', '복소 스텝': 'Complex step', '스텝 크기 h': 'Step size h', '미분값의 절대오차 · 표시 하한 1e−16': 'Absolute derivative error · display floor 1e-16', '8장  차분 간격을 계속 줄이면 정확해질까': 'Chapter 8 · Does a smaller difference step improve accuracy?'}
    if not Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').exists():
        for artist in fig.findobj(matplotlib.text.Text):
            artist.set_text(translations.get(artist.get_text(), artist.get_text()))
    fig.savefig(args.output_dir/'chapter08.png',dpi=160);plt.close(fig)
    (args.output_dir/'chapter08.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(json.dumps(results,ensure_ascii=False))
if __name__=='__main__':main()
