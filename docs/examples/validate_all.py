#!/usr/bin/env python3
"""Copy each chapter script alone to a fresh folder and run its assert checks."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path("validation_output"))
    parser.add_argument("--summary", type=Path, default=Path("validation_summary.json"))
    args = parser.parse_args()
    if sys.flags.optimize:
        raise SystemExit("Do not use python -O: assert checks must stay enabled.")
    root = Path(__file__).resolve().parent
    scripts = sorted(root.glob("chapter[0-9][0-9]_*.py"))
    assert len(scripts) == 8, f"Expected 8 chapter files, found {len(scripts)}"
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    runs = []
    for chapter, script in enumerate(scripts, 1):
        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix=f"mpc-chapter{chapter:02d}-") as temporary:
            work = Path(temporary)
            copied = work / script.name
            shutil.copy2(script, copied)
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            env["MPLCONFIGDIR"] = str(work / "mpl-cache")
            env["XDG_CACHE_HOME"] = str(work / "xdg-cache")
            env["PYTHONNOUSERSITE"] = "1"
            process = subprocess.run([sys.executable, "-B", str(copied), "--output-dir", str(work / "result")],
                                     cwd=work, env=env, text=True, capture_output=True, timeout=180)
            passed = process.returncode == 0
            result_path = work / "result" / "result.json"
            figure_path = work / "result" / "figure.png"
            result = json.loads(result_path.read_text()) if result_path.exists() else None
            passed = passed and result is not None and result.get("status") == "passed"
            passed = passed and figure_path.exists() and figure_path.stat().st_size > 1024
            if result is not None and result.get("chapter") != chapter:
                passed = False
            destination = output_root / f"chapter{chapter:02d}"
            destination.mkdir(parents=True, exist_ok=True)
            if (work / "result").exists():
                for artifact in (work / "result").iterdir():
                    if artifact.is_file():
                        shutil.copy2(artifact, destination / artifact.name)
            (destination / "stdout.txt").write_text(process.stdout, encoding="utf-8")
            (destination / "stderr.txt").write_text(process.stderr, encoding="utf-8")
            run = {"chapter": chapter, "source": script.name, "status": "passed" if passed else "failed",
                   "returncode": process.returncode, "isolated_single_file_execution": True,
                   "sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
                   "duration_seconds": round(time.perf_counter() - started, 3),
                   "checks": result.get("checks", []) if result else [],
                   "result": f"chapter{chapter:02d}/result.json",
                   "figure": f"chapter{chapter:02d}/figure.png"}
            runs.append(run)
            print(f"Chapter {chapter:02d}: {run['status']} ({run['duration_seconds']:.2f}s)")
            if not passed:
                print(process.stderr, file=sys.stderr)
    summary = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "status": "passed" if all(run["status"] == "passed" for run in runs) else "failed",
               "python_version": platform.python_version(), "platform": platform.platform(),
               "dependencies": {name: importlib.metadata.version(name) for name in ["numpy", "scipy", "matplotlib"]},
               "method": "Each single source file copied alone to a new temporary working directory and executed in a separate Python process",
               "assert_checks_enabled": True, "output_root": args.output_root.name,
               "runs": runs}
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if summary["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
