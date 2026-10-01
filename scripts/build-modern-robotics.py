"""Render the explicitly allowlisted original educational source, without external repositories."""
from pathlib import Path
import json
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'content/books/modern-robotics'
EXAMPLES = ROOT / 'docs/examples/modern-robotics'
ASSETS = ROOT / 'docs/assets/books/modern-robotics'
CHAPTERS = json.loads((SOURCE / 'study-content.json').read_text(encoding='utf-8'))

SETUP = '''import argparse, json, sys, importlib.metadata
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
'''
FINAL = '''assert CHECKS and all(v['passed'] for v in CHECKS.values())
report = {'checks':CHECKS, 'seed':42, 'python':sys.version,
          'versions':{name:importlib.metadata.version(name) for name in
                      ['numpy','scipy','matplotlib','modern-robotics']}}
(FIG_DIR/'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\\n', encoding='utf-8', newline='\n')
print('PASS', len(CHECKS), 'numerical checks')
'''

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')

def main():
    EXAMPLES.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    registry, examples = [], []
    for c in CHAPTERS:
        n = c['n']; nn = f'{n:02d}'
        stems = re.findall(r"save\(fig,'([^']+)'\)", c['code'])
        script = f'chapter{nn}.py'
        code = f'"""Made by Codex: original supplementary Chapter {n} experiment. Not textbook source code."""\n'+SETUP+'\n'+c['code']+'\n\n'+FINAL
        write(EXAMPLES / script, code)
        text = f"# {c['title']}\n\n## 학습 범위와 가정\n\nLynch·Park의 *Modern Robotics* {n}장({c['en']}) 주제와 연결한 직접 작성한 보충 노트입니다. 교재 전체 절의 번역이나 해답집이 아닙니다. 아래 세 개념과 작은 실험에 범위를 한정합니다. 길이는 m, 시간은 s, 각도는 rad이며 열벡터·오른손 좌표계를 사용합니다.\n\n"
        for i, (title, body, _) in enumerate(c['topics']):
            text += f"## {title}\n\n{body}\n\n$$\n{c['equations'][i]}\n$$\n\n"
        text += '## 직접 설계한 실험과 검산\n\n교재의 그림·수치를 복제하지 않고 작은 모델을 구성했습니다. 아래 다운로드 코드의 assert는 독립 계산 또는 해석적 관계와 수치 결과를 비교합니다. 그림 라벨은 글꼴 설치 없이 실행할 수 있도록 영어로 표시합니다.\n\n'
        for stem in stems:
            text += f"![{c['title']}: 직접 계산한 {stem.replace('_',' ')} 결과](assets/books/modern-robotics/chapter{nn}/{stem}.png)\n\n"
        text += f"## 결과 해석과 바꿔 보기\n\n{c['interpret']}\n\n**바꿔 보기:** {c['exercise']}\n\n게시된 검증 결과는 기본 설정의 결과입니다. 입력이나 모델을 바꾸면 허용오차와 성공 기준을 재검토하세요.\n\n## 다음 학습과 출처\n\n[공식 저자 자료](https://modernrobotics.northwestern.edu/)에서 해당 장의 이론과 정오표를 확인하세요. 이 노트의 번호는 자체 학습 순서이며 교재 하위 절 번호를 재현하지 않습니다.\n\n**Made by Codex.** 설명·수식·코드에 오류가 있을 수 있습니다. 수치 검사는 모든 이론이나 실제 하드웨어의 정확성을 보장하지 않습니다.\n"
        write(SOURCE / f'chapter{nn}.md', text)
        registry.append(dict(number=n, title=c['title'], file=f'books/modern-robotics/chapter{nn}.md', description=c['interpret'], tags=[t[0] for t in c['topics']], category='ROBOTICS'))
        examples.append(dict(chapter=n, file=script, title=c['title']+' 보충 실험', purpose_ko=c['interpret'], scope_ko='직접 설계한 선택적 입문 실험. 해당 장 전체 이론·문제·실제 로봇을 재현하지 않습니다.', verified_claims_ko=['유한한 잔차와 모델별 허용오차를 assert로 확인합니다. 실제 값은 검증 JSON에 기록합니다.'], command=f'python {script} --output-dir output/chapter{nn}', figure=f'../../assets/books/modern-robotics/chapter{nn}/{stems[0]}.png', figures=[f'../../assets/books/modern-robotics/chapter{nn}/{s}.png' for s in stems], sha256=hashlib.sha256(code.encode()).hexdigest(), validation_result=f'../../assets/books/modern-robotics/chapter{nn}/metrics.json', random_seed=42))
    write(SOURCE/'chapters.json', json.dumps(registry, ensure_ascii=False, indent=2)+'\n')
    manifest=dict(schema_version=1, title='Modern Robotics 직접 작성한 보충 실험', authorship='Made by Codex. Original educational explanations and experiments; figures computed from these scripts. No textbook or archival files.', python_recommended='>=3.11', readme='README.ko.md', requirements='requirements.txt', validator='validate_all.py', validation_summary='validation_summary.json', chapters=examples)
    write(EXAMPLES/'manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')

if __name__ == '__main__':
    main()
