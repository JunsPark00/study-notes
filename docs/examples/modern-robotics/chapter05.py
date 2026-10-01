"""Made by Codex: original supplementary Chapter 5 experiment. Not textbook source code."""
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
    a,b=q; return np.array([L1*np.cos(a)+L2*np.cos(a+b),L1*np.sin(a)+L2*np.sin(a+b)])
def jac(q):
    a,b=q; return np.array([[-L1*np.sin(a)-L2*np.sin(a+b),-L2*np.sin(a+b)],[L1*np.cos(a)+L2*np.cos(a+b),L2*np.cos(a+b)]])
q=np.array([.4,.8]); h=1e-6
fd=np.column_stack([(fk(q+h*np.eye(2)[i])-fk(q-h*np.eye(2)[i]))/(2*h) for i in range(2)])
check('jacobian_central_difference',np.linalg.norm(fd-jac(q)),1e-8)
qd=np.array([.3,-.2]); force=np.array([2.,-1.]); tau=jac(q).T@force
check('virtual_power',abs(qd@tau-(jac(q)@qd)@force),1e-12)
angle=np.linspace(-np.pi,np.pi,201); area=np.array([abs(np.linalg.det(jac([.4,b]))) for b in angle])
check('manipulability_formula',np.max(np.abs(area-L1*L2*np.abs(np.sin(angle)))),1e-12)
fig,ax=plt.subplots(); ax.plot(angle,area); ax.set(xlabel='q2 [rad]',ylabel='Area index [m²]',title='Planar position manipulability'); save(fig,'manipulability')
u=np.linspace(0,2*np.pi,150); ellipse=jac(q)@np.array([np.cos(u),np.sin(u)])
fig,ax=plt.subplots(); ax.plot(*ellipse); ax.axis('equal'); ax.set(xlabel='vx [m/s]',ylabel='vy [m/s]',title='Unit joint-speed circle mapped to task space'); save(fig,'velocity_ellipse')

assert CHECKS and all(v['passed'] for v in CHECKS.values())
report = {'checks':CHECKS, 'seed':42, 'python':sys.version,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['numpy','scipy','matplotlib','modern-robotics']}}
(FIG_DIR/'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='
')
print('PASS', len(CHECKS), 'numerical checks')
