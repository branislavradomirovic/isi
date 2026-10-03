import json
import hashlib
import re
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]

HISTORY_HEADING = "### 2026-10-01 ISI-25B closure and shared-ingress governance reconciliation"
HISTORY_SHA256 = "52747042e67f3c21fb8a8b2be10f8a91688fcbba9833a621ad9e06605211bb87"
CURRENT_POINTER = "ISI-27A is accepted on main and 27B is current"
STALE24 = "ISI-27 B0-R1A bootstrap is closed, scope is locked, and 27A is current."
STALE25 = "ISI-27 B0-R1A bootstrap is closed with scope locked and 27A current"
ACCEPTED_MAIN = "74acd5d9a890733347554633f44a6d5319717ba3"


def _closeout_section(text, heading):
    matches = list(re.finditer(r"(?m)^" + re.escape(heading) + r"$", text))
    assert len(matches) == 1, f"Expected one section: {heading}"
    match = matches[0]
    level = len(heading.split(" ", 1)[0])
    boundary = re.search(r"(?m)^#{1," + str(level) + r"} ", text[match.end():])
    end = match.end() + boundary.start() if boundary else len(text)
    return text[match.start():end]


def _assert_closeout_live_pointers(master, live_tasks, status, tech):
    history = _closeout_section(master, HISTORY_HEADING)
    owner_history = _closeout_section(master, "## 11. Owner approval record")
    assert history in owner_history, "Dated history escaped the owner-approval ledger"
    assert hashlib.sha256(history.encode("utf-8")).hexdigest() == HISTORY_SHA256, "Dated history changed"
    assert history.count(STALE24) == 1
    assert master.count(STALE24) == 1, "Historical pointer was duplicated into live text"
    outside_history = master.replace(history, "", 1)
    assert STALE24 not in outside_history
    assert STALE25 not in outside_history
    for heading in ("### ISI-24 - ORDO Production Methodology", "### ISI-25 - Industrial AI / MLOps"):
        live = _closeout_section(master, heading)
        assert CURRENT_POINTER in live, f"Missing accepted-27A/current-27B pointer in {heading}"
        assert STALE24 not in live and STALE25 not in live
    inventory = [line for line in master.splitlines() if line.startswith("| INV-A21 |")]
    assert len(inventory) == 1
    assert "VERIFIED in the accepted ISI-27A implementation" in inventory[0]
    assert "local 27A candidate" not in inventory[0]
    entries = json.loads(live_tasks)["tasks"]
    tasks = {item["id"]: item for item in entries}
    assert len(tasks) == len(entries), "Duplicate task identity"
    for key in ("ISI-25-INDUSTRIAL-AI-MLOPS", "ISI-26-PERFORMANCE-LOAD-RESILIENCE"):
        note = tasks[key]["note"]
        assert CURRENT_POINTER in note, f"Stale predecessor note: {key}"
        assert "27A is current" not in note and "ISI-26 is current/next" not in note
    assert tasks["ISI-27-INDUSTRIAL-RELEASE-CANDIDATE"]["active_checkpoint"] == "ISI-27B-RC-EVIDENCE-GOVERNANCE-PACK"
    assert tasks["ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS"]["status"] == "done"
    assert tasks["ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS"]["accepted_main_sha"] == ACCEPTED_MAIN
    assert tasks["ISI-27B-RC-EVIDENCE-GOVERNANCE-PACK"]["status"] == "spec_ready"
    assert tasks["ISI-27C-REPRODUCIBLE-RELEASE-SUPPLY-CHAIN-ASSURANCE"]["status"] == "planned"
    assert tasks["ISI-27D-EXACT-MAIN-RC-ACCEPTANCE-CLOSEOUT"]["status"] == "planned"
    assert tasks["ISI-28-CURRENT-SERVER-CONTROLLED-UPGRADE"]["status"] == "deferred"
    summaries = [line for line in status.splitlines() if line.startswith("Overall `ISI-26-PERFORMANCE-LOAD-RESILIENCE`")]
    assert len(summaries) == 1
    assert "ISI-27A is accepted on main" in summaries[0]
    assert "current next action is `ISI-27B - RC Evidence & Governance Pack`" in summaries[0]
    help_summary = _closeout_section(tech, "## 15. Help, User Guide and XAI governance")
    assert "Shared Help/presentation is accepted on main" in help_summary
    assert ACCEPTED_MAIN in help_summary
    assert "NOT CI_VERIFIED" in help_summary
    assert "local ISI-27A candidate" not in help_summary


