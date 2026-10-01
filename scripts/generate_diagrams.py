#!/usr/bin/env python3
"""Original concept figures computed from the Korean MPC chapter guides.
Run from this bundle: python scripts/generate_diagrams.py
Dependencies: numpy, scipy, matplotlib, pillow. No network or notebook data needed.
"""
import os
from pathlib import Path
import tempfile
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir())/'mpc-matplotlib'))
from pathlib import Path
import json, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon
from scipy.stats import norm
from PIL import Image, ImageOps, ImageDraw
ROOT=Path(__file__).resolve().parent.parent/'content'
OUT=ROOT.parent/'docs'/'assets'/'diagrams'
OUT.mkdir(parents=True, exist_ok=True)
FONT=os.environ.get('MPC_FONT_REGULAR','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
font_manager.fontManager.addfont(FONT)
plt.rcParams.update({'font.family':[font_manager.FontProperties(fname=FONT).get_name(), 'DejaVu Sans'],
 'font.size':12,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False,
 'axes.labelcolor':'#334155','xtick.color':'#475569','ytick.color':'#475569',
 'text.color':'#0f172a','axes.edgecolor':'#cbd5e1','mathtext.fontset':'dejavusans',
 'svg.fonttype':'path','figure.facecolor':'#f8fafc','axes.facecolor':'#f8fafc',
 'legend.frameon':False,'lines.linewidth':2.5})
BLUE='#2563eb'; TEAL='#0f766e'; ORANGE='#c65d13'; PURPLE='#7c3aed'; DARK='#0f172a'; GREY='#64748b'; LIGHT='#e2e8f0'
manifest=[]; checks={}; qa=[]

def figbase(ch,title,subtitle,foot, h=6.5):
    fig=plt.figure(figsize=(12,h), dpi=180)
    fig.text(.045,.95,f'MPC {ch:02d}  /  개념 시각화',fontsize=10.5,color=TEAL,weight='bold',va='top')
    fig.text(.045,.893,title,fontsize=23,weight='bold',va='top')
    fig.text(.045,.825,subtitle,fontsize=11.5,color=GREY,va='top')
    fig.text(.045,.048,foot,fontsize=10.2,color=GREY,va='bottom',linespacing=1.5)
    return fig

def axstd(fig,rect=[.09,.19,.86,.56]):
    ax=fig.add_axes(rect); ax.grid(True,color=LIGHT,alpha=.65); ax.set_axisbelow(True); return ax

def canvas(fig,rect=[.035,.15,.93,.62],xlim=(0,12),ylim=(0,5)):
    ax=fig.add_axes(rect); ax.set_xlim(*xlim);ax.set_ylim(*ylim);ax.axis('off');return ax

def box(ax,x,y,w,h,title,sub='',color=BLUE,fs=15):
    p=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.035,rounding_size=0.12',fc='white',ec=color,lw=1.8)
    ax.add_patch(p)
    ax.text(x+w/2,y+h*.64 if sub else y+h/2,title,ha='center',va='center',fontsize=fs,color=color,weight='bold')
    if sub: ax.text(x+w/2,y+h*.25,sub,ha='center',va='center',fontsize=10.5,color=GREY,linespacing=1.6)
    return p

def arrow(ax,start,end,color=GREY,style='-|>',lw=1.8,rad=0):
    ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle=style,color=color,lw=lw,connectionstyle=f'arc3,rad={rad}',shrinkA=3,shrinkB=3))

def save(fig,ch,slug,caption,interpretation,section,kind='computed',assumptions=''):
    stem=f'ch{ch:02d}_{slug}'
    if os.environ.get('MPC_DIAGRAM_ONLY') and stem != os.environ['MPC_DIAGRAM_ONLY']:
        plt.close(fig)
        return
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    clipped=[]
    # Matplotlib keeps tick objects beyond the visible range; do not count those.
    rendered_texts=list(fig.texts)
    for ax in fig.axes:
        rendered_texts += list(ax.texts) + [ax.title,ax.xaxis.label,ax.yaxis.label]
        legend=ax.get_legend()
        if legend: rendered_texts += list(legend.get_texts())
        for axis,lims in [(ax.xaxis,ax.get_xlim()),(ax.yaxis,ax.get_ylim())]:
            lo,hi=sorted(lims)
            for tick in axis.get_major_ticks()+axis.get_minor_ticks():
                if lo <= tick.get_loc() <= hi:
                    rendered_texts += [tick.label1,tick.label2]
    for artist in rendered_texts:
        if not artist.get_visible() or not artist.get_text(): continue
        bb=artist.get_window_extent(renderer)
        if bb.x0 < -1 or bb.y0 < -1 or bb.x1 > fig.bbox.width+1 or bb.y1 > fig.bbox.height+1:
            clipped.append(artist.get_text())
    qa.append({'figure':stem,'text_outside_canvas':clipped})
    fig.savefig(OUT/(stem+'.png'),dpi=180,facecolor=fig.get_facecolor())
    fig.savefig(OUT/(stem+'.svg'),facecolor=fig.get_facecolor())
    manifest.append({'chapter':ch, 'image':stem+'.png', 'svg':stem+'.svg', 'caption':caption, 'interpretation':interpretation, 'kind':kind, 'assumptions':assumptions})
    plt.close(fig)

