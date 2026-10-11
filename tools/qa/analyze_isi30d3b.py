"""Read-only exact-candidate analyzer. Never invokes an implementation agent."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "eabdc3f30ceaa53286a4700ecef9d2d18fbfa44a"
FILES = (
    "automation/specs/ISI-30D3B-REPORTING-WORKFLOWS.md",
    "src/platform/reporting/schemas.py",
    "src/api/reporting_routes.py",
    "src/streamlit_app/reporting_api.py",
    "src/streamlit_app/reporting_workspace.py",
    "src/streamlit_app/linked_reporting_workspace.py",
    "tests/test_isi_30d3b_reporting_workflows.py",
    "tests/test_isi_29f_api_ui.py",
    "tools/qa/run_isi30d3b.py",
    "tools/qa/analyze_isi30d3b.py",
    "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md",
    "TECHNICAL_DOCUMENTATION.md",
    "automation/STATUS.md",
    "automation/tasks.json",
    "docs/help/ISI-REPORTING-WORKFLOWS-GUIDE.md",
    "docs/help/ISI-HELP-COVERAGE-MATRIX.md",
)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def manifest():
    assert git("branch", "--show-current") == "main"
    assert git("rev-parse", "HEAD") == git("rev-parse", "origin/main") == BASELINE
    assert not git("diff", "--cached", "--name-only") and not git("stash", "list")
    assert git("worktree", "list", "--porcelain").count("worktree ") == 1
    dirty = set(git("diff", "--name-only").splitlines()) | set(
        git("ls-files", "--others", "--exclude-standard").splitlines()
    )
    assert dirty == set(FILES), sorted(dirty ^ set(FILES))
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}
    fingerprint = hashlib.sha256(
        json.dumps({"baseline": BASELINE, "files": hashes}, sort_keys=True).encode()
    ).hexdigest()
    return {"baseline": BASELINE, "files": hashes, "fingerprint": fingerprint}


def analyze(*, local_only=False):
    folder = ROOT / "automation/evidence/ISI-30D3B"
    report = json.loads((folder / "acceptance.json").read_text())
    assert report["candidate"] == manifest() and report["status"] == "LOCAL_GATES_PASS"
    assert len(report["gates"]) == 7
    for gate in report["gates"]:
        assert gate["returncode"] == 0
        assert Path(gate["log"]).name == gate["log"]
        assert hashlib.sha256((folder / gate["log"]).read_bytes()).hexdigest() == gate["sha256"]
    for name, digest in report["xml_sha256"].items():
        assert Path(name).name == name
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
        count = 0
        for suite in ET.parse(folder / name).getroot().iter("testsuite"):
            assert int(suite.get("failures", "0")) == int(suite.get("errors", "0")) == 0
            if name == "focused.xml":
                assert int(suite.get("skipped", "0")) == 0
            count += int(suite.get("tests", "0"))
        assert count > 0
    if local_only:
        return {
            "status": "LOCAL_REVIEW_PASS_ONLY",
            "candidate": manifest(),
            "required_remaining": ["browser screenshots/keyboard/mobile", "assistant exact review"],
            "implemented": False,
            "ci_verified": False,
            "server_verified": False,
        }
    browser = json.loads((folder / "browser-verification.json").read_text())
    assert browser["status"] == "PASS" and browser["candidate"] == manifest()
    assert {1280, 390}.issubset(set(browser["widths"])) and browser["keyboard"] and not browser["overflow"]
    assert browser["files"]
    for name, digest in browser["files"].items():
        assert Path(name).name == name
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
    return {"status": "PASS", "candidate": manifest(), "ci_verified": False, "server_verified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(analyze(local_only=args.local_only), indent=2))
