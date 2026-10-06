"""Deterministic local R3 gate. No staging, hosted CI, or server execution."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    evidence = root / 'automation/evidence/ISI-28/r3'
    evidence.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    commands = [
        [sys.executable, '-m', 'ruff', 'check', 'tools/server/isi28_operations.py',
         'tools/qa/run_isi28_r3.py', 'tools/qa/analyze_isi28_r3.py',
         'src/core/config.py', 'src/streamlit_app/app.py', 'src/platform/ai/gateway.py', 'src/platform/ai/providers.py',
         'tests/test_isi_28_operations.py', 'tests/test_isi_28_provider_resources.py',
         'tests/test_isi_04c_readiness_contract.py'],
        [sys.executable, '-m', 'mypy', 'tools/ci'],
        [sys.executable, '-m', 'tools.ci.policy_check'],
        ['git', 'diff', '--check'],
        [sys.executable, '-m', 'pytest', '--junitxml=' + str(evidence / 'regression-final.xml')],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=root, env=env)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
