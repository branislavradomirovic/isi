import json
from pathlib import Path

from tools.performance.workloads import catalogue


def test_r1_authority_and_formal_coverage_gate_reconciliation():
    tasks = {t["id"]: t for t in json.loads(Path("automation/tasks.json").read_text())["tasks"]}
    parent = tasks["ISI-26-PERFORMANCE-LOAD-RESILIENCE"]
    assert parent["spec"].endswith("ISI-26-R1-FULL-PERFORMANCE-LOAD-RESILIENCE.md")
    assert parent["phase_status"] == "IN PROGRESS / R1 FULL IMPLEMENTATION CANDIDATE"
    expected = {
        "ISI-26A-PERFORMANCE-CONTRACT-DETERMINISTIC-HARNESS": ("spec_ready", "ISI-26B-API-AUTH-READINESS-LOAD-RESILIENCE"),
        "ISI-26B-API-AUTH-READINESS-LOAD-RESILIENCE": ("planned", "ISI-26C-DATA-ANALYTICS-REPORTING-SCALE"),
        "ISI-26C-DATA-ANALYTICS-REPORTING-SCALE": ("planned", "ISI-26D-AI-CONCURRENCY-RESILIENCE"),
        "ISI-26D-AI-CONCURRENCY-RESILIENCE": ("planned", "ISI-26E-PERFORMANCE-RESILIENCE-CLOSEOUT"),
    }
    for key, (status, nxt) in expected.items():
        task = tasks[key]
        assert task["status"] == status and task["next"] == nxt
        assert task["execution_group"] == "ISI-26-R1-FULL-PERFORMANCE-LOAD-RESILIENCE"
        assert task["coverage_status"] == "R1_CANDIDATE_COVERED"
        assert "superseded" not in task["note"].lower()
    closeout = tasks["ISI-26E-PERFORMANCE-RESILIENCE-CLOSEOUT"]
    assert closeout["status"] == "planned"
    assert closeout["depends_on"] == ["ISI-26D-AI-CONCURRENCY-RESILIENCE"]
    assert "whole-phase closeout gate" in closeout["note"]
    assert tasks["ISI-27-INDUSTRIAL-RELEASE-CANDIDATE"]["depends_on"] == [parent["id"]]
    for path in ("TECHNICAL_DOCUMENTATION.md", "automation/STATUS.md",
                 "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md"):
        text = Path(path).read_text()
        assert "R1 FULL IMPLEMENTATION CANDIDATE" in text
        assert "formal" in text.lower() and "coverage/gate" in text.lower()
        assert "ISI-28" in text and "Krcuga" in text and "OralScanXAI" in text
        assert "SUPERSEDED_BY_R1_FULL_SLICE" not in text


def test_local_evidence_boundaries_and_manual_ci():
    text = Path("docs/ops/ISI-26-PERFORMANCE-LOAD-RESILIENCE.md").read_text()
    for marker in ("PRODUCTION_CAPACITY_VERIFIED=false", "SERVER_VERIFIED=false", "STAGE_COMMIT_PUSH=NO",
                   "SERVER_MUTATION=NO", "GITHUB_ACTIONS_DISPATCH=NO", "UNCALIBRATED", "UNAVAILABLE"):
        assert marker in text
    workflow = Path(".github/workflows/ci.yml").read_text()
    assert "  workflow_dispatch:" in workflow
    assert all(f"  {trigger}:" not in workflow for trigger in ("push", "pull_request", "schedule"))
    assert all(w.environment == "LOCAL_REPOSITORY" for w in catalogue())
