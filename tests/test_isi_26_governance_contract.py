import json
from pathlib import Path

from tools.performance.workloads import catalogue


def test_26e_closeout_accepts_r1_and_formal_coverage_gates():
    tasks = {t["id"]: t for t in json.loads(Path("automation/tasks.json").read_text())["tasks"]}
    parent = tasks["ISI-26-PERFORMANCE-LOAD-RESILIENCE"]
    assert parent["status"] == "done"
    assert parent["phase_status"] == "IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED"
    assert parent["spec"].endswith("ISI-26E-PERFORMANCE-RESILIENCE-CLOSEOUT.md")
    assert parent["accepted_main_sha"] == "e4b5b7f5927bc553fd616800d37beb5d115bb46e"
    assert parent["accepted_main_tree"] == "9a30b280ba44798b987167c155f0be6ccc13776e"
    assert parent["accepted_candidate_fingerprint"] == "98653d20a5223d4f6be66f3ee2017f998865b00ecb08a0950c07123d60dc2e24"
    expected = {
        "ISI-26A-PERFORMANCE-CONTRACT-DETERMINISTIC-HARNESS": "ISI-26B-API-AUTH-READINESS-LOAD-RESILIENCE",
        "ISI-26B-API-AUTH-READINESS-LOAD-RESILIENCE": "ISI-26C-DATA-ANALYTICS-REPORTING-SCALE",
        "ISI-26C-DATA-ANALYTICS-REPORTING-SCALE": "ISI-26D-AI-CONCURRENCY-RESILIENCE",
        "ISI-26D-AI-CONCURRENCY-RESILIENCE": "ISI-26E-PERFORMANCE-RESILIENCE-CLOSEOUT",
    }
    for key, nxt in expected.items():
        task = tasks[key]
        assert task["status"] == "done" and task["next"] == nxt
        assert task["execution_group"] == "ISI-26-R1-FULL-PERFORMANCE-LOAD-RESILIENCE"
        assert task["coverage_status"] == "ACCEPTED_THROUGH_R1"
    closeout = tasks["ISI-26E-PERFORMANCE-RESILIENCE-CLOSEOUT"]
    assert closeout["status"] == "done"
    assert closeout["spec"].endswith("ISI-26E-PERFORMANCE-RESILIENCE-CLOSEOUT.md")
    assert closeout["coverage_status"] == "CLOSEOUT_COMPLETE"
    phase27 = tasks["ISI-27-INDUSTRIAL-RELEASE-CANDIDATE"]
    assert phase27["status"] == "in_progress"
    assert phase27["active_checkpoint"] == "ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS"
    assert tasks["ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS"]["status"] == "spec_ready"
    assert tasks["ISI-27-INDUSTRIAL-RELEASE-CANDIDATE"]["depends_on"] == [parent["id"]]
    for path in ("TECHNICAL_DOCUMENTATION.md", "automation/STATUS.md",
                 "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md"):
        body = Path(path).read_text()
        assert "IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED" in body
        assert "e4b5b7f5927bc553fd616800d37beb5d115bb46e" in body
        assert "ISI-27" in body and "ISI-28" in body

def test_local_evidence_boundaries_and_manual_ci():
    text = Path("docs/ops/ISI-26-PERFORMANCE-LOAD-RESILIENCE.md").read_text()
    for marker in ("PRODUCTION_CAPACITY_VERIFIED=NO", "SERVER_VERIFIED=NO", "R1_STAGE_COMMIT_PUSH=PASS",
                   "R1_REMOTE_EQUALITY=PASS", "SERVER_MUTATION=NO", "GITHUB_ACTIONS_DISPATCH=NO",
                   "CI_VERIFIED=NO", "UNCALIBRATED", "UNAVAILABLE"):
        assert marker in text
    evidence = json.loads(Path("automation/specs/ISI-26E-PERFORMANCE-RESILIENCE-CLOSEOUT-EVIDENCE.json").read_text())
    assert evidence["r1_accepted_main_sha"] == "e4b5b7f5927bc553fd616800d37beb5d115bb46e"
    assert evidence["r1_accepted_main_tree"] == "9a30b280ba44798b987167c155f0be6ccc13776e"
    assert evidence["r1_candidate_fingerprint"] == "98653d20a5223d4f6be66f3ee2017f998865b00ecb08a0950c07123d60dc2e24"
    assert evidence["human_review"] == "PASS" and evidence["independent_analysis"] == "PASS"
    assert evidence["open_remove_before_next_slice"] == []
    assert evidence["ci_verified"] is False
    assert evidence["production_capacity_verified"] is False
    assert evidence["server_verified"] is False
    workflow = Path(".github/workflows/ci.yml").read_text()
    assert "  workflow_dispatch:" in workflow
    assert all(f"  {trigger}:" not in workflow for trigger in ("push", "pull_request", "schedule"))
    assert all(w.environment == "LOCAL_REPOSITORY" for w in catalogue())
