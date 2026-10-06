"""Read-only exact candidate analyzer. Does not invoke implementation tools."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

BASE = "1bf0552d702c0e6cefc659b38184f505118f11d1"
ALLOWED = {
    'TECHNICAL_DOCUMENTATION.md',
    'automation/STATUS.md',
    'automation/tasks.json',
    'automation/specs/ISI-28-R3-OPERATIONS-AND-RESPONSIVE-CLOSEOUT.md',
    'docs/legal/ISI-LEGAL-NOTICES-RELEASE-CHECKLIST.md',
    'docs/ops/ISI-28-CONTROLLED-DEPLOYMENT-PLAN.md',
    'docs/ops/ISI-28-PRIVACY-OPERATIONS-BASELINE.md',
    'docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md',
    'src/core/config.py',
    'src/streamlit_app/app.py',
    'src/platform/ai/gateway.py',
    'src/platform/ai/providers.py',
    'src/public/static/css/public-readiness.css',
    'src/public/static/js/public-readiness.js',
    'tests/test_isi_04c_readiness_contract.py',
    'tests/test_isi_28_operations.py',
    'tests/test_isi_28_provider_resources.py',
    'tools/server/isi28_operations.py',
    'tools/qa/run_isi28_r3.py',
    'tools/qa/analyze_isi28_r3.py',
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def main() -> int:
    assert git("branch", "--show-current") == "main"
    assert git("rev-parse", "HEAD") == BASE == git("rev-parse", "origin/main")
    assert not git("diff", "--cached", "--name-only")
    assert not git("stash", "list")
    assert git("worktree", "list", "--porcelain").count("worktree ") == 1
    paths = set(git("diff", "--name-only").splitlines()) | set(
        git("ls-files", "--others", "--exclude-standard").splitlines())
    assert paths == ALLOWED, sorted(paths.symmetric_difference(ALLOWED))
    subprocess.run(["git", "diff", "--check"], check=True)
    suite = next(ET.parse("automation/evidence/ISI-28/r3/regression-final.xml").iter("testsuite"))
    assert int(suite.attrib["failures"]) == int(suite.attrib["errors"]) == 0
    assert int(suite.attrib["tests"]) == 1223 and int(suite.attrib["skipped"]) == 43
    tasks = json.loads(Path("automation/tasks.json").read_text())
    from tools.release.governance import validate_release_state
    assert validate_release_state({t["id"]: t for t in tasks["tasks"]}) == "ISI-28-CURRENT-SERVER-CONTROLLED-UPGRADE"
    digest = hashlib.sha256()
    files = {}
    for path in sorted(paths):
        p = Path(path)
        assert not p.is_symlink()
        data = p.read_bytes()
        files[path] = hashlib.sha256(data).hexdigest()
        digest.update(path.encode() + b"\0" + data + b"\0")
    print(json.dumps({"status": "PASS", "baseline": BASE, "candidate_fingerprint": digest.hexdigest(),
                      "files": files, "passed": 1180, "skipped": 43,
                      "schema_domain_dependency_CI_changes": False, "server_verified": False, "preproduction_testing": True, "new_backups_authorized": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
