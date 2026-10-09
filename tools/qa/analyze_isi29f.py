"""Read-only exact-candidate analyzer; no implementation/CI/server invocation."""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "33e86e6e99179f8572bc180b377cee7ca57be8a0"
FILES = ('TECHNICAL_DOCUMENTATION.md', 'automation/STATUS.md', 'automation/tasks.json', 'docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md', 'docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md', 'docs/help/ISI-HELP-COVERAGE-MATRIX.md', 'docs/help/ISI-LINKED-REPORTS-GUIDE.md', 'automation/specs/ISI-29F-EVIDENCE-RELEASE.md', 'src/platform/reporting/schemas.py', 'src/platform/reporting/linked_evidence.py', 'src/domains/simpa/report_evidence.py', 'src/domains/ordo/report_evidence.py', 'src/api/reporting_routes.py', 'src/streamlit_app/reporting_api.py', 'src/streamlit_app/reporting_workspace.py', 'src/streamlit_app/linked_reporting_workspace.py', 'tests/test_isi_29f_linked_reports.py', 'tests/test_isi_29f_api_ui.py', 'tests/test_isi_29f_numerical_evidence.py', 'tools/qa/run_isi29f.py', 'tools/qa/analyze_isi29f.py', 'src/streamlit_app/help_manual.py', 'src/streamlit_app/shared_help_workspace.py', 'src/streamlit_app/simpa_help_workspace.py', 'src/streamlit_app/ordo_help_workspace.py', 'docs/help/ISI-ILLUSTRATED-MANUAL.json', 'tests/test_isi_29f_illustrated_help.py', 'docs/help/screens/ISI-29C-ordo-desktop.jpg', 'docs/help/screens/ISI-29C-simpa-desktop.jpg', 'docs/help/screens/ISI-29C-simpa-mobile.jpg', 'docs/help/screens/ISI-29D-desktop-matrix.jpg', 'docs/help/screens/ISI-29D-desktop-waterfall.jpg', 'docs/help/screens/ISI-29D-mobile-invalid.jpg', 'docs/help/screens/ISI-29E-desktop-review.jpg', 'docs/help/screens/ISI-29E-desktop-source.jpg', 'docs/help/screens/ISI-29E-mobile-review.jpg', 'docs/help/screens/ISI-29F-desktop-approved.jpg', 'docs/help/screens/ISI-29F-desktop-export.jpg', 'docs/help/screens/ISI-29F-desktop-form.jpg', 'docs/help/screens/ISI-29F-desktop-map.jpg', 'docs/help/screens/ISI-29F-desktop-review.jpg', 'docs/help/screens/ISI-29F-mobile-ordo-map.jpg', 'docs/help/screens/screenshots-admin-overview.jpg', 'docs/help/screens/screenshots-data.jpg', 'docs/help/screens/screenshots-help-invitation.jpg', 'docs/help/screens/screenshots-login-recovery.jpg', 'docs/help/screens/screenshots-login.jpg', 'docs/help/screens/screenshots-ordo-analysis.jpg', 'docs/help/screens/screenshots-ordo-forecast.jpg', 'docs/help/screens/screenshots-ordo-goal.jpg', 'docs/help/screens/screenshots-ordo-help.jpg', 'docs/help/screens/screenshots-ordo-indicators.jpg', 'docs/help/screens/screenshots-ordo-overview.jpg', 'docs/help/screens/screenshots-public-help.jpg', 'docs/help/screens/screenshots-public-home.jpg', 'docs/help/screens/screenshots-reports.jpg', 'docs/help/screens/screenshots-security.jpg', 'docs/help/screens/screenshots-shared-help.jpg', 'docs/help/screens/screenshots-simpa-analysis.jpg', 'docs/help/screens/screenshots-simpa-cycle.jpg', 'docs/help/screens/screenshots-simpa-indicators.jpg', 'docs/help/screens/screenshots-simpa-overview.jpg', 'docs/help/screens/screenshots-simpa-profile.jpg', 'docs/help/screens/screenshots-simpa-statistics.jpg')


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
    p = ROOT / "automation/evidence/ISI-29F"
    report = json.loads((p / "acceptance.json").read_text())
    assert report["status"] == "PASS" and report["candidate"] == manifest()
    assert len(report["gates"]) == 8
    assert set(report["xml_sha256"]) == {"focused.xml", "native.xml", "regression.xml"}
    browser = json.loads((p / "browser-verification.json").read_text())
    assert browser["status"] == "PASS" and browser["candidate"] == manifest()
    for name, sha in browser["files"].items():
        assert hashlib.sha256((p / name).read_bytes()).hexdigest() == sha
    manual = json.loads((p / "manual-verification.json").read_text())
    assert manual["status"] == "PASS" and manual["candidate"] == manifest()
    assert manual["pages_visually_reviewed"] == list(range(1, manual["pages_rendered"] + 1))
    assert hashlib.sha256(Path(manual["output_path"]).read_bytes()).hexdigest() == manual["output_sha256"]
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
    print(json.dumps({"status": "PASS", "candidate": manifest(), "server": "PENDING_EXACT_MAIN_RELEASE_CHECKPOINT"}, indent=2))


if __name__ == "__main__":
    main()
