"""Made by Codex: original supplementary Chapter 10 experiment. Not textbook source code."""
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

import heapq
center=np.array([1.,1.]); radius=.4
def collision(a,b):
    delta=b-a; d2=delta@delta; z=np.clip((center-a)@delta/d2,0,1) if d2 else 0
    return np.linalg.norm(a+z*delta-center)<=radius
grid=np.linspace(0,2,11); points=np.array([[x,y] for x in grid for y in grid]); start=0; goal=len(points)-1
dist={start:0.}; parent={}; heap=[(0.,start)]
while heap:
    cost,i=heapq.heappop(heap)
    if cost>dist[i]: continue
    if i==goal: break
    x,y=divmod(i,len(grid))
    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
        xx,yy=x+dx,y+dy
        if not (0<=xx<len(grid) and 0<=yy<len(grid)): continue
        j=xx*len(grid)+yy
        if collision(points[i],points[j]): continue
        candidate=cost+np.linalg.norm(points[j]-points[i])
        if candidate<dist.get(j,np.inf): dist[j]=candidate; parent[j]=i; heapq.heappush(heap,(candidate,j))
assert goal in dist
indices=[goal]
while indices[-1]!=start: indices.append(parent[indices[-1]])
path=points[indices[::-1]]
check('path_colliding_edges',sum(collision(a,b) for a,b in zip(path[:-1],path[1:])),0)
check('path_endpoints',np.linalg.norm(path[0]-points[start])+np.linalg.norm(path[-1]-points[goal]),1e-12)
check('dijkstra_cost_reconstruction',abs(np.linalg.norm(np.diff(path,axis=0),axis=1).sum()-dist[goal]),1e-12)
fig,ax=plt.subplots(); ax.add_patch(plt.Circle(center,radius,color='gray')); ax.plot(*path.T,'o-'); ax.plot([0,2],[0,2],'r--')
ax.axis('equal'); ax.set(xlabel='x [m]',ylabel='y [m]',title='Every returned edge checked'); save(fig,'planning')
fig,ax=plt.subplots(); lengths=np.linalg.norm(np.diff(path,axis=0),axis=1); ax.plot(np.r_[0,np.cumsum(lengths)],'o-')
ax.set(xlabel='Path node',ylabel='Cumulative distance [m]',title='Graph shortest-path cost'); save(fig,'path_cost')

assert CHECKS and all(v['passed'] for v in CHECKS.values())
report = {'checks':CHECKS, 'seed':42, 'python':sys.version,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['numpy','scipy','matplotlib','modern-robotics']}}
(FIG_DIR/'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')
print('PASS', len(CHECKS), 'numerical checks')
