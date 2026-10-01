"""Made by Codex: original supplementary Chapter 7 experiment. Not textbook source code."""
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

angles=np.arange(3)*2*np.pi/3
A0=1.5*np.column_stack([np.cos(angles),np.sin(angles)])
B0=.5*np.column_stack([np.cos(angles),np.sin(angles)])
def legs(q):
    x,y,phi=q; R=np.array([[np.cos(phi),-np.sin(phi)],[np.sin(phi),np.cos(phi)]])
    offsets=B0@R.T; d=offsets+[x,y]-A0; lengths=np.linalg.norm(d,axis=1); unit=d/lengths[:,None]
    derivative=np.column_stack([-offsets[:,1],offsets[:,0]])
    J=np.column_stack([unit,np.sum(unit*derivative,axis=1)])
    return lengths,J,offsets+[x,y]
q=np.array([.1,.2,.4]); h=1e-6
fd=np.column_stack([(legs(q+h*np.eye(3)[i])[0]-legs(q-h*np.eye(3)[i])[0])/(2*h) for i in range(3)])
check('leg_jacobian_difference',np.linalg.norm(fd-legs(q)[1]),1e-8)
lengths,J,ends=legs(q)
check('length_reconstruction',np.max(np.abs(lengths-np.linalg.norm(ends-A0,axis=1))),1e-12)
fig,ax=plt.subplots()
for a,b in zip(A0,ends): ax.plot([a[0],b[0]],[a[1],b[1]],'o-')
closed=np.vstack([ends,ends[0]]); ax.plot(*closed.T); ax.axis('equal'); ax.set(title='Designed planar 3RPR',xlabel='x [m]',ylabel='y [m]'); save(fig,'parallel_geometry')
phi=np.linspace(-np.pi,np.pi,200); sigma=[np.linalg.svd(legs([.1,.2,p])[1],compute_uv=False)[-1] for p in phi]
fig,ax=plt.subplots(); ax.plot(phi,sigma); ax.set(xlabel='Platform angle [rad]',ylabel='Smallest singular value',title='Mixed translation/rotation coordinates, fixed length scale'); save(fig,'constraint_rank')

assert CHECKS and all(v['passed'] for v in CHECKS.values())
report = {'checks':CHECKS, 'seed':42, 'python':sys.version,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['numpy','scipy','matplotlib','modern-robotics']}}
(FIG_DIR/'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='
')
print('PASS', len(CHECKS), 'numerical checks')
