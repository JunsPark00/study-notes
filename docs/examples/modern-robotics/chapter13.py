"""Made by Codex: original supplementary Chapter 13 experiment. Not textbook source code."""
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

r,d=.05,.2; uR,uL=12.,8.; v=r*(uR+uL)/2; omega=r*(uR-uL)/d; duration=2.
def exact(t):
    t=np.asarray(t)
    if abs(omega)<1e-12: return np.column_stack([v*t,np.zeros_like(t)])
    return np.column_stack([v*np.sin(omega*t)/omega,v*(1-np.cos(omega*t))/omega])
def euler(dt):
    count=round(duration/dt); dt=duration/count; z=np.zeros(3); path=[z.copy()]
    for _ in range(count): z+=dt*np.array([v*np.cos(z[2]),v*np.sin(z[2]),omega]); path.append(z.copy())
    return np.array(path)
times=np.linspace(0,duration,200); path=exact(times)
theta=omega*times
check('nonholonomic_constraint',np.max(np.abs(-np.sin(theta)*v*np.cos(theta)+np.cos(theta)*v*np.sin(theta))),1e-12)
if abs(omega)>1e-12:
    check('circular_radius',np.max(np.abs(np.linalg.norm(path-[0,v/omega],axis=1)-abs(v/omega))),1e-12)
else:
    check('straight_line_limit',np.max(np.abs(path-np.column_stack([v*times,np.zeros_like(times)]))),1e-12)
    print('omega=0: straight/stationary motion; no circular radius is defined.')
steps=np.array([.1,.05,.025,.0125]); errors=np.array([np.linalg.norm(euler(dt)[-1,:2]-exact([duration])[0]) for dt in steps])
ratio_applicable=abs(v)>1e-12 and abs(omega)>1e-12 and errors[1]>1e-12
if ratio_applicable:
    check('euler_first_order_ratio',abs(errors[0]/errors[1]-2),.02)
else:
    check('euler_exact_limit_error',np.max(errors),1e-12)
    print('Straight/stationary position integration is exact to roundoff; no convergence ratio is defined.')
fig,ax=plt.subplots(); ax.plot(*path.T,label='Exact'); coarse=euler(.1); ax.plot(*coarse[:,:2].T,'o--',label='Euler dt=0.1'); ax.axis('equal'); ax.legend()
ax.set(xlabel='x [m]',ylabel='y [m]',title='Differential drive at common physical horizon'); save(fig,'odometry')
fig,ax=plt.subplots()
if ratio_applicable: ax.loglog(steps,errors,'o-')
else: ax.plot(steps,errors,'o-')
ax.set(xlabel='dt [s]',ylabel='Final position error [m]',title='Euler convergence' if ratio_applicable else 'Exact limit: no convergence ratio'); save(fig,'integration_error')

assert CHECKS and all(v['passed'] for v in CHECKS.values())
report = {'checks':CHECKS, 'seed':42, 'python':sys.version,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['numpy','scipy','matplotlib','modern-robotics']}}
(FIG_DIR/'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')
print('PASS', len(CHECKS), 'numerical checks')
