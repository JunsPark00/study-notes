"""Made by Codex: original supplementary Chapter 1 experiment. Not textbook source code."""
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

L1,L2=1.,.7
def fk(q):
    a,b=q
    return np.array([L1*np.cos(a)+L2*np.cos(a+b), L1*np.sin(a)+L2*np.sin(a+b)])
q=np.array([.5,1.]); p=fk(q)
b=-q[1]; a=np.arctan2(p[1],p[0])-np.arctan2(L2*np.sin(b),L1+L2*np.cos(b))
check('two_configurations_same_position',np.linalg.norm(fk([a,b])-p),1e-12)
angles=rng.uniform(-np.pi,np.pi,(4000,2)); pts=np.array([fk(qi) for qi in angles]); radii=np.linalg.norm(pts,axis=1)
check('outer_radius_violation',max(0.,radii.max()-L1-L2),1e-12)
check('inner_radius_violation',max(0.,abs(L1-L2)-radii.min()),1e-12)
fig,ax=plt.subplots(); ax.scatter(*pts.T,s=2,alpha=.2); ax.scatter(*p,c='red')
ax.set(xlabel='x [m]',ylabel='y [m]',title='2R workspace and coincident end point'); ax.axis('equal'); save(fig,'workspace')
fig,ax=plt.subplots(); ax.hist(radii,bins=40); ax.axvline(abs(L1-L2),color='red'); ax.axvline(L1+L2,color='red')
ax.set(xlabel='Reach [m]',ylabel='Samples',title='Reach distribution, uniform joint samples'); save(fig,'reach')

assert CHECKS and all(v['passed'] for v in CHECKS.values())
report = {'checks':CHECKS, 'seed':42, 'python':sys.version,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['numpy','scipy','matplotlib','modern-robotics']}}
(FIG_DIR/'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')
print('PASS', len(CHECKS), 'numerical checks')
