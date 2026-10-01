"""Made by Codex: original supplementary Chapter 9 experiment. Not textbook source code."""
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

T=2.; t=np.linspace(0,T,401); u=t/T
s=10*u**3-15*u**4+6*u**5; v=(30*u**2-60*u**3+30*u**4)/T; a=(60*u-180*u**2+120*u**3)/T**2
check('quintic_endpoint_position',max(abs(s[0]),abs(s[-1]-1)),1e-12)
check('quintic_endpoint_velocity',np.max(np.abs(v[[0,-1]])),1e-12)
check('quintic_endpoint_acceleration',np.max(np.abs(a[[0,-1]])),1e-12)
D,vmax,amax=1.,1.,2.; peak=min(vmax,np.sqrt(amax*D)); ramp=peak/amax; cruise=(D-peak**2/amax)/peak
total=2*ramp+cruise; tt=np.linspace(0,total,401); vv=np.minimum(np.minimum(amax*tt,amax*(total-tt)),peak)
ss=np.where(tt<ramp,.5*amax*tt**2,np.where(tt<=ramp+cruise,.5*peak*ramp+peak*(tt-ramp),D-.5*amax*(total-tt)**2))
check('constant_limit_distance',abs(ss[-1]-D),1e-12)
check('strict_time_grid',float(np.sum(np.diff(tt)<=0)),0)
check('speed_limit_violation',max(0.,vv.max()-vmax),1e-12)
fig,ax=plt.subplots(); ax.plot(t,s,label='Quintic'); ax.plot(tt,ss,label='Minimum scalar time'); ax.legend()
ax.set(xlabel='Time [s]',ylabel='s',title='Same scalar path, different timing'); save(fig,'time_scaling')
fig,ax=plt.subplots(); ax.plot(t,v,label='Quintic'); ax.plot(tt,vv,label='Trapezoidal'); ax.axhline(vmax,color='red',ls=':'); ax.legend()
ax.set(xlabel='Time [s]',ylabel='s_dot',title='Endpoint conditions and speed bound'); save(fig,'speed_profile')

assert CHECKS and all(v['passed'] for v in CHECKS.values())
report = {'checks':CHECKS, 'seed':42, 'python':sys.version,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['numpy','scipy','matplotlib','modern-robotics']}}
(FIG_DIR/'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='
')
print('PASS', len(CHECKS), 'numerical checks')
