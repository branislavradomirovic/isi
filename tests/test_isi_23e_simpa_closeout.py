from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md"
STATUS = ROOT / "automation/STATUS.md"
TASKS = ROOT / "automation/tasks.json"
EVIDENCE = ROOT / "automation/evidence/ISI-23/acceptance-summary.md"
SPEC = ROOT / "automation/specs/ISI-23E-SIMPA-CLOSEOUT.md"
MATRIX = ROOT / "docs/help/ISI-HELP-COVERAGE-MATRIX.md"
GUIDE = ROOT / "docs/help/SIMPA-USER-GUIDE.md"


def _matrix_rows() -> dict[str, str]:
    rows = {}
    for line in MATRIX.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| INV-A"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[2] in {"MISSING", "PARTIAL", "COMPLETE", "VERIFIED"}:
            rows[cells[0]] = cells[2]
    return rows


def test_closeout_records_exact_23d_acceptance_and_serial_transition():
    status = STATUS.read_text(encoding="utf-8")
    assert "Accepted ISI-23D implementation SHA: `a39caa8160f01dee4e30ab7912a732f0aa68c0d6`." in status
    assert "Accepted ISI-23D implementation tree: `05384a755462790484794714e741f74762d6da0d`." in status
    assert "run #83" in status and "run ID `35081472982`" in status
    assert "Accepted ISI-23E closeout SHA: `3894f5d4ce9b78abc39f9a565fecf83bc2ce7a73`." in status
    assert "run #84" in status and "run ID `35084716444`" in status
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))["tasks"]
    by_id = {item["id"]: item for item in tasks}
    phase = by_id["ISI-23-SIMPA-PRODUCTION-METHODOLOGY"]
    assert phase["status"] == "done"
    assert phase["next"] == "ISI-24-ORDO-PRODUCTION-METHODOLOGY"
    assert "ISI-23E final closeout is COMPLETE / CI_VERIFIED on 3894f5d4ce9b78abc39f9a565fecf83bc2ce7a73" in phase["note"]
    assert "run #84 / 35084716444" in phase["note"]
    assert "ISI-23-SIMPA-PRODUCTION-METHODOLOGY" in by_id["ISI-24-ORDO-PRODUCTION-METHODOLOGY"]["depends_on"]


def test_masterplan_and_evidence_close_phase_without_claiming_new_capability():
    master = MASTER.read_text(encoding="utf-8")
    evidence = EVIDENCE.read_text(encoding="utf-8")
    assert "ISI-23E final closeout is COMPLETE / CI_VERIFIED" in master
    assert "ISI-23E closeout boundary: no new production feature." in master
    assert "a39caa8160f01dee4e30ab7912a732f0aa68c0d6" in evidence
    assert "35081472982" in evidence
    assert "No Phase-23 `REMOVE_BEFORE_NEXT_SLICE` item remains" in evidence
    assert "unavailable_legacy_result" in evidence
    for deferred in ("ISI-24", "ISI-25", "ISI-26", "ISI-27", "ISI-28"):
        assert deferred in evidence
    assert "no citizen scoring" in evidence.casefold()
    assert "causal" in evidence.casefold()
    assert "LISI" in evidence


def test_simpa_help_acceptance_preserves_simpa_and_follows_current_global_matrix_authority():
    rows = _matrix_rows()
    assert rows["INV-A10"] == "VERIFIED"
    assert rows["INV-A11"] == "VERIFIED"
    assert rows["INV-A18"] == "VERIFIED"
    assert rows["INV-A21"] == "VERIFIED"
    assert any(value in {"PARTIAL", "MISSING"} for key, value in rows.items() if key not in {"INV-A10", "INV-A11", "INV-A18"})
    assert GUIDE.is_file()


def test_closeout_spec_is_evidence_test_governance_only_and_keeps_server_frozen():
    spec = SPEC.read_text(encoding="utf-8")
    assert "No application/runtime behavior changes" in spec
    assert "Any `src/`, migration, dependency/lock, workflow, deployment or server mutation is forbidden" in spec
    assert "DEFERRED_SERVER_VERIFICATION" in spec
    assert "no new SIMPA feature" in spec
