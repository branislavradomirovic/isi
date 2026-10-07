"""Deterministic local gate; candidate-bound logs. No hosted CI or server action."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.qa.analyze_isi29a import manifest  # noqa: E402


def main() -> int:
    assert Path(sys.executable).parent == ROOT / '.venv/bin'
    evidence = ROOT / 'automation/evidence/ISI-29A'
    evidence.mkdir(parents=True, exist_ok=True)
    prestate = json.loads((evidence / 'planning-prestate.json').read_text())
    assert prestate['baseline'] == manifest()['baseline']
    assert len(prestate['candidate_files']) == 8 and all(len(f['sha256']) == 64 for f in prestate['candidate_files'])
    candidate = manifest()
    env = dict(os.environ)
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    focused = ['tests/test_isi_29a_xai_charts.py', 'tests/test_isi_29a_xai_ui_contract.py', 'tests/test_isi_29a_xai_help_contract.py']
    commands = [
        [sys.executable, '-m', 'ruff', 'check', 'src/streamlit_app/xai_charts.py', *focused, 'tools/qa/run_isi29a.py', 'tools/qa/analyze_isi29a.py'],
        [sys.executable, '-m', 'mypy', 'tools/ci'],
        [sys.executable, '-m', 'tools.ci.policy_check'],
        [sys.executable, '-m', 'pytest', '-q', *focused, '--junitxml=' + str(evidence / 'focused.xml')],
        [sys.executable, '-m', 'pytest', '-q', '--junitxml=' + str(evidence / 'regression.xml')],
        ['git', 'diff', '--check'],
    ]
    gates = []
    for i, command in enumerate(commands):
        log = evidence / f'gate-{i}.log'
        with log.open('wb') as handle:
            completed = subprocess.run(command, cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT)
        gates.append({'command': command, 'returncode': completed.returncode, 'log': log.name,
                      'sha256': hashlib.sha256(log.read_bytes()).hexdigest()})
        print(f'gate {i}: {completed.returncode}', flush=True)
        if completed.returncode:
            print(log.read_text()[-6000:])
            return completed.returncode
    assert candidate == manifest(), 'candidate changed during gates'
    xml = {name: hashlib.sha256((evidence / name).read_bytes()).hexdigest() for name in ('focused.xml', 'regression.xml')}
    (evidence / 'acceptance.json').write_text(json.dumps({'status': 'PASS', 'candidate': candidate,
                                                       'gates': gates, 'xml_sha256': xml}, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
