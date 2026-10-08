"""Read-only exact-candidate analyzer; no implementation/CI/server invocation."""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "95fec43590e9b1d3eb44d55867666581118ec650"
FILES = (
    "TECHNICAL_DOCUMENTATION.md",
    "automation/STATUS.md",
    "automation/tasks.json",
    "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md",
    "docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md",
    "docs/help/ISI-HELP-COVERAGE-MATRIX.md",
    "docs/help/ISI-EXTRACTION-GUIDE.md",
    "automation/specs/ISI-29E-ENTITY-CLAIM-EXTRACTION.md",
    "src/platform/extraction/__init__.py",
    "src/platform/extraction/contracts.py",
    "src/platform/extraction/models.py",
    "src/platform/extraction/service.py",
    "src/domains/simpa/extraction_adapter.py",
    "src/domains/ordo/extraction_adapter.py",
    "src/platform/models.py",
    "src/api/extraction_routes.py",
    "src/api/app.py",
    "src/workers/ai_jobs.py",
    "src/streamlit_app/extraction_api.py",
    "src/streamlit_app/extraction_workspace.py",
    "src/streamlit_app/data_workspace.py",
    "migrations/versions/20261008_0037_extraction.py",
    "tests/test_isi_29e_contracts.py",
    "tests/test_isi_29e_service.py",
    "tests/test_isi_29e_ui_api.py",
    "tests/test_isi_29e_native_postgres.py",
    "tests/evals/SIMPA-EXTRACTION-v1.json",
    "tests/evals/ORDO-EXTRACTION-v1.json",
    "tools/qa/run_isi29e.py",
    "tools/qa/analyze_isi29e.py",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def manifest() -> dict:
    assert git("branch", "--show-current") == "main"
    assert git("rev-parse", "HEAD") == git("rev-parse", "origin/main") == BASELINE
    assert not git("diff", "--cached", "--name-only") and not git("stash", "list")
    assert git("worktree", "list", "--porcelain").count("worktree ") == 1
    dirty = set(git("diff", "--name-only").splitlines()) | set(
        git("ls-files", "--others", "--exclude-standard").splitlines()
    )
    assert dirty == set(FILES), sorted(dirty ^ set(FILES))
    files = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}
    fingerprint = hashlib.sha256(
        json.dumps({"baseline": BASELINE, "files": files}, sort_keys=True).encode()
    ).hexdigest()
    return {"baseline": BASELINE, "files": files, "fingerprint": fingerprint}


def main() -> None:
    p = ROOT / "automation/evidence/ISI-29E"
    report = json.loads((p / "acceptance.json").read_text())
    assert report["status"] == "PASS" and report["candidate"] == manifest()
    assert len(report["gates"]) == 8
    assert set(report["xml_sha256"]) == {"focused.xml", "native.xml", "regression.xml"}
    browser = json.loads((p / "browser-verification.json").read_text())
    assert browser["status"] == "PASS" and browser["candidate"] == manifest()
    for name, sha in browser["files"].items():
        assert hashlib.sha256((p / name).read_bytes()).hexdigest() == sha
    for gate in report["gates"]:
        assert gate["returncode"] == 0
        assert hashlib.sha256((p / gate["log"]).read_bytes()).hexdigest() == gate["sha256"]
    for name, sha in report["xml_sha256"].items():
        assert hashlib.sha256((p / name).read_bytes()).hexdigest() == sha
        suites = ET.parse(p / name).getroot().iter("testsuite")
        count = 0
        for suite in suites:
            count += int(suite.get("tests", "0"))
            assert int(suite.get("failures", "0")) == int(suite.get("errors", "0")) == 0
            if name in {"focused.xml", "native.xml"}:
                assert int(suite.get("skipped", "0")) == 0
        assert count > 0
    print(json.dumps({"status": "PASS", "candidate": manifest(), "server": "DEFERRED_SERVER_VERIFICATION"}, indent=2))


if __name__ == "__main__":
    main()