# Chapter 1: loop and honest fixed-time discretization comparison
f=figbase(1,'MPC는 매 측정마다 계획을 새로 세웁니다','한 번의 제어 주기: 측정 → 추정 → 목표 → 계획 → 첫 입력 → 공정','도식의 화살표는 정보·제어의 흐름입니다. 예측 길이 N은 실제 운전 전체 시간이 아닙니다.')
a=canvas(f)
xs=[.5,4.5,8.5]; w=3.; h=1.15
box(a,xs[0],3.55,w,h,'측정',r'현재 센서 값 $y_k$',BLUE)
box(a,xs[1],3.55,w,h,'상태 추정',r'현재 상태 $\hat{x}_k$',BLUE)
box(a,xs[2],3.55,w,h,'정상 목표',r'가능한 $(x_s,u_s)$',PURPLE)
box(a,xs[2],.45,w,h,'미래 최적화',r'$N$단계 입력 계획 $U_k$',PURPLE)
box(a,xs[1],.45,w,h,'첫 입력만 적용',r'$u_{0|k}$만 지금 사용',ORANGE)
box(a,xs[0],.45,w,h,'실제 공정',r'외란·모델 오차가 존재',TEAL)
for s,e in [((3.5,4.12),(4.5,4.12)),((7.5,4.12),(8.5,4.12)),((10,3.55),(10,1.60)),((8.5,1.02),(7.5,1.02)),((4.5,1.02),(3.5,1.02)),((2,1.60),(2,3.55))]: arrow(a,s,e)
a.text(6,2.63,'다음 측정에서 초기상태를 갱신',ha='center',fontsize=16,weight='bold')
a.text(6,2.15,'계획 전체를 그대로 실행하지 않고 다시 최적화',ha='center',fontsize=12,color=GREY)
save(f,1,'receding_loop','MPC 한 주기의 정보·제어 흐름','미래 입력 여러 개를 계산하지만 첫 입력만 적용합니다. 다음 측정이 들어오면 추정 상태와 목표를 갱신해 다시 풉니다.','## 2 MPC의 한 번의 순환','schematic')

f=figbase(1,'같은 4초를 비교해야 이산화 오차가 보입니다','정지에서 일정 가속도 u=1 m/s² · 정확한 영차 유지 모델과 전진 Euler','직접 계산한 보충 예제입니다. Δ를 줄일 때 총 시간 T=4 s를 유지하도록 단계 수를 늘렸습니다.')
a=axstd(f,[.08,.20,.43,.55]); b=axstd(f,[.62,.20,.32,.55])
t=np.linspace(0,4,301);a.plot(t,.5*t*t,color=DARK,label='정확해 / 정확한 ZOH')
for dt,col in [(.4,ORANGE),(.2,TEAL)]:
    n=round(4/dt);ts=np.arange(n+1)*dt;p=.5*dt*dt*np.arange(n+1)*(np.arange(n+1)-1)
    a.plot(ts,p,'o--',ms=4,color=col,label=f'Euler Δ={dt:g} s')
a.set(xlabel='시간 t [s]',ylabel='위치 p [m]',xlim=(0,4.1));a.legend(loc='upper left',fontsize=10)
a.annotate('8.0 m',xy=(4,8),xytext=(3.3,8.6),fontsize=11,color=DARK)
a.annotate('7.2 m',xy=(4,7.2),xytext=(3.1,6.15),arrowprops={'arrowstyle':'-','color':ORANGE},fontsize=11,color=ORANGE)
a.set_ylim(0,9)
dt=np.array([.05,.1,.2,.4,.8]);err=4*dt/2;b.plot(dt,err,'o-',color=ORANGE)
b.set(xlabel='샘플링 간격 Δ [s]',ylabel='4초 뒤 위치 오차 [m]',xlim=(0,.86),ylim=(0,1.8))
for d in [.2,.4]:b.annotate(f'Δ={d:g} → {2*d:g} m',(d,2*d),xytext=(d+.035,2*d-.04),fontsize=11)
b.text(.04,1.5,'Δ를 절반으로 줄이면\n이 예제의 오차도 절반',fontsize=12,color=ORANGE)
checks['ch01_discretization']={'T':4,'dt_0.4_exact_position':8,'dt_0.4_euler_position':7.2,'dt_0.2_euler_position':7.6}
save(f,1,'discretization','정확 모델과 Euler: 총 시간을 고정한 위치 오차 비교','Δ=0.4초에서는 Euler 종단 위치가 7.2 m, 정확값은 8 m입니다. Δ=0.2초·20단계에서는 오차가 0.4 m로 줄어듭니다.','### 손계산 예제 가속하는 물체')

# Chapter 2: predecessor sets, shift candidate
f=figbase(2,'종단 집합에서 거꾸로 넓어지는 실행 가능 집합','x⁺=1.1x+u · |x|≤4 · |u|≤1 · 종단 집합 Xf=[−0.5,0.5]','이 예제에서는 허용 종단 제어로 계획을 연장할 수 있어 X₀ ⊆ X₁ ⊆ ⋯가 성립합니다.')
a=axstd(f,[.11,.20,.76,.55]);rs=[.5]
for j in range(5):rs.append(min(4,(rs[-1]+1)/1.1))
for j,r in enumerate(rs):
    y=5-j;a.plot([-r,r],[y,y],lw=18,solid_capstyle='butt',color=plt.cm.Blues(.35+.11*j))
    a.text(r+.10,y,f'r={r:.4f}',va='center',fontsize=10,color=DARK)
a.axvline(-4,color=ORANGE,ls='--',lw=1.5);a.axvline(4,color=ORANGE,ls='--',lw=1.5)
a.set(yticks=np.arange(6),yticklabels=[f'X{j}  (N={j})' for j in reversed(range(6))],xlabel='현재 상태 x',xlim=(-4.5,5.0),ylim=(-.7,5.7));a.grid(axis='y',visible=False)
a.text(-4.25,5.48,'상태 한계',color=ORANGE,fontsize=10)
f.text(.51,.103,'한 단계 가능: x=1.3  |  한 단계 불가능: x=1.4',ha='center',fontsize=11,color=TEAL)
checks['ch02_feasible_radii']=rs
save(f,2,'feasible_sets','예측 길이에 따라 넓어지는 스칼라 실행 가능 집합','반경은 r₀=0.5, rₙ₊₁=min(4,(rₙ+1)/1.1)입니다. 한 단계 집합의 경계 1.3636이 x=1.3과 x=1.4를 구분합니다.','## 4 실행 가능 집합을 거꾸로 구하기')

f=figbase(2,'남은 계획을 이동하고, 종단 제어를 하나 붙입니다','N=4로 그린 이동 후보해: 다음 문제의 실행 가능성을 보이는 구성','성립 조건: 실제 다음 상태=예측 첫 상태, 종단 제어의 허용성·불변성·비용 감소. 외란이 있으면 재검사가 필요합니다.')
a=canvas(f)
a.text(.15,4.03,'시점 k',fontsize=14,weight='bold');a.text(.15,1.4,'시점 k+1',fontsize=14,weight='bold')
for j in range(4):
    box(a,1.55+j*2.35,3.4,2.0,1.15,fr'$u_{{{j}|k}}^*$', '지금 적용' if j==0 else '남은 계획',ORANGE if j==0 else BLUE)
    title=fr'$u_{{{j+1}|k}}^*$' if j<3 else r'$\kappa_f(x_{4|k}^*)$'
    box(a,1.55+j*2.35,.75,2.0,1.15,title,'한 칸 이동' if j<3 else '종단 영역에서 추가',BLUE if j<3 else PURPLE,fs=14)
    if j>0:arrow(a,(2.55+j*2.35,3.38),(2.55+(j-1)*2.35,1.93),BLUE)
