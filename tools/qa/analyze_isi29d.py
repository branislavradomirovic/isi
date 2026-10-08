"""Read-only exact-candidate analyzer; no implementation/CI/server invocation."""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "a77f9f0b4e43038554ee203a0c5ad22cd0b9e981"
FILES = (
    "TECHNICAL_DOCUMENTATION.md",
    "automation/STATUS.md",
    "automation/tasks.json",
    "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md",
    "docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md",
    "docs/help/ISI-HELP-COVERAGE-MATRIX.md",
    "docs/help/ISI-SHAP-GUIDE.md",
    "automation/specs/ISI-29D-MODEL-ATTRIBUTION.md",
    "src/domains/simpa/analytics_models.py",
    "src/domains/simpa/statistical_attribution.py",
    "src/domains/simpa/attribution_service.py",
    "src/api/simpa_analytics_routes.py",
    "src/streamlit_app/simpa_analytics_api.py",
    "src/streamlit_app/simpa_analytics_workspace.py",
    "src/streamlit_app/attribution_view.py",
    "migrations/versions/20261008_0036_simpa_attribution.py",
    "tests/test_isi_29d_attribution_engine.py",
    "tests/test_isi_29d_attribution_service.py",
    "tests/test_isi_29d_attribution_ui_api.py",
    "tests/test_isi_29d_native_postgres.py",
    "tools/qa/run_isi29d.py",
    "tools/qa/analyze_isi29d.py",
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
    p = ROOT / "automation/evidence/ISI-29D"
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
