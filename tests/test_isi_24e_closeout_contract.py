from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_EVIDENCE = ROOT / "automation/specs/ISI-26-R1-HISTORICAL-GOVERNANCE-EVIDENCE.json"


def _historical_evidence() -> dict:
    return json.loads(HISTORICAL_EVIDENCE.read_text(encoding="utf-8"))


def test_24e_accepted_checkpoint_closes_phase24_and_transitions_to_25_bootstrap():
    status = (ROOT / "automation/STATUS.md").read_text()
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    tasks = json.loads((ROOT / "automation/tasks.json").read_text())["tasks"]
    by_id = {item["id"]: item for item in tasks}
    phase24 = by_id["ISI-24-ORDO-PRODUCTION-METHODOLOGY"]
    phase25 = by_id["ISI-25-INDUSTRIAL-AI-MLOPS"]
    historical = _historical_evidence()["phase24_transition"]

    assert "Accepted ISI-24E remediation/closeout implementation SHA: `5937daa2ea7ff9c476bd6a05a04841d1534aefe2`." in status
    assert "Accepted ISI-24E remediation/closeout implementation tree: `6e75bf1cd13b95e23f9189b9e94453dd130eaa19`." in status
    assert "run #90" in status and "run ID `35238623960`" in status and "attempt 2" in status
    assert "Overall `ISI-24-ORDO-PRODUCTION-METHODOLOGY` is `COMPLETE / CI_VERIFIED`." in status
    assert "24A through 24E complete" in status
    assert historical["authority_sha"] == "7e4db145c285aaff7a96f9c37279c44477f4432f"
    assert historical["status_marker"] == "ISI-25 bootstrap/audit - Industrial AI / MLOps"
    assert historical["phase25_status"] == "planned"
    assert historical["phase25_note_marker"] == "CURRENT/NEXT BOOTSTRAP"
    assert phase24["status"] == "done"
    assert phase24["next"] == "ISI-25-INDUSTRIAL-AI-MLOPS"
    assert phase24["spec"] == "automation/specs/ISI-24E-ORDO-FINAL-CLOSEOUT.md"
    assert "5937daa2ea7ff9c476bd6a05a04841d1534aefe2" in phase24["note"]
    assert "run #90 / 35238623960 attempt 2 completed success" in phase24["note"]
    assert phase25["status"] == "done"
    assert phase25["next"] == "ISI-26-PERFORMANCE-LOAD-RESILIENCE"
    assert "ISI-24E accepted checkpoint and Phase-24 closeout" in master
    assert historical["overall_phase24_status"] == "Overall ISI-24 is `COMPLETE / CI_VERIFIED`"


def test_24e_final_spec_records_resolved_and_deferred_findings_without_scope_leakage():
    spec = (ROOT / "automation/specs/ISI-24E-ORDO-FINAL-CLOSEOUT.md").read_text()
    for phrase in (
        "5937daa2ea7ff9c476bd6a05a04841d1534aefe2",
        "6e75bf1cd13b95e23f9189b9e94453dd130eaa19",
        "run #90 / `35238623960` / attempt 2 / `completed success`",
        "F01: stale user-facing `ISI-11 povezuje` wording — RESOLVED",
        "F02: accepted forecast runtime was not reachable as a complete governed customer workflow — RESOLVED",
        "F08: global cross-product Help completion — `REMOVE_IN_NAMED_PHASE(ISI-25/ISI-27)`",
        "No Phase-24 `REMOVE_BEFORE_NEXT_SLICE` item remains",
        "Exactly eleven paths may change",
        "CI / GitHub Actions Cost & Acceptance Policy",
        "manual `workflow_dispatch`",
        "Codex is not authorized",
        "no automatic model selection/promotion/fallback",
        "No ISI-25 implementation",
        "deferred to owner-approved ISI-28",
    ):
        assert phrase in spec
    assert "NOT COMPLETE / NOT CI_VERIFIED" not in spec
    assert "overall ISI-24 stays `IN PROGRESS`" not in spec


def test_phase24_inventory_is_synchronized_to_accepted_customer_workflow():
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    a13 = next(line for line in master.splitlines() if line.startswith("| INV-A13 |"))
    a19 = next(line for line in master.splitlines() if line.startswith("| INV-A19 |"))
    m08 = next(line for line in master.splitlines() if line.startswith("| INV-M08 |"))
    assert "governed time-series-spec lifecycle" in a13
    assert "explicit forecast execution" in a13
    assert "indicator.manage" in a13 and "analysis.run" in a13 and "analysis.read" in a13
    assert "read-only persisted forecast presentation" not in a13
    assert "no raw-UUID execution form" not in a13
    assert "tests/test_isi_24e_forecast_workflow_ui.py" in a19
    assert "ISI-27A supplies current shared Help/presentation authority" in a19
    assert "tests/test_isi_24e*.py" in m08


def test_f01_stale_caption_remains_removed_and_f08_stays_deferred():
    ui = (ROOT / "src/streamlit_app/ordo_analytics_workspace.py").read_text()
    matrix = (ROOT / "docs/help/ISI-HELP-COVERAGE-MATRIX.md").read_text()
    assert "ISI-11 povezuje" not in ui
    assert "| INV-A13 | ORDO analytics and scenarios | VERIFIED |" in matrix
    assert "| INV-A19 | ORDO Help, User Guide and XAI interpretation | VERIFIED |" in matrix
    assert "| INV-A21 | Cross-product Help Coverage Matrix | VERIFIED |" in matrix
    assert "test_isi_27a_shared_help_contract.py" in next(line for line in matrix.splitlines() if line.startswith("| INV-A21 |"))

def test_masterplan_has_no_stale_phase24_in_progress_binding_after_closeout():
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    assert "overall ISI-24 remains IN PROGRESS, ORDO Help/XAI remains owned by 24D" not in master
    assert "ISI-24 remained IN PROGRESS through the accepted ISI-24D checkpoint" in master
    assert "historical phase-status constraint is superseded by the accepted ISI-24E closeout recorded below" in master


def test_masterplan_has_no_stale_24c_current_slice_authority_after_phase24_closeout():
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    assert "ISI-24C - Forecast Engine + Rolling-Origin Backtesting + Uncertainty/Diagnostics + NOT_ESTIMATED Runtime Semantics is the current owner-scope-frozen slice" not in master
    assert "ISI-24C - Forecast Engine + Rolling-Origin Backtesting + Uncertainty/Diagnostics + NOT_ESTIMATED Runtime Semantics was the owner-scope-frozen forecast-engine slice through its accepted checkpoint" in master
    assert "it is no longer the current implementation slice after accepted ISI-24D/ISI-24E closeout" in master
    assert "its accepted runtime semantics remain authoritative" in master


def test_masterplan_historicizes_24b_plan_only_authority_after_24e_workflow_acceptance():
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    assert "the 24B time-series specification remains plan-only" not in master
    assert "At the accepted ISI-24C checkpoint, the 24B time-series specification was plan-only" in master
    assert "only naive and seasonal-naive were executable forecast families" in master
    assert "accepted ISI-24E later exposed the governed specification lifecycle" in master
    assert "without changing the accepted 24C forecast-family boundary or authorizing automatic model selection or scenario impact estimation" in master
