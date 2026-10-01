"""Made by Codex: original supplementary Chapter 2 experiment. Not textbook source code."""
import argparse, json, sys, importlib.metadata
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
import modern_robotics as mr
from scipy.spatial.transform import Rotation
from scipy.integrate import solve_ivp
parser = argparse.ArgumentParser(description='Independent educational experiment; units m, s, rad.')
parser.add_argument('--output-dir', type=Path, default=Path('output'))
args = parser.parse_args()
FIG_DIR = args.output_dir.resolve()
FIG_DIR.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)
CHECKS = {}
plt.rcParams.update({'figure.figsize':(8,4.8),'font.size':11,'axes.grid':True,
                     'grid.alpha':.25,'figure.dpi':120})
def check(name, value, tolerance):
    value = float(value)
    passed = bool(np.isfinite(value) and value <= tolerance)
    CHECKS[name] = dict(value=value, tolerance=tolerance, passed=passed)
    assert passed, f'{name}: {value} > {tolerance}'
def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG_DIR / f'{name}.png', dpi=150, bbox_inches='tight')
    plt.close(fig)

def grubler(m,N,fi): return m*(N-1-len(fi))+sum(fi)
check('four_bar_dof',abs(grubler(3,4,[1]*4)-1),0)
def segment_distance(a,b,c):
    d=b-a; u=np.clip(np.dot(c-a,d)/np.dot(d,d),0,1) if np.dot(d,d)>0 else 0.
    return np.linalg.norm(a+u*d-c)
c=np.array([.7,.4]); radius=.18; grid=np.linspace(-np.pi,np.pi,75)
blocked=np.zeros((len(grid),len(grid)),dtype=bool)
for i,a in enumerate(grid):
    for j,b in enumerate(grid):
        elbow=np.array([np.cos(a),np.sin(a)]); end=elbow+.7*np.array([np.cos(a+b),np.sin(a+b)])
        blocked[i,j]=min(segment_distance(np.zeros(2),elbow,c),segment_distance(elbow,end,c))<=radius
check('periodic_seam',np.max(np.abs(blocked[0].astype(int)-blocked[-1].astype(int))),0)
check('segment_crossing',segment_distance(np.array([-1.,0]),np.array([1.,0]),np.zeros(2)),1e-12)
fig,ax=plt.subplots(); ax.imshow(blocked.T,origin='lower',extent=[-180,180,-180,180],aspect='auto')
ax.set(xlabel='q1 [deg]',ylabel='q2 [deg]',title='Forbidden configurations: both links checked'); save(fig,'cspace')
fig,ax=plt.subplots(); ax.bar(['serial 2R','four bar','spatial 6R'],[grubler(3,3,[1,1]),grubler(3,4,[1]*4),grubler(6,7,[1]*6)])
ax.set(ylabel='DOF',title='Independent constraints assumed'); save(fig,'mobility')

assert CHECKS and all(v['passed'] for v in CHECKS.values())
report = {'checks':CHECKS, 'seed':42, 'python':sys.version,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['numpy','scipy','matplotlib','modern-robotics']}}
(FIG_DIR/'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')
print('PASS', len(CHECKS), 'numerical checks')