arrow(a,(2.55,3.37),(2.55,2.55),ORANGE)
a.text(1.6,2.23,'실제 x⁺가\n새 출발점',fontsize=10.5,color=ORANGE)
a.text(10.0,2.56,'끝 상태를\nXf 안에 유지',ha='center',fontsize=11,color=PURPLE)
save(f,2,'shifted_candidate','이전 최적 입력을 이동해 다음 후보를 만드는 과정','처음 적용한 입력을 버리고 나머지를 옮긴 뒤 종단 정책을 붙입니다. 이 후보가 다음 문제에 허용되면 다음 최적 비용은 후보 비용보다 크지 않습니다.','## 5 안정성 증명의 중심 이동 후보해','schematic')

# Chapter 3: robust tightening and probabilistic horizon budgeting
f=figbase(3,'최적화 전에 오차가 차지할 여유를 비워 둡니다','x⁺=1.1x+u+w · |w|≤0.1 · K=−0.6 → 오차계 e⁺=0.5e+w','초기 오차가 |e₀|≤0.2여야 합니다. 도식은 스칼라 불변 오차와 제약 축소를 보여 주며 완성된 MPC 설계 전체는 아닙니다.')
for rect,lim,tight,res,title,variable,col in [([.105,.19,.385,.55],3,2.8,.2,'상태 제약','z',BLUE),([.64,.19,.30,.55],1,.88,.12,'입력 제약','v',TEAL)]:
    a=axstd(f,rect);a.set_ylim(-.4,2.4);a.set_xlim(-lim*1.15,lim*1.15);a.set_yticks([0,1,2]);a.set_yticklabels(['실제 범위','명목 허용','원래 허용']);a.grid(axis='y',visible=False)
    a.plot([-lim,lim],[2,2],lw=18,color=LIGHT,solid_capstyle='butt');a.plot([-tight,tight],[1,1],lw=18,color=col,solid_capstyle='butt')
    a.plot([tight-res,tight+res],[0,0],lw=18,color=ORANGE,alpha=.3,solid_capstyle='butt');a.scatter([tight],[0],s=55,color=col,zorder=5)
    a.axvline(lim,color=GREY,ls='--',lw=1.4);a.axvline(-lim,color=GREY,ls='--',lw=1.4)
    a.set_title(title,loc='left',fontsize=15,pad=12);a.set_xlabel('상태 값' if variable=='z' else '입력 값')
    a.text(0,1.32,f'|{variable}| ≤ {tight:g}',ha='center',fontsize=13,color=col)
    a.text(0,2.28,f'±{lim:g}',ha='center',fontsize=11,color=GREY)
    a.text(-lim*.97,.25,f'여유 ±{res:g}',fontsize=11,color=ORANGE)
    if variable=='z':a.text(-lim*.97,-.35,'z=2.8이면 x≤3',fontsize=10,color=GREY)
    else:a.text(-lim*.97,-.35,'v=0.88이면 u≤1',fontsize=10,color=GREY)
checks['ch03_tightening']={'error_radius':.2,'state_nominal_limit':2.8,'input_correction_radius':.12,'input_nominal_limit':.88}
save(f,3,'constraint_tightening','불변 오차 반경이 상태·입력의 명목 허용 범위를 줄이는 방식','상태 여유는 0.2, 입력 여유는 |K|×0.2=0.12입니다. 그래서 명목 한계는 각각 ±2.8, ±0.88이 됩니다. 경계의 명목 중심에서도 모든 허용 오차를 더할 공간을 남깁니다.','### 직접 계산하는 튜브 예제')

f=figbase(3,'한 시점 95%와 열 시점 전체 95%는 다릅니다','전체 위반 확률 ε=0.05를 10단계에 균등 배분하면 각 εⱼ=0.005','가우스 패널은 영평균·정확한 분산 가정입니다. 합집합 상계 Σ εⱼ≤ε에는 시점 사이의 독립성이 필요하지 않습니다.')
a=axstd(f,[.075,.21,.44,.53]);b=axstd(f,[.625,.21,.32,.53]);x=np.linspace(-4,4,1000);p=norm.pdf(x);q1=norm.ppf(.975);q10=norm.ppf(.9975)
a.plot(x,p,color=DARK);a.fill_between(x,p,where=np.abs(x)>=q1,color=ORANGE,alpha=.3,label='개별 5%: ±1.960σ 밖');a.fill_between(x,p,where=np.abs(x)>=q10,color=PURPLE,alpha=.6,label='개별 0.5%: ±2.807σ 밖')
for q,col in [(q1,ORANGE),(q10,PURPLE)]:a.axvline(q,color=col,ls='--',lw=1.6);a.axvline(-q,color=col,ls='--',lw=1.6)
a.set(xlabel='표준화 오차 e/σ',ylabel='확률 밀도',xlim=(-4,4),ylim=(0,.48));a.legend(loc='upper left',fontsize=9.5)
b.bar(np.arange(1,11),[.5]*10,color=PURPLE,width=.75);b.set(xlabel='예측 단계 j',ylabel='허용 위반 확률 [%]',xticks=np.arange(1,11),ylim=(0,.72));b.text(5.5,.61,'0.5% × 10 = 5%',ha='center',fontsize=14,color=PURPLE,weight='bold');b.text(5.5,.16,'각 단계의 위험을\n작게 배분',ha='center',color='white',fontsize=12)
checks['ch03_gaussian_quantiles']={'individual_5pct':float(q1),'individual_0.5pct':float(q10),'horizon_union_bound':.05}
save(f,3,'risk_allocation','개별 시점의 가우스 여유와 구간 위험 배분','전체 10단계에서 어느 한 번이라도 위반할 확률을 5% 이하로 제한하려면, 균등 배분 예에서는 각 단계가 0.5%를 맡습니다. 필요한 양측 가우스 여유는 1.960σ에서 2.807σ로 커집니다.','## 6 확률 제약에서 반드시 구분할 네 가지',assumptions='오차가 영평균 가우스이며 각 단계의 분산을 정확히 안다는 조건. 그림의 단계별 막대는 관측 위반 빈도가 아니라 설계 위험 배분.')

