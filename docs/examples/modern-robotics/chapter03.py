"""Made by Codex: original supplementary Chapter 3 experiment. Not textbook source code."""
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

R=Rotation.from_rotvec([0,0,np.pi/3]).as_matrix()
check('rotation_orthogonality',np.linalg.norm(R.T@R-np.eye(3)),1e-12)
check('proper_rotation',abs(np.linalg.det(R)-1),1e-12)
A=np.eye(4); A[:3,:3]=R
B=np.eye(4); B[:3,3]=[1,.2,0]
p=np.array([.2,.4,.1,1]); ab=A@B@p; ba=B@A@p
inv=np.eye(4); inv[:3,:3]=R.T; inv[:3,3]=-R.T@A[:3,3]
check('inverse_roundtrip',np.linalg.norm(inv@A@p-p),1e-12)
fig,ax=plt.subplots(); ax.scatter([p[0],ab[0],ba[0]],[p[1],ab[1],ba[1]])
for xy,label in [(p,'p'),(ab,'A B p'),(ba,'B A p')]: ax.annotate(label,xy[:2])
ax.axis('equal'); ax.set(xlabel='x [m]',ylabel='y [m]',title='Rotation/translation order'); save(fig,'composition')
angle=np.linspace(0,np.pi,100); diff=[]
for v in angle:
    A[:3,:3]=Rotation.from_rotvec([0,0,v]).as_matrix(); diff.append(np.linalg.norm((A@B@p-B@A@p)[:3]))
fig,ax=plt.subplots(); ax.plot(angle,diff); ax.set(xlabel='Angle [rad]',ylabel='Point difference [m]',title='Noncommuting transformations'); save(fig,'order')

assert CHECKS and all(v['passed'] for v in CHECKS.values())
report = {'checks':CHECKS, 'seed':42, 'python':sys.version,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['numpy','scipy','matplotlib','modern-robotics']}}
(FIG_DIR/'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')
print('PASS', len(CHECKS), 'numerical checks')
