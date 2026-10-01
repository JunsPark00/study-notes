"""Made by Codex: original supplementary Chapter 8 experiment. Not textbook source code."""
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

mass,length,g=1.,.8,9.81; I=mass*length**2
def rhs(t,z): return [z[1],-mass*g*length*np.sin(z[0])/I]
def energy(z): return .5*I*z[1]**2+mass*g*length*(1-np.cos(z[0]))
t=np.linspace(0,5,501); sol=solve_ivp(rhs,[0,5],[.7,0],t_eval=t,rtol=1e-10,atol=1e-12)
assert sol.success; E=energy(sol.y)
check('energy_conservation',np.max(np.abs(E-E[0])),1e-7)
check('positive_inertia',max(0.,-I),0)
z=np.array([.7,0.]); euler=[z.copy()]
for ti in t[:-1]: z=z+(t[1]-t[0])*np.array(rhs(ti,z)); euler.append(z.copy())
euler=np.array(euler).T
fig,ax=plt.subplots(); ax.plot(t,sol.y[0],label='Adaptive'); ax.plot(t,euler[0],'--',label='Euler'); ax.legend()
ax.set(xlabel='Time [s]',ylabel='q [rad]',title='Unforced pendulum'); save(fig,'dynamics')
fig,ax=plt.subplots(); ax.plot(t,E-E[0],label='Adaptive'); Ee=energy(euler); ax.plot(t,Ee-Ee[0],label='Euler'); ax.legend()
ax.set(xlabel='Time [s]',ylabel='Energy change [J]',title='Integration error and energy'); save(fig,'energy')

assert CHECKS and all(v['passed'] for v in CHECKS.values())
report = {'checks':CHECKS, 'seed':42, 'python':sys.version,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['numpy','scipy','matplotlib','modern-robotics']}}
(FIG_DIR/'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')
print('PASS', len(CHECKS), 'numerical checks')