# Chapter 4: information times and scalar Gaussian update
f=figbase(4,'같은 상태 xₖ를 추정해도, 사용한 측정 시점이 다릅니다','예측·필터링·평활화를 같은 정보 조건의 추정기로 혼동하지 마세요','채워진 점은 사용한 측정, 빈 점은 사용하지 않은 측정입니다. 미래 측정은 현재의 실시간 제어에 쓸 수 없습니다.')
a=canvas(f,xlim=(-.4,8.5),ylim=(-.5,4.9));pos=np.arange(7)+1
rows=[(3.7,'예측',3,BLUE),(2.25,'필터링',4,TEAL),(.8,'평활화',6,PURPLE)]
for y,name,last,col in rows:
    a.plot([1,7],[y,y],color=LIGHT,lw=2)
    for j,p in enumerate(pos):a.scatter(p,y,s=115,facecolors=col if j<=last else '#f8fafc',edgecolors=col if j<=last else '#cbd5e1',lw=1.6,zorder=3)
    a.text(-.1,y,name,va='center',fontsize=14,color=col,weight='bold')
    a.text(7.3,y,f'y₀…y{last}',va='center',fontsize=11,color=col)
for j,p in enumerate(pos):a.text(p,4.38,f'y{j}',ha='center',fontsize=12,color=GREY)
a.axvline(5,ymin=.1,ymax=.91,color=ORANGE,ls='--',lw=1.5)
a.text(5,4.82,'추정할 상태 x₄',ha='center',fontsize=13,color=ORANGE)
a.text(3,3.08,'현재 측정 y₄가 도착하기 전',ha='center',fontsize=10.5,color=BLUE)
a.text(3,1.63,'현재 측정 y₄까지 반영',ha='center',fontsize=10.5,color=TEAL)
a.text(4.6,.12,'이후 y₅, y₆로 과거 x₄를 다시 추정',ha='center',fontsize=10.5,color=PURPLE)
save(f,4,'information_timeline','예측·필터링·평활화가 사용하는 정보의 시간 경계','세 행은 모두 x₄를 대상으로 하지만 예측은 y₃까지, 필터링은 y₄까지, 평활화는 예시의 미래 y₆까지 사용합니다. 같은 시점의 추정 오차를 비교해도 정보 조건은 다릅니다.','## 1 같은 상태라도 사용할 수 있는 정보가 다릅니다','schematic')

f=figbase(4,'사전과 측정을 결합하면 평균과 불확실성이 함께 바뀝니다','스칼라 예제: 사전 N(0,1), 측정 y=1, 측정 분산 R=0.25','선형·가우스 및 독립 잡음 가정의 정확한 계산입니다. 측정 곡선은 x에 대한 정규화 우도이며 별도 사후가 아닙니다.')
a=axstd(f,[.07,.21,.46,.53]);b=axstd(f,[.63,.21,.30,.53]);x=np.linspace(-3,3,800)
for mu,var,col,lab in [(0,1,BLUE,'사전: 평균 0, 분산 1'),(1,.25,ORANGE,'측정 우도: 중심 1'),(.8,.2,TEAL,'사후: 평균 0.8, 분산 0.2')]:a.plot(x,norm.pdf(x,mu,np.sqrt(var)),color=col,label=lab)
a.set(xlabel='현재 상태 x',ylabel='밀도 / 정규화 우도',xlim=(-2.7,2.7),ylim=(0,1.03));a.legend(loc='upper left',fontsize=9.3)
for y,mu,var,col,label in [(2,0,1,BLUE,'사전'),(1,.8,.2,TEAL,'필터링'),(0,.8,.24,PURPLE,'다음 예측')]:
    half=norm.ppf(.975)*np.sqrt(var);b.plot([mu-half,mu+half],[y,y],color=col,lw=6);b.scatter(mu,y,s=65,color=col);b.text(mu,y+.20,f'분산 {var:g}',ha='center',color=col,fontsize=10.5)
b.set(yticks=[0,1,2],yticklabels=['다음 예측','필터링','사전'],xlabel='각 시점의 조건부 95% 구간',ylim=(-.55,2.6),xlim=(-2.2,2.15));b.grid(axis='y',visible=False)
b.text(-2.0,-.43,'다음 예측은 Qw=0.04만큼 다시 넓어짐',fontsize=8.9,color=GREY)
checks['ch04_kalman']={'innovation_variance':1.25,'gain':.8,'posterior_mean':.8,'posterior_variance':.2,'next_prior_variance':.24}
save(f,4,'kalman_update','측정 한 번이 평균을 이동시키고 분산을 줄이는 과정','칼만 이득 0.8은 사전 평균 0을 측정값 1 쪽으로 옮겨 사후 평균 0.8을 만듭니다. 분산은 1→0.2로 줄지만 다음 예측에서는 과정 잡음 때문에 0.24가 됩니다.','### 손으로 푸는 한 단계 예제')

# Chapter 5: two errors and target feasibility
seps=.041/.6; se=.7*(seps+.03)/.4; sx=se+seps
f=figbase(5,'실제 상태에는 추종 오차와 추정 오차가 모두 더해집니다','세 상태의 관계: 명목 z → 추정 x̂ → 실제 x · x=z+e+ε','보충 스냅샷: z=0, e=0.15, ε=0.06. 개별 불변 반경 안의 예시이며 MPC 최적화 궤적을 그린 것은 아닙니다.')
a=axstd(f,[.13,.23,.76,.49]);a.set_xlim(-.29,.30);a.set_ylim(-.5,3.35)
for y,lo,hi,col in [(0,-sx,sx,GREY),(1,-se,se,BLUE),(2,.15-seps,.15+seps,TEAL)]:
    a.plot([lo,hi],[y,y],color=col,lw=19,alpha=.30,solid_capstyle='butt');a.plot([lo,hi],[y,y],'|',ms=18,color=col)
