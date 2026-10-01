"""Explicit public allowlist and source hashes; no repository-directory mirroring."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT/'content/books/modern-robotics'
EXAMPLES = ROOT/'docs/examples/modern-robotics'
ASSETS = ROOT/'docs/assets/books/modern-robotics'

def main():
    chapters=json.loads((CONTENT/'study-content.json').read_text(encoding='utf-8'))
    expected = {CONTENT/'study-content.json', CONTENT/'chapters.json', CONTENT/'attribution.md'}
    expected |= {CONTENT/f'chapter{n:02d}.md' for n in range(1,14)}
    expected |= {EXAMPLES/f'chapter{n:02d}.py' for n in range(1,14)}
    expected |= {EXAMPLES/name for name in ['README.ko.md','requirements.txt','manifest.json','validate_all.py','validation_summary.json']}
    for c in chapters:
        folder=ASSETS/f"chapter{c['n']:02d}"
        expected.add(folder/'metrics.json')
        expected |= {folder/(name+'.png') for name in re.findall(r"save\(fig,'([^']+)'\)",c['code'])}
    actual={p for root in [CONTENT,EXAMPLES,ASSETS] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    actual.discard(EXAMPLES/'provenance.json')
    assert actual == expected, f'Unexpected or missing allowlist files: {actual ^ expected}'
    forbidden=re.compile(r'github\.com/JunsPark00/(?!study-notes)|[A-Za-z]:[\\/]+Users[\\/]|/workspace/|sediment://|beamer_legacy|chapter\d+_notes\.(?:tex|pdf)|\.\./README\.md')
    scanned=0
    for folder in [CONTENT,ROOT/'docs']:
        for p in folder.rglob('*'):
            if p.is_file() and p.suffix in ['.md','.json','.py','.html','.js','.css','.mjs']:
                assert not forbidden.search(p.read_text(encoding='utf-8')), f'Nonpublic source reference: {p.relative_to(ROOT)}'
                scanned+=1
    files=[]
    for p in sorted(expected):
        role='newly computed figure' if p.suffix=='.png' else 'original public educational content/code or derived execution evidence'
        files.append(dict(path=p.relative_to(ROOT).as_posix(),role=role,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    report=dict(status='passed',policy='Explicit file allowlist. No textbook, scans, archival notes, TeX, slides, notebook, repository history or private links. No blanket legal clearance implied.',authorship='Made by Codex; original supplementary educational explanations and examples.',figures=26,chapters=13,scanned_text_files=scanned,dependencies='Imports only; no vendored Modern Robotics implementation. Dependency licenses remain with their projects.',files=files)
    (EXAMPLES/'provenance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8', newline='\n')
    print(f'PASS explicit allowlist {len(expected)} files; {scanned} text files scanned; 26 computed figures')

if __name__ == '__main__':
    main()
