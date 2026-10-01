"""Made by Codex: original supplementary Chapter 11 experiment. Not textbook source code."""
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

I,Kp,target=1.,16.,1.; t=np.linspace(0,4,501); wn=np.sqrt(Kp/I)
def response(zeta):
    Kd=2*zeta*np.sqrt(Kp*I)
    return solve_ivp(lambda t,z:[z[1],(Kp*(target-z[0])-Kd*z[1])/I],[0,4],[0,0],t_eval=t,rtol=1e-10,atol=1e-12)
critical=response(1.); assert critical.success
exact=target*(1-(1+wn*t)*np.exp(-wn*t))
check('critical_damping_analytic',np.max(np.abs(critical.y[0]-exact)),1e-8)
check('steady_tracking_error',abs(critical.y[0,-1]-target),1e-5)
fig,ax=plt.subplots(); peaks=[]
for damping in [.3,1.,2.]:
    sol=response(damping); assert sol.success; ax.plot(t,sol.y[0],label=f'zeta={damping}'); peaks.append(sol.y[0].max()-target)
ax.axhline(target,color='gray',ls=':'); ax.legend(); ax.set(xlabel='Time [s]',ylabel='q [rad]',title='PD response, no torque saturation'); save(fig,'control_response')
fig,ax=plt.subplots(); ax.bar(['0.3','1.0','2.0'],peaks); ax.set(xlabel='Damping ratio',ylabel='Maximum signed overshoot [rad]',title='Finite-horizon comparison'); save(fig,'overshoot')

assert CHECKS and all(v['passed'] for v in CHECKS.values())
report = {'checks':CHECKS, 'seed':42, 'python':sys.version,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['numpy','scipy','matplotlib','modern-robotics']}}
(FIG_DIR/'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='
')
print('PASS', len(CHECKS), 'numerical checks')
