"""Read-only candidate analysis; no implementation invocation or state mutations."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASE = '374dda3db89f6fb87dde7f5b761642440da17bef'
ALLOWED = {
    'TECHNICAL_DOCUMENTATION.md', 'automation/STATUS.md', 'automation/tasks.json',
    'automation/specs/TASK-TEMPLATE.md', 'docs/ops/ISI-AUTONOMOUS-DEVELOPMENT-LOCK.md',
    'docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md',
    'automation/specs/ISI-29A-GRAPHICAL-XAI.md', 'docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md',
    'src/streamlit_app/xai_charts.py', 'src/streamlit_app/simpa_analytics_workspace.py',
    'src/streamlit_app/ordo_analytics_workspace.py', 'src/streamlit_app/simpa_help_workspace.py',
    'src/streamlit_app/ordo_help_workspace.py', 'docs/help/SIMPA-USER-GUIDE.md',
    'docs/help/ORDO-USER-GUIDE.md', 'docs/help/ISI-HELP-COVERAGE-MATRIX.md',
    'tests/test_isi_29a_xai_charts.py', 'tests/test_isi_29a_xai_ui_contract.py',
    'tests/test_isi_29a_xai_help_contract.py', 'tools/qa/run_isi29a.py', 'tools/qa/analyze_isi29a.py',
}


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def manifest() -> dict:
    assert git('branch', '--show-current') == 'main'
    assert git('rev-parse', 'HEAD') == BASE == git('rev-parse', 'origin/main')
    assert not git('diff', '--cached', '--name-only') and not git('stash', 'list')
    assert git('worktree', 'list', '--porcelain').count('worktree ') == 1
    paths = set(git('diff', '--name-only').splitlines()) | set(git('ls-files', '--others', '--exclude-standard').splitlines())
    assert paths <= ALLOWED, sorted(paths - ALLOWED)
    files = {}
    for name in sorted(paths):
        p = ROOT / name
        assert p.is_file() and not p.is_symlink()
        files[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return {'baseline': BASE, 'files': files, 'fingerprint': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def main() -> None:
    current = manifest()
    evidence = ROOT / 'automation/evidence/ISI-29A'
    assert set(current['files']) == ALLOWED
    preflight = json.loads((evidence / 'planning-preflight.json').read_text())
    assert preflight['status'] == 'PASS' and preflight['planning_prestate_8_hashes_match']
    report = json.loads((evidence / 'acceptance.json').read_text())
    assert report['candidate'] == current and report['status'] == 'PASS'
    assert all(g['returncode'] == 0 for g in report['gates'])
    for gate in report['gates']:
        assert hashlib.sha256((evidence / gate['log']).read_bytes()).hexdigest() == gate['sha256']
    for name in ('focused.xml', 'regression.xml'):
        data = (evidence / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == report['xml_sha256'][name]
        suites = list(ET.fromstring(data).iter('testsuite'))
        assert suites and sum(int(s.attrib['tests']) for s in suites) > 0
        assert all(int(s.attrib['errors']) == int(s.attrib['failures']) == 0 for s in suites)
    subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
    print(json.dumps({'status': 'PASS', 'candidate': current, 'runtime_scope': '29A_ONLY',
                      'server_verification': 'DEFERRED_SERVER_VERIFICATION', 'visual_qa_required': True}, indent=2))


if __name__ == '__main__':
    main()