a.set(yticks=[0,1,2],yticklabels=['전체 여유','추종 여유','추정 여유'],xlabel='z=0을 기준으로 한 상태 값');a.grid(axis='y',visible=False)
for val,lab,col in [(0,'z=0',DARK),(.15,'x̂=0.15',BLUE),(.21,'x=0.21',TEAL)]:
    a.scatter(val,2.88,s=80,color=col,zorder=5);a.text(val,3.13,lab,ha='center',fontsize=11.5,color=col);a.axvline(val,0,.85,color=col,ls=':',lw=1)
arrow(a,(0,2.58),(.15,2.58),BLUE,style='<->');a.text(.075,2.28,'e=0.15',ha='center',color=BLUE,fontsize=11)
arrow(a,(.15,2.58),(.21,2.58),TEAL,style='<->');a.text(.215,2.31,'ε=0.06',ha='left',color=TEAL,fontsize=11)
a.text(-.285,.27,f'전체 반경 {sx:.6f}',color=GREY,fontsize=10.5)
a.text(-.285,1.27,f'추종 반경 {se:.6f}',color=BLUE,fontsize=10.5)
a.text(-.285,2.02,f'추정 반경 {seps:.6f}',color=TEAL,fontsize=10.5)
checks['ch05_error_radii']={'estimation':seps,'tracking':se,'combined_sum':sx,'nominal_state_limit':2-sx,'nominal_input_limit':.8-se}
save(f,5,'two_errors','두 오차를 구분해야 실제 상태의 여유가 보입니다','추정 오차 반경 0.068333과 추종 오차 반경 0.172083을 더하면 실제 상태의 보수적 반경은 0.240417입니다. 입력에는 Ke만 들어가므로 입력 여유에는 추종 반경만 사용합니다.','## 3. 손으로 계산하는 강인 여유','computed schematic',assumptions='임의의 허용 스냅샷이며 시간 시뮬레이션 아님. 개별 구간의 민코프스키 합 경계이며 더 작은 결합 불변 집합 경계와 구분.')

f=figbase(5,'외란을 알더라도 요청한 정상 목표가 가능해야 합니다','x⁺=0.8x+0.5u+d · xₛ=r · |uₛ|≤0.8 · |r|≤2','정적 정상 목표의 가능성만 표시합니다. 과도 상태의 제약 만족이나 재귀적 실행 가능성 보장은 별도로 필요합니다.')
a=axstd(f,[.075,.21,.48,.54]);b=axstd(f,[.665,.21,.27,.54]);r=np.linspace(-2,2,300)
a.fill_between(r,.2*r-.4,.2*r+.4,color=TEAL,alpha=.16,label='가능한 정상 목표');a.plot(r,.2*r-.4,color=TEAL,lw=1.5);a.plot(r,.2*r+.4,color=TEAL,lw=1.5)
a.set(xlabel='요청·조정 목표 r',ylabel='추정 상수 외란 d̂',xlim=(-2.2,2.6),ylim=(-1,1.1));a.axvline(2,color=GREY,ls='--',lw=1);a.axvline(-2,color=GREY,ls='--',lw=1)
for rr,dd,col in [(1,.12,BLUE),(1,.8,ORANGE),(2,.8,TEAL)]:a.scatter(rr,dd,s=70,color=col,zorder=5)
a.annotate('r=1, d̂=0.12\nuₛ=0.16',(1,.12),xytext=(-.4,-.35),arrowprops={'arrowstyle':'-','color':BLUE},fontsize=11,color=BLUE)
a.annotate('요청: uₛ=−1.2\n입력 한계 위반',(1,.8),xytext=(-1.45,.87),arrowprops={'arrowstyle':'-','color':ORANGE},fontsize=10.5,color=ORANGE)
a.annotate('조정: r=2\nuₛ=−0.8',(2,.8),xytext=(1.40,.36),arrowprops={'arrowstyle':'-','color':TEAL},fontsize=10.5,color=TEAL)
arrow(a,(1.02,.8),(1.97,.8),ORANGE);a.legend(loc='lower left',fontsize=10)
b.bar([0],[.8],color=GREY,label='0.8xₛ = 0.80');b.bar([0],[.08],bottom=.8,color=BLUE,label='0.5uₛ = 0.08');b.bar([0],[.12],bottom=.88,color=ORANGE,label='d = 0.12')
b.axhline(1,color=DARK,ls='--',lw=1.2);b.set(xticks=[0],xticklabels=['r=1, d=0.12'],ylim=(0,1.15),ylabel='평형식의 기여');b.text(0,.40,'0.8xₛ = 0.80',ha='center',color='white',fontsize=12);b.text(0,.84,'0.5uₛ = 0.08',ha='center',color='white',fontsize=10);b.text(0,.94,'d = 0.12',ha='center',color='white',fontsize=10.5);b.text(0,1.065,'합계 1.00 = xₛ',ha='center',fontsize=12,weight='bold');b.grid(axis='x',visible=False)
checks['ch05_targets']={'r1_d012_us':.16,'r1_d08_us':-1.2,'r2_d08_us':-.8}
save(f,5,'target_feasibility','외란 추정값에 따라 달라지는 정상 목표의 가능 영역','초록 띠는 |0.2r−d̂|≤0.4와 |r|≤2를 만족하는 목표입니다. d̂=0.8에서 r=1은 불가능하지만 r=2, uₛ=−0.8은 경계에서 가능합니다. 오른쪽은 d=0.12일 때 유지 입력 0.16이 평형식을 맞추는 계산입니다.','### 두 번째 수치 예: 왜 유지 입력이 달라지는가')

