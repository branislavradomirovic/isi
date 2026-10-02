import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_corrected_b0_r1a_and_four_gate_scope_are_locked():
    ev=json.loads((ROOT/"automation/specs/ISI-27-B0-R1A-BOOTSTRAP-AUDIT-EVIDENCE.json").read_text())
    assert ev["counts"]=={"DONE":6,"DRIFT":0,"MISSING":5,"PARTIAL":8}
    assert ev["release_blockers_not_done"]==13
    assert len(ev["help_release_blockers"])==12
    by={x["id"]:x for x in ev["findings"]}
    assert by["B0-13"]["status"]=="MISSING"
    tasks={x["id"]:x for x in json.loads((ROOT/"automation/tasks.json").read_text())["tasks"]}
    parent=tasks["ISI-27-INDUSTRIAL-RELEASE-CANDIDATE"]
    assert parent["status"]=="in_progress"
    assert parent["active_checkpoint"]=="ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS"
    chain=[
      ("ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS","spec_ready","ISI-27B-RC-EVIDENCE-GOVERNANCE-PACK"),
      ("ISI-27B-RC-EVIDENCE-GOVERNANCE-PACK","planned","ISI-27C-REPRODUCIBLE-RELEASE-SUPPLY-CHAIN-ASSURANCE"),
      ("ISI-27C-REPRODUCIBLE-RELEASE-SUPPLY-CHAIN-ASSURANCE","planned","ISI-27D-EXACT-MAIN-RC-ACCEPTANCE-CLOSEOUT"),
      ("ISI-27D-EXACT-MAIN-RC-ACCEPTANCE-CLOSEOUT","planned","ISI-28-CURRENT-SERVER-CONTROLLED-UPGRADE"),
    ]
    for key,status,nxt in chain:
        assert tasks[key]["status"]==status
        assert tasks[key]["next"]==nxt
    assert tasks["ISI-28-CURRENT-SERVER-CONTROLLED-UPGRADE"]["status"]=="deferred"

def test_scope_docs_preserve_release_and_server_boundaries():
    spec=(ROOT/"automation/specs/ISI-27-SCOPE-LOCK.md").read_text()
    status=(ROOT/"automation/STATUS.md").read_text()
    master=(ROOT/"docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    tech=(ROOT/"TECHNICAL_DOCUMENTATION.md").read_text()
    for text in (spec,status,master,tech):
        assert "27A" in text and "27B" in text and "27C" in text and "27D" in text
        assert "ISI-28" in text
    assert "workflow_dispatch" in spec and "release-candidate" in spec
    assert "must not create public signup" in spec
    assert "automatic github actions triggers remain forbidden" in spec.casefold()
    workflow=(ROOT/".github/workflows/ci.yml").read_text()
    assert "  workflow_dispatch:" in workflow
    for trigger in ("push","pull_request","schedule","workflow_run"):
        assert f"  {trigger}:" not in workflow

def test_scope_lock_is_governance_only():
    spec=(ROOT/"automation/specs/ISI-27-SCOPE-LOCK.md").read_text()
    for marker in ("No runtime, dependency, migration, Compose, Docker, workflow, deployment or server path may change",
                   "No Codex call is authorized for the scope lock"):
        assert marker in spec


def test_r2_review_recovery_records_final_surface_and_live_handoff():
    spec=(ROOT/"automation/specs/ISI-27-SCOPE-LOCK.md").read_text()
    status=(ROOT/"automation/STATUS.md").read_text()
    tech=(ROOT/"TECHNICAL_DOCUMENTATION.md").read_text()
    master=(ROOT/"docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    assert "R1 governance-convergence recovery" in spec
    assert "exact 10-path final surface" in spec
    assert "tests/test_isi_17_harness_contract.py" in spec
    assert "tests/test_isi_26_governance_contract.py" in spec
    assert "The next action is a fresh ISI-27 bootstrap/audit" not in status
    assert "ISI-27 is current/next for a fresh Industrial Release Candidate bootstrap" not in tech
    assert "ISI-27 is current/next for a fresh bootstrap/audit" not in master
    for text in (status, tech, master):
        assert "27A" in text and "scope" in text.casefold()
    live_tasks=(ROOT/"automation/tasks.json").read_text()
    for text in (status, tech, master, live_tasks):
        assert "fresh release-candidate bootstrap" not in text.casefold()
