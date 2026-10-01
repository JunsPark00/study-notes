"""Made by Codex: original supplementary Chapter 6 experiment. Not textbook source code."""
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

L1,L2=1.,.7; target=np.array([1.,.6])
def fk(q):
    a,b=q; return np.array([L1*np.cos(a)+L2*np.cos(a+b),L1*np.sin(a)+L2*np.sin(a+b)])
def jac(q):
    a,b=q; return np.array([[-L1*np.sin(a)-L2*np.sin(a+b),-L2*np.sin(a+b)],[L1*np.cos(a)+L2*np.cos(a+b),L2*np.cos(a+b)]])
c=(target@target-L1**2-L2**2)/(2*L1*L2)
assert abs(c)<=1
solutions=[]
for b in [np.arccos(c),-np.arccos(c)]: solutions.append([np.arctan2(target[1],target[0])-np.arctan2(L2*np.sin(b),L1+L2*np.cos(b)),b])
check('analytic_ik_roundtrip',max(np.linalg.norm(fk(q)-target) for q in solutions),1e-12)
q=np.array([.2,.5]); residual=[]; path=[]
for _ in range(80):
    e=target-fk(q); residual.append(np.linalg.norm(e)); path.append(fk(q))
    if residual[-1]<1e-9: break
    J=jac(q); delta=J.T@np.linalg.solve(J@J.T+.03**2*np.eye(2),e)
    q+=delta*min(1.,.4/max(np.linalg.norm(delta),1e-15))
check('damped_ik_final_residual',np.linalg.norm(fk(q)-target),1e-8)
fig,ax=plt.subplots(); ax.semilogy(residual); ax.set(xlabel='Iteration',ylabel='Position residual [m]',title='Damped IK with step bound'); save(fig,'ik_convergence')
fig,ax=plt.subplots(); ax.plot(*np.array(path).T,'o-'); ax.scatter(*target,c='red'); ax.axis('equal')
ax.set(xlabel='x [m]',ylabel='y [m]',title='End-point iteration path, not a commanded trajectory'); save(fig,'ik_path')

assert CHECKS and all(v['passed'] for v in CHECKS.values())
report = {'checks':CHECKS, 'seed':42, 'python':sys.version,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['numpy','scipy','matplotlib','modern-robotics']}}
(FIG_DIR/'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='
')
print('PASS', len(CHECKS), 'numerical checks')
