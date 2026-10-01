"""Made by Codex: original supplementary Chapter 12 experiment. Not textbook source code."""
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

from scipy.spatial import ConvexHull, QhullError
def strict_inside(points):
    points=np.asarray(points,float)
    if len(points)<4 or np.linalg.matrix_rank(points-points[0])<3: return False
    try: return bool(np.all(ConvexHull(points).equations[:,-1]<-1e-9))
    except QhullError: return False
contacts=[([-.5,0],[1,0]),([.5,0],[-1,0]),([.3,.3],[0,-1]),([-.3,.3],[0,-1]),([.3,-.3],[0,1]),([-.3,-.3],[0,1])]
wrenches=np.array([[f[0],f[1],r[0]*f[1]-r[1]*f[0]] for r,f in contacts])
check('positive_form_closure',float(not strict_inside(wrenches)),0)
check('boundary_rejected',float(strict_inside([[0,0,0],[1,0,0],[0,1,0],[0,0,1]])),0)
check('rank_deficiency_rejected',float(strict_inside(wrenches[2:])),0)
check('positive_equilibrium',np.linalg.norm(wrenches.T@np.ones(6)/6),1e-12)
fig,ax=plt.subplots()
for r,f in contacts: ax.arrow(*r,f[0]*.15,f[1]*.15,width=.01)
ax.add_patch(plt.Rectangle((-.5,-.3),1,.6,fill=False)); ax.axis('equal'); ax.set(title='Designed frictionless planar contacts',xlabel='x [m]',ylabel='y [m]'); save(fig,'contacts')
fig=plt.figure(); ax=fig.add_subplot(projection='3d'); ax.scatter(*wrenches.T); ax.scatter(0,0,0,c='red')
ax.set(xlabel='fx [N]',ylabel='fy [N]',zlabel='tau [Nm]',title='Origin strictly inside full-dimensional hull'); save(fig,'wrench_hull')

assert CHECKS and all(v['passed'] for v in CHECKS.values())
report = {'checks':CHECKS, 'seed':42, 'python':sys.version,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['numpy','scipy','matplotlib','modern-robotics']}}
(FIG_DIR/'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')
print('PASS', len(CHECKS), 'numerical checks')