# Chapter 6: cooperative vs raw iteration and coupled resources
f=figbase(6,'같은 볼록 비용도 동시 갱신 방식에 따라 발산합니다','3인 예제: H의 대각=1, 비대각=0.8 · 전체 후보 평균은 T=I−H/3','가로축 p는 물리 시간이 아니라 같은 최적화 문제 안의 반복입니다. 반복 수렴만으로 폐루프 안정성은 결론낼 수 없습니다.')
a=axstd(f,[.10,.22,.81,.53]);H=np.full((3,3),.8);np.fill_diagonal(H,1);Tr=np.eye(3)-H;Ta=np.eye(3)-H/3
p=np.arange(9)
for T,u,col,lab in [(Tr,np.ones(3),ORANGE,'새 블록 단순 결합 · 초기 (1,1,1)'),(Ta,np.ones(3),TEAL,'전체 후보 평균 · 초기 (1,1,1)'),(Ta,np.array([1.,-1.,0.]),PURPLE,'전체 후보 평균 · 초기 (1,−1,0)')]:
    us=[u.copy()]
    for i in range(8):us.append(T@us[-1])
    norms=np.linalg.norm(us,axis=1)/np.linalg.norm(u);a.semilogy(p,norms,'o-',color=col,ms=5,label=lab)
a.axhline(1,color=GREY,ls='--',lw=1.2);a.set(xlabel='최적화 반복 p',ylabel='초기값으로 정규화한 ‖uᵖ‖',xticks=p,xlim=(-.2,8.2),ylim=(5e-8,100));a.legend(loc='lower left',fontsize=10.5)
a.text(4.7,20,'단순 결합: ρ=1.6',color=ORANGE,fontsize=12)
a.text(4.2,.002,'후보 평균: 전체 ρ≈0.9333\n초기 방향에 따라 감소 속도가 다름',color=TEAL,fontsize=11)
checks['ch06_iterations']={'raw_spectral_radius':float(max(abs(np.linalg.eigvals(Tr)))),'averaged_spectral_radius':float(max(abs(np.linalg.eigvals(Ta)))),'raw_first_cost':float(.5*(Tr@np.ones(3))@H@(Tr@np.ones(3))),'averaged_first_cost':float(.5*(Ta@np.ones(3))@H@(Ta@np.ones(3)))}
save(f,6,'cooperative_iteration','단순 동시 결합과 전체 후보 평균의 서로 다른 수렴','단순 결합은 초기 (1,1,1)에서 크기가 1.6배씩 커집니다. 후보 평균은 수렴하지만 (1,1,1)은 빠른 모드, (1,−1,0)은 느린 모드이므로 감소 속도가 다릅니다.','### 손으로 계산하는 세 참여자 예')

f=figbase(6,'각자 움직일 수 없어도, 함께 움직이면 비용이 줄어듭니다','공유 자원 u₁+u₂≤1 · u₁,u₂≥0 · J=(u₁−1)²+(u₂−2)²','공유 제약에서는 실행 가능성 유지와 전역 최적해 수렴이 다른 문제입니다. 블록별 정체가 전체 최적성을 뜻하지 않습니다.')
a=axstd(f,[.075,.21,.42,.54]);b=axstd(f,[.615,.21,.32,.54]);v=np.linspace(-.12,1.2,240);xx,yy=np.meshgrid(v,v);jj=(xx-1)**2+(yy-2)**2
a.contour(xx,yy,jj,levels=[2,2.5,3.28,4,5],colors=GREY,alpha=.45,linewidths=1)
a.add_patch(Polygon([(0,0),(1,0),(0,1)],facecolor=TEAL,alpha=.12,edgecolor=TEAL,lw=2))
a.plot([0,1],[1,0],color=TEAL,lw=2);a.scatter(.8,.2,color=ORANGE,s=70,zorder=5);a.scatter(0,1,color=TEAL,s=70,zorder=5)
arrow(a,(.77,.23),(.03,.97),BLUE,lw=2.5)
a.annotate('블록별 정체\n(0.8,0.2), J=3.28',(.8,.2),xytext=(.55,.63),arrowprops={'arrowstyle':'-','color':ORANGE},fontsize=10.5,color=ORANGE)
a.annotate('전체 최적\n(0,1), J=2',(0,1),xytext=(.17,1.02),fontsize=10.5,color=TEAL)
a.text(.22,.18,'실행 가능',color=TEAL,fontsize=12);a.set(xlabel='u₁',ylabel='u₂',xlim=(-.12,1.2),ylim=(-.12,1.2),aspect='equal')
t=np.linspace(0,.8,200);cost=3.28-3.2*t+2*t*t;b.plot(t,cost,color=BLUE);b.scatter([0,.8],[3.28,2],color=[ORANGE,TEAL],s=60)
b.set(xlabel='공동 이동량 t',ylabel='J((0.8,0.2)+t(−1,+1))',xlim=(-.03,.83),ylim=(1.8,3.55));b.text(.05,3.40,'u₁을 줄인 만큼 u₂를 늘림',fontsize=11,color=BLUE)
checks['ch06_resource']={'start_cost':3.28,'joint_optimal_cost':2.0,'path_parameter_end':.8}
save(f,6,'shared_resource','공유 자원 경계를 따라 움직이는 공동 개선 방향','(0.8,0.2)에서는 상대 입력을 고정한 각 참가자가 개선하지 못합니다. 두 입력을 (−1,+1) 방향으로 함께 바꾸면 실행 가능성을 유지하면서 (0,1)까지 비용을 낮출 수 있습니다.','## 5. 독립 입력 제약과 공유 자원: §6.3–6.4')

# Chapter 7: exact scalar PWA law and branching validity conditions
f=figbase(7,'영역이 바뀌면 입력의 기울기가 바뀝니다','J(u,x)=x²+xu+½u² · −1≤u≤1 · 상태 x가 최적화 문제의 파라미터','이 스칼라 예제에서는 포화가 정확한 해입니다. 여러 입력이 결합된 일반 MPC에서 성분별 clipping이 최적이라는 뜻은 아닙니다.')
a=axstd(f,[.08,.21,.40,.54]);b=axstd(f,[.60,.21,.34,.54]);x=np.linspace(-2.5,2.5,1001);u=np.clip(-x,-1,1);val=x*x+x*u+.5*u*u
for ax in [a,b]:
    for lo,hi,col in [(-2.5,-1,ORANGE),(-1,1,BLUE),(1,2.5,TEAL)]:ax.axvspan(lo,hi,color=col,alpha=.085)
    for z in [-1,1]:ax.axvline(z,color=GREY,ls='--',lw=1.2)
