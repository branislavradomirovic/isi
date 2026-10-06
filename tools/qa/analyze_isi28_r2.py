"""Read-only exact candidate analyzer. Does not invoke implementation tools."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

BASE = "3986a03182eed04ba8055a6156d6722bca1504f5"
ALLOWED = {
    "TECHNICAL_DOCUMENTATION.md", "automation/STATUS.md", "automation/tasks.json",
    "automation/specs/ISI-28-R2-PRODUCTION-ACTIVATION.md", "data/public/legal_notices.json",
    "docs/legal/ISI-LEGAL-NOTICES-RELEASE-CHECKLIST.md",
    "docs/ops/ISI-28-PRIVACY-OPERATIONS-BASELINE.md",
    "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md",
    "src/api/auth_routes.py", "src/platform/auth/delivery.py", "src/platform/deployment/runtime.py",
    "tests/test_isi_28_pending_email.py", "tests/test_isi_28_legal_publication.py",
    "tools/publish_isi_legal_notices.py", "tools/qa/run_isi28_r2.py", "tools/qa/analyze_isi28_r2.py",
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
    suite = next(ET.parse("automation/evidence/ISI-28/r2/regression-final.xml").iter("testsuite"))
    assert int(suite.attrib["failures"]) == int(suite.attrib["errors"]) == 0
    assert int(suite.attrib["tests"]) == 1187 and int(suite.attrib["skipped"]) == 43
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
                      "files": files, "passed": 1144, "skipped": 43,
                      "schema_domain_dependency_CI_changes": False, "server_verified": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
