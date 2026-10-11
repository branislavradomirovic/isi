"""Read-only exact-candidate analyzer. Never invokes an implementation agent."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "e3ac9c758044988b8cfb7df1ad0c2765701ade0b"
FILES = (
    "tests/test_isi_29a_xai_help_contract.py",
    "tests/test_isi_30c2b2_ordo_statistical_workflow.py",
    "tests/test_isi_30d2_ai_review_workflows.py",
    "tests/test_isi_30d3a_typed_result_views.py",
    "tests/test_isi_30d3b_reporting_workflows.py",
    "automation/specs/ISI-30E-ILLUSTRATED-HELP-MANUAL.md",
    "automation/contracts/ISI-30E-ASSET-PLAN.json",
    "docs/help/ISI-ILLUSTRATED-MANUAL.json",
    "src/streamlit_app/help_manual.py",
    "src/streamlit_app/shared_help_workspace.py",
    "src/streamlit_app/simpa_help_workspace.py",
    "src/streamlit_app/ordo_help_workspace.py",
    "docs/help/SIMPA-USER-GUIDE.md",
    "docs/help/ORDO-USER-GUIDE.md",
    "tools/docs/build_isi30e_help.py",
    "tools/docs/build_isi30e_manual.py",
    "tests/test_isi_30e_illustrated_workflows.py",
    "tools/qa/run_isi30e.py",
    "tools/qa/analyze_isi30e.py",
    "docs/help/ISI-30E-MANUAL-ARTIFACT.json",
    "docs/help/ISI-HELP-COVERAGE-MATRIX.md",
    "TECHNICAL_DOCUMENTATION.md",
    "automation/STATUS.md",
    "automation/tasks.json",
    "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md",
    "docs/help/ISI-SHARED-USER-GUIDE.md",
    "docs/help/screens/ISI-30A-desktop-simpa.jpg",
    "docs/help/screens/ISI-30A-desktop-ordo-scenarios.jpg",
    "docs/help/screens/ISI-30A-desktop-status-confirmation.jpg",
    "docs/help/screens/ISI-30A-mobile-sidebar.jpg",
    "docs/help/screens/ISI-30A-mobile-ordo-scenarios.jpg",
    "docs/help/screens/ISI-30A-mobile-review-form.jpg",
    "docs/help/screens/ISI-30B-mobile-version-created.jpg",
    "docs/help/screens/ISI-30B-mobile-readonly.jpg",
    "docs/help/screens/ISI-30B-mobile-retry.jpg",
    "docs/help/screens/ISI-30B-desktop-source.jpg",
    "docs/help/screens/ISI-30B-desktop-output.jpg",
    "docs/help/screens/ISI-30B-mobile-output.jpg",
    "docs/help/screens/ISI-30B-desktop-evaluation.jpg",
    "docs/help/screens/ISI-30B2-final-mobile-mapping.jpg",
    "docs/help/screens/ISI-30B2-final-desktop-policy-validation.jpg",
    "docs/help/screens/ISI-30B2-final-desktop-ingest-created.jpg",
    "docs/help/screens/ISI-30B2-final-desktop-mapping-created.jpg",
    "docs/help/screens/ISI-30B2-final-desktop-records-created.jpg",
    "docs/help/screens/ISI-30B2-final-desktop-policy-created.jpg",
    "docs/help/screens/ISI-30B2-final-mobile-connector.jpg",
    "docs/help/screens/ISI-30B2-final-mobile-ingest-created.jpg",
    "docs/help/screens/ISI-30B3-mobile-lifecycle.jpg",
    "docs/help/screens/ISI-30B3-desktop-snapshot.jpg",
    "docs/help/screens/ISI-30B3-desktop-registry.jpg",
    "docs/help/screens/ISI-30B3-mobile-confirmation.jpg",
    "docs/help/screens/ISI-30B3-mobile-feature.jpg",
    "docs/help/screens/ISI-30B3-desktop-contract.jpg",
    "docs/help/screens/ISI-30B3-desktop-feature-registry.jpg",
    "docs/help/screens/ISI-30B3-mobile-feature-lifecycle.jpg",
    "docs/help/screens/ISI-30B4A-desktop-backfill.jpg",
    "docs/help/screens/ISI-30B4A-mobile-resolve.jpg",
    "docs/help/screens/ISI-30B4A-mobile-requeue.jpg",
    "docs/help/screens/ISI-30B4A-desktop-replay.jpg",
    "docs/help/screens/ISI-30B4B-mobile-confirmation.jpg",
    "docs/help/screens/ISI-30B4B-desktop-record-comparison.jpg",
    "docs/help/screens/ISI-30B4B-mobile-record-decision.jpg",
    "docs/help/screens/ISI-30B4B-desktop-profile.jpg",
    "docs/help/screens/ISI-30B4C-mobile-proposal.jpg",
    "docs/help/screens/ISI-30B4C-mobile-read-only.jpg",
    "docs/help/screens/ISI-30B4C-desktop-hold.jpg",
    "docs/help/screens/ISI-30B4C-desktop-export.jpg",
    "docs/help/screens/ISI-30B4C-mobile-export.jpg",
    "docs/help/screens/ISI-30C1-mobile-statistical.jpg",
    "docs/help/screens/ISI-30C1-desktop-review.jpg",
    "docs/help/screens/ISI-30C1-mobile-review.jpg",
    "docs/help/screens/ISI-30C1-desktop-draft.jpg",
    "docs/help/screens/ISI-30C2A-desktop-authoring-final.jpg",
    "docs/help/screens/ISI-30C2A-desktop-forecast-final.jpg",
    "docs/help/screens/ISI-30C2A-desktop-review-final.jpg",
    "docs/help/screens/ISI-30C2A-desktop-validated-final.jpg",
    "docs/help/screens/ISI-30C2A-mobile-authoring-final.jpg",
    "docs/help/screens/ISI-30C2A-mobile-readonly-final.jpg",
    "docs/help/screens/ISI-30C2A-mobile-validation-final.jpg",
    "docs/help/screens/ISI-30C2B1-desktop-explicit-inputs.jpg",
    "docs/help/screens/ISI-30C2B1-mobile-readonly.jpg",
    "docs/help/screens/ISI-30C2B1-mobile-reset.jpg",
    "docs/help/screens/ISI-30C2B1-desktop-review.jpg",
    "docs/help/screens/ISI-30C2B1-mobile-review.jpg",
    "docs/help/screens/ISI-30C2B1-desktop-success.jpg",
    "docs/help/screens/ISI-30C2B2-mobile-success-reset.jpg",
    "docs/help/screens/ISI-30C2B2-mobile-readonly.jpg",
    "docs/help/screens/ISI-30C2B2-desktop-authoring-fields.jpg",
    "docs/help/screens/ISI-30C2B2-desktop-success-reset.jpg",
    "docs/help/screens/ISI-30C2B2-desktop-authoring-success.jpg",
    "docs/help/screens/ISI-30C2B2-desktop-specification.jpg",
    "docs/help/screens/ISI-30C2B2-mobile-review-confirmation.jpg",
    "docs/help/screens/ISI-30D1-desktop-confirmation.jpg",
    "docs/help/screens/ISI-30D1-desktop-readonly.jpg",
    "docs/help/screens/ISI-30D1-desktop-review.jpg",
    "docs/help/screens/ISI-30D1-desktop-session-review.jpg",
    "docs/help/screens/ISI-30D1-desktop-success.jpg",
    "docs/help/screens/ISI-30D1-mobile-actions.jpg",
    "docs/help/screens/ISI-30D1-mobile-invitation.jpg",
    "docs/help/screens/ISI-30D1-mobile-session-review.jpg",
    "docs/help/screens/ISI-30D1-mobile-workspace.jpg",
    "docs/help/screens/ISI-30D2-desktop-readonly-boundaries.jpg",
    "docs/help/screens/ISI-30D2-mobile-xai-boundaries.jpg",
    "docs/help/screens/ISI-30D2-desktop-ai-overview.jpg",
    "docs/help/screens/ISI-30D2-mobile-review-success.jpg",
    "docs/help/screens/ISI-30D2-desktop-job-xai.jpg",
    "docs/help/screens/ISI-30D3A-desktop-forecast.jpg",
    "docs/help/screens/ISI-30D3A-desktop-not-estimated.jpg",
    "docs/help/screens/ISI-30D3A-desktop-citations.jpg",
    "docs/help/screens/ISI-30D3A-desktop-interval.jpg",
    "docs/help/screens/ISI-30D3A-desktop-shap.jpg",
    "docs/help/screens/ISI-30D3A-mobile-shap.jpg",
    "docs/help/screens/ISI-30D3A-mobile-citations.jpg",
    "docs/help/screens/ISI-30D3B-desktop-explicit-selection.jpg",
    "docs/help/screens/ISI-30D3B-desktop-linked-inputs.jpg",
    "docs/help/screens/ISI-30D3B-desktop-draft-evidence.jpg",
    "docs/help/screens/ISI-30D3B-desktop-review-confirmation.jpg",
    "docs/help/screens/ISI-30D3B-desktop-publish-confirmation.jpg",
    "docs/help/screens/ISI-30D3B-desktop-export.jpg",
    "docs/help/screens/ISI-30D3B-mobile-export.jpg",
    "docs/help/screens/ISI-30D3B-mobile-readonly.jpg",
    "docs/help/screens/ISI-30D3B-mobile-ordo-context.jpg",
    "docs/help/screens/ISI-30D4-desktop-inventory.jpg",
    "docs/help/screens/ISI-30D4-desktop-confirmation.jpg",
    "docs/help/screens/ISI-30D4-desktop-receipt.jpg",
    "docs/help/screens/ISI-30D4-mobile-assurance-form.jpg",
    "docs/help/screens/ISI-30D4-mobile-receipt.jpg",
    "docs/help/ISI-WORKFLOW-SHELL-GUIDE.md",
    "docs/help/ISI-DATA-WORKFLOWS-GUIDE.md",
    "docs/help/ISI-GOVERNED-INGESTION-GUIDE.md",
    "docs/help/ISI-ANALYTICAL-AUTHORING-GUIDE.md",
    "docs/help/ISI-INGESTION-RECOVERY-GUIDE.md",
    "docs/help/ISI-SOURCE-GOVERNANCE-GUIDE.md",
    "docs/help/ISI-PRIVACY-CONTROLS-GUIDE.md",
    "docs/help/SIMPA-METHODOLOGY-WORKFLOWS-GUIDE.md",
    "docs/help/ORDO-METHODOLOGY-WORKFLOWS-GUIDE.md",
    "docs/help/ORDO-SPATIAL-AGGREGATION-GUIDE.md",
    "docs/help/ORDO-STATISTICAL-SPECIFICATION-GUIDE.md",
    "docs/help/ISI-ADMINISTRATION-WORKFLOWS-GUIDE.md",
    "docs/help/ISI-AI-REVIEW-WORKFLOWS-GUIDE.md",
    "docs/help/ISI-RESULT-EVIDENCE-GUIDE.md",
    "docs/help/ISI-REPORTING-WORKFLOWS-GUIDE.md",
    "docs/help/ISI-ACCOUNT-SECURITY-WORKFLOWS-GUIDE.md",
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
    folder = ROOT / "automation/evidence/ISI-30E"
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
    layout = json.loads((folder / "word-layout-review.json").read_text())
    artifact = json.loads((ROOT / "docs/help/ISI-30E-MANUAL-ARTIFACT.json").read_text())
    assert layout["status"] == "PASS" and layout["docx_sha256"] == artifact["sha256"]
    assert set(map(int, layout["pages"])) == set(range(1, artifact["page_count"] + 1))
    assert hashlib.sha256((folder / artifact["filename"]).read_bytes()).hexdigest() == artifact["sha256"]
    for page, digest in layout["pages"].items():
        assert (
            hashlib.sha256((folder / "render-shap-corrected" / f"page-{page}.png").read_bytes()).hexdigest() == digest
        )
    return {"status": "PASS", "candidate": manifest(), "ci_verified": False, "server_verified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(analyze(local_only=args.local_only), indent=2))
