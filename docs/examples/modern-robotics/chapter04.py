"""Made by Codex: original supplementary Chapter 4 experiment. Not textbook source code."""
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

L1,L2=1.,.6
S=np.array([[0,0,1,0,0,0],[0,0,1,0,-L1,0]]).T.astype(float)
M=np.eye(4); M[0,3]=L1+L2
qs=rng.uniform(-np.pi,np.pi,(200,2)); poe=[]; direct=[]
for a,b in qs:
    poe.append(mr.FKinSpace(M,S,[a,b])[:2,3]); direct.append([L1*np.cos(a)+L2*np.cos(a+b),L1*np.sin(a)+L2*np.sin(a+b)])
poe=np.array(poe); direct=np.array(direct)
check('poe_vs_trigonometry',np.max(np.linalg.norm(poe-direct,axis=1)),1e-10)
check('home_pose',np.linalg.norm(mr.FKinSpace(M,S,[0,0])-M),1e-12)
fig,ax=plt.subplots(); ax.scatter(*poe.T,s=9,label='PoE'); ax.axis('equal'); ax.legend()
ax.set(xlabel='x [m]',ylabel='y [m]',title='Independent FK comparison'); save(fig,'poe')
fig,ax=plt.subplots(); ax.plot(np.linalg.norm(poe-direct,axis=1)); ax.set(xlabel='Configuration',ylabel='Residual [m]',title='PoE versus analytic residual'); save(fig,'fk_residual')

assert CHECKS and all(v['passed'] for v in CHECKS.values())
report = {'checks':CHECKS, 'seed':42, 'python':sys.version,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['numpy','scipy','matplotlib','modern-robotics']}}
(FIG_DIR/'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='
')
print('PASS', len(CHECKS), 'numerical checks')