a.plot(x,u,color=DARK);a.set(xlabel='현재 상태 x',ylabel='첫 입력 u*(x)',xlim=(-2.5,2.5),ylim=(-1.45,1.55));a.text(-2.0,1.25,'u*=1',ha='center',color=ORANGE);a.text(0,1.25,'u*=−x',ha='center',color=BLUE);a.text(1.8,1.25,'u*=−1',ha='center',color=TEAL)
b.plot(x,val,color=DARK);b.set(xlabel='현재 상태 x',ylabel='최적 비용 V(x)',xlim=(-2.5,2.5),ylim=(-.15,4.7))
for q in [.4,1.6]:
    uq=np.clip(-q,-1,1);vq=q*q+q*uq+.5*uq*uq;a.scatter(q,uq,s=50,color=PURPLE,zorder=5);b.scatter(q,vq,s=50,color=PURPLE,zorder=5)
b.annotate('(0.4, 0.08)',(.4,.08),xytext=(-1.55,.75),arrowprops={'arrowstyle':'-','color':PURPLE},fontsize=10,color=PURPLE)
b.annotate('(1.6, 1.46)',(1.6,1.46),xytext=(.10,2.10),arrowprops={'arrowstyle':'-','color':PURPLE},fontsize=10,color=PURPLE)
checks['ch07_scalar']={'u_at_04':-.4,'V_at_04':.08,'u_at_16':-1,'V_at_16':1.46,'boundaries':[-1,1]}
save(f,7,'explicit_scalar','구간별 아핀 입력과 구간별 이차 최적 비용','경계 x=±1에서 입력과 비용은 이어지지만 입력 기울기는 바뀝니다. 가운데는 u=−x, 양쪽은 입력 한계에서 포화됩니다.','## 4. 손으로 풀어 보는 세 영역 예제')

f=figbase(7,'활성 집합의 해는 조건을 통과한 상태에서만 쓸 수 있습니다','같은 스칼라 QP의 세 후보 → 실행 가능성과 승수 부호 검사 → 임계 영역','경계 x=±1에서는 인접 식이 같은 입력을 줍니다. 일반 문제에서는 빈 영역·퇴화·경계 허용오차를 별도로 처리합니다.')
a=canvas(f,xlim=(0,12),ylim=(0,5.3))
for x0,title,law,condition,region,col in [(.4,'상한 활성',r'$u=1$',r'$\lambda=-x-1\geq0$',r'$x\leq-1$',ORANGE),(4.4,'활성 제약 없음',r'$u=-x$',r'$-1\leq u\leq1$',r'$-1\leq x\leq1$',BLUE),(8.4,'하한 활성',r'$u=-1$',r'$\lambda=x-1\geq0$',r'$x\geq1$',TEAL)]:
    box(a,x0,3.62,3.2,1.12,title,law,col,fs=15)
    arrow(a,(x0+1.6,3.6),(x0+1.6,2.96),col)
    a.text(x0+1.6,2.7,condition,ha='center',fontsize=15,color=col)
    arrow(a,(x0+1.6,2.43),(x0+1.6,1.86),col)
    box(a,x0,1.02,3.2,.80,region,color=col,fs=17)
a.text(6,.32,'온라인: x=0.4 → 가운데 영역 선택 → u*=−0.4',ha='center',fontsize=14,weight='bold',color=BLUE)
save(f,7,'active_set_regions','후보 아핀 식을 유효한 임계 영역으로 제한하는 과정','활성 제약을 고정해 얻은 입력 식이 모든 상태에서 유효하지는 않습니다. 원래 부등식과 활성 승수의 비음수 조건을 함께 확인해야 실제 영역이 됩니다.','## 3. 활성 집합에서 임계 영역까지','schematic')

# Chapter 8: stiffness, shooting defects, independent Taylor check
f=figbase(8,'안정한 연속 모델도 나쁜 시간 간격에서는 수치적으로 발산합니다','ẋ=−100x · x(0)=1 · 명시적 Euler의 배율은 1−100h','음함수 Euler는 이 예제에서 모든 양의 h에 안정하지만, 큰 h의 정확도까지 보장하지는 않습니다.')
a=axstd(f,[.09,.21,.40,.54]);b=axstd(f,[.61,.21,.33,.54]);h=np.linspace(0,.04,401)
a.axhspan(-1,1,color=TEAL,alpha=.08);a.plot(h,np.exp(-100*h),color=DARK,label='정확한 배율');a.plot(h,1-100*h,color=ORANGE,label='명시적 Euler');a.plot(h,1/(1+100*h),color=BLUE,label='음함수 Euler');a.axhline(-1,color=GREY,ls='--',lw=1);a.axhline(1,color=GREY,ls='--',lw=1);a.axvline(.02,color=GREY,ls=':',lw=1);a.scatter([.03],[-2],color=ORANGE,s=60);a.annotate('h=0.03 → −2',(.03,-2),xytext=(.016,-2.7),fontsize=11,color=ORANGE)
a.set(xlabel='시간 간격 h [s]',ylabel='한 단계 증폭 배율',xlim=(0,.04),ylim=(-3.2,1.55));a.legend(loc='upper right',fontsize=9.5)
k=np.arange(9);t=.03*k
for vals,col,lab in [(np.exp(-100*t),DARK,'정확해'),(2.**k,ORANGE,'명시적 Euler |x|'),(.25**k,BLUE,'음함수 Euler')]:b.semilogy(t,vals,'o-',color=col,ms=4,label=lab)
b.set(xlabel='시간 t [s]  (h=0.03 s)',ylabel='상태의 절댓값 |x|',xlim=(-.007,.245),ylim=(1e-11,1e3));b.legend(loc='lower left',fontsize=9.5)
checks['ch08_stiffness']={'h':.03,'explicit_factor':-2,'implicit_factor':.25,'exact_factor':float(np.exp(-3))}
save(f,8,'stiff_integration','적분법의 안정 영역과 강직 모델의 수치 응답','명시적 Euler는 0<h<0.02에서만 이 모델의 절댓값을 줄입니다. h=0.03에서는 부호가 뒤집히며 크기가 두 배씩 커지고, 정확해는 빠르게 감쇠합니다.','## 2. 시간 이산화: 적분 정확도만 보면 충분할까?')