NEGATIVE_CASES = (
    "phase24", "phase25", "task25", "task26", "outside_history",
    "history_deleted", "history_altered", "history_duplicated", "history_renamed",
    "history_pointer_moved", "history_outside_owner", "phase24_missing",
    "phase24_duplicated", "phase25_missing", "inventory_candidate", "status_next27a",
    "technical_candidate", "parent27a", "27b_planned", "27c_promoted", "28_enabled",
)


def _closeout_negative_case(case, documents):
    changed = dict(documents)
    master = changed["master"]
    if case in ("phase24", "phase25"):
        heading = "### ISI-24 - ORDO Production Methodology" if case == "phase24" else "### ISI-25 - Industrial AI / MLOps"
        section = _closeout_section(master, heading)
        stale = STALE24 if case == "phase24" else STALE25
        changed["master"] = master.replace(section, section.replace(CURRENT_POINTER, stale, 1), 1)
    elif case in ("task25", "task26", "parent27a", "27b_planned", "27c_promoted", "28_enabled"):
        data = json.loads(changed["tasks"])
        tasks = {item["id"]: item for item in data["tasks"]}
        if case == "task25":
            tasks["ISI-25-INDUSTRIAL-AI-MLOPS"]["note"] = "ISI-26 is current/next."
        elif case == "task26":
            tasks["ISI-26-PERFORMANCE-LOAD-RESILIENCE"]["note"] = "27A is current."
        elif case == "parent27a":
            tasks["ISI-27-INDUSTRIAL-RELEASE-CANDIDATE"]["active_checkpoint"] = "ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS"
        elif case == "27b_planned":
            tasks["ISI-27B-RC-EVIDENCE-GOVERNANCE-PACK"]["status"] = "planned"
        elif case == "27c_promoted":
            tasks["ISI-27C-REPRODUCIBLE-RELEASE-SUPPLY-CHAIN-ASSURANCE"]["status"] = "done"
        else:
            tasks["ISI-28-CURRENT-SERVER-CONTROLLED-UPGRADE"]["status"] = "spec_ready"
        changed["tasks"] = json.dumps(data)
    elif case == "outside_history":
        changed["master"] += "\n" + STALE24 + "\n"
    elif case.startswith("history_"):
        history = _closeout_section(master, HISTORY_HEADING)
        if case == "history_deleted":
            changed["master"] = master.replace(history, "", 1)
        elif case == "history_altered":
            changed["master"] = master.replace(history, history.replace("central-ingress-nginx-1", "changed-edge", 1), 1)
        elif case == "history_duplicated":
            changed["master"] += history
        elif case == "history_renamed":
            changed["master"] = master.replace(HISTORY_HEADING, HISTORY_HEADING + " moved", 1)
        elif case == "history_pointer_moved":
            changed["master"] = master.replace(history, history.replace(STALE24, "", 1), 1) + "\n" + STALE24 + "\n"
        elif case == "history_outside_owner":
            changed["master"] = master.replace(history, "", 1) + "\n## Unscoped area\n\n" + history
        else:
            raise AssertionError(f"Unknown historical negative case: {case}")
    elif case in ("phase24_missing", "phase24_duplicated", "phase25_missing"):
        heading = "### ISI-25 - Industrial AI / MLOps" if case == "phase25_missing" else "### ISI-24 - ORDO Production Methodology"
        if case == "phase24_duplicated":
            changed["master"] += "\n" + heading + "\n"
        else:
            changed["master"] = master.replace(heading, heading + " renamed", 1)
    elif case == "inventory_candidate":
        changed["master"] = master.replace("VERIFIED in the accepted ISI-27A implementation", "VERIFIED in the local 27A candidate", 1)
    elif case == "status_next27a":
        changed["status"] = changed["status"].replace("current next action is `ISI-27B - RC Evidence & Governance Pack`", "current next action is `ISI-27A - Shared Help & Release UX Completeness`", 1)
    elif case == "technical_candidate":
        changed["tech"] = changed["tech"].replace("Shared Help/presentation is accepted on main", "Shared Help/presentation has a local ISI-27A candidate", 1)
    else:
        raise AssertionError(f"Unknown negative case: {case}")
    assert changed != documents, f"Negative control did not mutate: {case}"
    return changed


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
    assert parent["active_checkpoint"]=="ISI-27B-RC-EVIDENCE-GOVERNANCE-PACK"
    chain=[
      ("ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS","done","ISI-27B-RC-EVIDENCE-GOVERNANCE-PACK"),
      ("ISI-27B-RC-EVIDENCE-GOVERNANCE-PACK","spec_ready","ISI-27C-REPRODUCIBLE-RELEASE-SUPPLY-CHAIN-ASSURANCE"),
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
        assert "27A ACCEPTED ON MAIN" in text
        assert "27B" in text and "SPEC_READY" in text
        assert "SCOPE LOCKED / 27A IMPLEMENTATION CANDIDATE / NOT CI_VERIFIED" not in text
        assert "## ISI-27A accepted-main closeout and ISI-27B promotion — 2026-10-03" in text
        assert "## ISI-27A accepted-main closeout and ISI-27B promotion — 2026-10-02" not in text
    live_tasks=(ROOT/"automation/tasks.json").read_text()
    for text in (status, tech, master, live_tasks):
        assert "fresh release-candidate bootstrap" not in text.casefold()
    tasks={x["id"]:x for x in json.loads(live_tasks)["tasks"]}
    assert "27A is current" not in tasks["ISI-26-PERFORMANCE-LOAD-RESILIENCE"]["note"]
    assert "ISI-27A is accepted on main and 27B is current" in tasks["ISI-26-PERFORMANCE-LOAD-RESILIENCE"]["note"]
    _assert_closeout_live_pointers(master, live_tasks, status, tech)
    evidence=json.loads((ROOT/"automation/specs/ISI-27A-ACCEPTANCE-CLOSEOUT-EVIDENCE.json").read_text())
    chain=evidence["independent_review_recovery"]["recovery_chain"]
    assert [item["revision"] for item in chain] == ["R1","R2","R3","R4","R4-R1"]
    assert evidence["independent_review_recovery"]["finding"] == "HISTORICAL_LEDGER_VALIDATION_SCOPE_AND_RESIDUAL_LIVE_SUMMARIES"
    assert evidence["independent_review_recovery"]["historical_ledger"]["sha256"] == HISTORY_SHA256
    assert evidence["independent_review_recovery"]["negative_controls"] == len(NEGATIVE_CASES)


@pytest.mark.parametrize("case", NEGATIVE_CASES)
def test_closeout_guard_rejects_live_drift_and_historical_tampering(case):
    documents = {
        "master": (ROOT/"docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text(),
        "tasks": (ROOT/"automation/tasks.json").read_text(),
        "status": (ROOT/"automation/STATUS.md").read_text(),
        "tech": (ROOT/"TECHNICAL_DOCUMENTATION.md").read_text(),
    }
    changed = _closeout_negative_case(case, documents)
    with pytest.raises(AssertionError):
        _assert_closeout_live_pointers(changed["master"], changed["tasks"], changed["status"], changed["tech"])
