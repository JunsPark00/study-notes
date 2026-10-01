"""Execute each public script in a fresh process; regenerate figures and numerical evidence."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import tempfile
import hashlib
import time

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=ROOT/'../../assets/books/modern-robotics')
    args = parser.parse_args()
    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    results = []
    for entry in manifest['chapters']:
        script = ROOT/entry['file']
        assert hashlib.sha256(script.read_bytes()).hexdigest() == entry['sha256']
        folder = out/f"chapter{entry['chapter']:02d}"
        start = time.monotonic()
        run = subprocess.run([sys.executable,str(script),'--output-dir',str(folder)], capture_output=True, text=True, timeout=120)
        if run.returncode:
            raise RuntimeError(f"{script.name}: {run.stdout}\n{run.stderr}")
        metrics = json.loads((folder/'metrics.json').read_text(encoding='utf-8'))
        assert metrics['checks'] and all(c['passed'] for c in metrics['checks'].values())
        assert len(list(folder.glob('*.png'))) == 2
        results.append(dict(chapter=entry['chapter'],status='passed',checks=metrics['checks'],seconds=round(time.monotonic()-start,3)))
    cases = []
    original = (ROOT/'chapter13.py').read_text(encoding='utf-8')
    with tempfile.TemporaryDirectory() as temp:
        for right,left in [(12,8),(10,10),(0,0),(8,-8)]:
            code = original.replace('uR,uL=12.,8.',f'uR,uL={right}.,{left}.')
            assert code != original or (right,left)==(12,8)
            script=Path(temp)/'case.py'; script.write_text(code,encoding='utf-8')
            folder=Path(temp)/f'case-{right}-{left}'
            run=subprocess.run([sys.executable,str(script),'--output-dir',str(folder)],capture_output=True,text=True,timeout=120)
            assert run.returncode == 0, run.stdout+run.stderr
            metrics=json.loads((folder/'metrics.json').read_text(encoding='utf-8'))
            cases.append(dict(right=right,left=left,status='passed',checks=metrics['checks']))
    report=dict(status='passed',python=sys.version,chapters=results,odometry_limit_cases=cases,
                scope='Default models and four Chapter 13 limits; not complete textbook or hardware verification.')
    (ROOT/'validation_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8', newline='\n')
    print(f"PASS {len(results)} independent scripts, {sum(len(r['checks']) for r in results)} default numerical checks, {len(cases)} odometry limits")

if __name__ == '__main__':
    main()