f=figbase(8,'다중 사격의 중간 반복에서는 구간 사이가 아직 끊길 수 있습니다','ẋ=−x+0.2x³+u · T=2 · 구조를 보이기 위한 N=4 보충 도식','입력과 다중 사격 노드 값은 설명용으로 지정했습니다. 최적해가 아닌 중간 반복의 구조이며, 최적화 수렴 시 연결 결함이 작아져야 합니다.')
a=axstd(f,[.10,.50,.82,.24]);b=axstd(f,[.10,.18,.82,.24]);U=[-.5,-.3,-.1,0];starts=[.8,.64,.38,.25];dt=.5

def rk4(x,u,h):
    fun=lambda x:-x+.2*x*x*x+u
    k1=fun(x);k2=fun(x+h*k1/2);k3=fun(x+h*k2/2);k4=fun(x+h*k3)
    return x+h*(k1+2*k2+2*k3+k4)/6
xcur=.8;defects=[]
for j,u in enumerate(U):
    ts=np.linspace(j*dt,(j+1)*dt,41);one=[xcur];multi=[starts[j]]
    for i in range(40):one.append(rk4(one[-1],u,dt/40));multi.append(rk4(multi[-1],u,dt/40))
    a.plot(ts,one,color=BLUE);a.scatter(ts[0],one[0],color=BLUE,s=30);xcur=one[-1]
    b.plot(ts,multi,color=TEAL);b.scatter(ts[0],multi[0],color=TEAL,s=35,zorder=5)
    if j<3:
        b.plot([ts[-1],ts[-1]],[multi[-1],starts[j+1]],color=ORANGE,ls='--',lw=2)
        defects.append(starts[j+1]-multi[-1]);b.text(ts[-1]+.025,(multi[-1]+starts[j+1])/2,'연결 결함',color=ORANGE,fontsize=9)
    a.axvline(j*dt,color=LIGHT,ls=':',lw=1);b.axvline(j*dt,color=LIGHT,ls=':',lw=1)
a.set(ylabel='단일 사격 x(t)',xlim=(-.04,2.04),ylim=(-.05,.90),xticks=np.arange(0,2.01,.5));a.tick_params(labelbottom=False)
b.set(ylabel='다중 사격 x(t)',xlabel='시간 t [s]',xlim=(-.04,2.04),ylim=(-.05,.9),xticks=np.arange(0,2.01,.5))
a.text(1.02,.75,'U를 정하면 상태는 연속해서 전파',fontsize=11,color=BLUE)
b.text(1.05,.76,'노드 상태도 독립 변수',fontsize=11,color=TEAL)
checks['ch08_shooting']={'illustrative_inputs':U,'multiple_shooting_node_initial_guesses':starts,'continuity_defects':defects,'not_optimized':True}
save(f,8,'shooting_structure','단일 사격의 연속 전파와 다중 사격의 연결 결함','같은 입력을 쓰더라도 다중 사격의 노드 초기 추정값을 별도 변수로 두면 중간 반복에서 구간이 끊길 수 있습니다. 연결 등식이 이러한 결함을 줄입니다.','## 4. 직접 최적 제어의 세 가지 매개화','computed schematic',assumptions='장에 제시된 연속 모델을 사용하되 설명용 N=4, U와 노드 초기값을 직접 지정. 최적 제어 계산 결과 아님.')

f=figbase(8,'올바른 기울기를 빼면 Taylor 나머지의 차수가 달라집니다','손계산 비용 J(u)=0.405+0.09u+0.01u² · 검사점 u=0 · 방향 d=1','이 장의 한 구간 이차 비용에 적용한 별도 검증입니다. h가 너무 작으면 부동소수점 상쇄가 차수 관찰을 방해합니다.')
a=axstd(f,[.10,.21,.81,.54]);hh=np.logspace(-5,-1,41);J=lambda u:.405+.09*u+.01*u*u;r0=np.abs(J(hh)-J(0));r1=np.abs(J(hh)-J(0)-.09*hh);rb=np.abs(J(hh)-J(0)-.08*hh)
a.loglog(hh,r0,color=GREY,label='보정 전: |J(h)−J(0)|');a.loglog(hh,r1,'o-',color=TEAL,ms=3,markevery=5,label='정확한 기울기 0.09로 보정');a.loglog(hh,rb,'--',color=ORANGE,label='틀린 기울기 0.08로 보정')
a.set(xlabel='검사 간격 h',ylabel='Taylor 나머지 절댓값',xlim=(8e-6,.13),ylim=(5e-13,.03));a.legend(loc='upper left',fontsize=10.5)
a.text(.007,.000045,'틀린 보정: 약 O(h)',color=ORANGE,fontsize=12,rotation=18)
a.text(.003,.0000003,'올바른 보정: 약 O(h²)',color=TEAL,fontsize=12,rotation=25)
sl1=float(np.polyfit(np.log(hh[hh>=1e-4]),np.log(r1[hh>=1e-4]),1)[0]);slb=float(np.polyfit(np.log(hh[hh>=1e-4]),np.log(rb[hh>=1e-4]),1)[0])
checks['ch08_taylor']={'test_point':0,'true_gradient':.09,'intentionally_wrong_gradient':.08,'fitted_correct_order':sl1,'fitted_wrong_order':slb}
save(f,8,'taylor_check','기울기 구현의 정확성을 Taylor 나머지 차수로 검사하기','정확한 기울기 0.09를 빼면 나머지는 0.01h²입니다. 일부러 틀린 0.08을 빼면 0.01h+0.01h²가 남아 주로 1차로 줄어듭니다. 최적화 성공 표시와 독립적인 도함수 검사를 구분합니다.','## 8. 독립적인 도함수·해 검증',assumptions='본문의 손계산 이차 비용을 사용한 보충 테스트이며 비선형 최적제어 문제 전체의 도함수 검증은 아님.')

assert np.isclose(rs[1],15/11)
assert np.isclose(seps,.06833333333333333) and np.isclose(sx,.24041666666666667)
assert np.isclose(checks['ch06_iterations']['raw_first_cost'],9.984)
assert np.isclose(checks['ch06_iterations']['averaged_first_cost'],.06933333333333333)
assert abs(sl1-2)<.001 and abs(slb-1)<.02
assert not any(item['text_outside_canvas'] for item in qa), 'Visible text outside image canvas'
print(json.dumps({'figures':len(manifest),'checks':checks},ensure_ascii=False,indent=2))
