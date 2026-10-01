#!/usr/bin/env python3
"""Re-run every independently downloadable example in a clean temporary folder.

Run: python validate_all.py --output-dir validation_output
Requires the 19 chapterNN.py files beside this validator and the libraries in
requirements.txt. Each subprocess gets only its one chapter script, its own
output directory, and fresh plotting caches. No prior figures/results are read.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "optimization-validator-mpl"))
import numpy
import scipy
import matplotlib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('validation_output'))
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    destination = args.output_dir.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for chapter in range(1, 20):
        filename = f'chapter{chapter:02d}.py'
        source = here / filename
        tree = ast.parse(source.read_text(encoding='utf-8'))
        imports = sorted({(node.module or '').split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)} | {alias.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names})
        assert all(module in sys.stdlib_module_names or module in {'numpy', 'scipy', 'matplotlib'} for module in imports), imports
        with tempfile.TemporaryDirectory(prefix=f'optimization-ch{chapter:02d}-') as temporary:
            root = Path(temporary)
            shutil.copy2(source, root / filename)
            output = root / 'output'
            environment = os.environ.copy()
            environment.update(MPLCONFIGDIR=str(root / 'mpl-cache'), XDG_CACHE_HOME=str(root / 'cache'), PYTHONHASHSEED='0', PYTHONNOUSERSITE='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
            environment.pop('PYTHONPATH', None)
            start = time.monotonic()
            run = subprocess.run([sys.executable, '-I', filename, '--output-dir', str(output)], cwd=root, env=environment, capture_output=True, text=True, timeout=180)
            if run.returncode:
                raise RuntimeError(f'{filename} failed ({run.returncode})\n{run.stdout}\n{run.stderr}')
            result_files = list(output.glob('*.json'))
            assert len(result_files) == 1, f'{filename}: expected one saved JSON result, got {result_files}'
            data = json.loads(result_files[0].read_text(encoding='utf-8'), parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
            assert isinstance(data, dict) and data, f'{filename}: empty result'
            figure = output / f'chapter{chapter:02d}.png'
            assert figure.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'), f'{filename}: missing PNG'
            target = destination / f'chapter{chapter:02d}'
            target.mkdir(exist_ok=True)
            (target / 'result.json').write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
            shutil.copy2(figure, target / 'figure.png')
            records.append({'chapter': chapter, 'script': filename, 'status': 'passed', 'isolated_script_only': True, 'assertions_enabled': True, 'json_saved_by_script': result_files[0].name, 'figure_bytes': figure.stat().st_size, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'imports': imports, 'elapsed_seconds': round(time.monotonic() - start, 3), 'stderr': run.stderr.strip()})
            print(f'PASS {filename}: assertions, saved JSON, freshly rendered PNG', flush=True)
    summary = {'status': 'passed', 'examples': len(records), 'python': platform.python_version(), 'numpy': numpy.__version__, 'scipy': scipy.__version__, 'matplotlib': matplotlib.__version__, 'method': 'Every script copied alone to its own fresh directory and run with Python isolated mode; all embedded assertions enabled; saved JSON parsed and PNG checked.', 'limits': 'These finite experiments validate their stated instances, not general convergence or correctness for all possible inputs. Plot fonts may vary by host.', 'chapters': records}
    (destination / 'validation_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'All {len(records)} examples passed. Summary: {destination / "validation_summary.json"}')


if __name__ == '__main__':
    main()
