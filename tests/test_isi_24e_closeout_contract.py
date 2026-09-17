from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_24d_is_accepted_and_24e_is_current_without_closing_phase():
    status = (ROOT / "automation/STATUS.md").read_text()
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    tasks = json.loads((ROOT / "automation/tasks.json").read_text())["tasks"]
    task = next(item for item in tasks if item["id"] == "ISI-24-ORDO-PRODUCTION-METHODOLOGY")
    assert "Accepted ISI-24D implementation SHA: `49377e808845fc8746f0484ea7b452954c9e83b4`." in status
    assert "Accepted ISI-24D implementation tree: `c8ea52299d80551ee303dbeef95d343b59448892`." in status
    assert "run #88" in status and "run ID `35220908672`" in status
    assert "Current slice is `ISI-24E - ORDO Final Whole-Phase Gap/Legacy Audit + Closeout`" in status
    assert "24A/24B/24C/24D accepted / 24E current" in status
    assert task["status"] == "in_progress"
    assert task["spec"] == "automation/specs/ISI-24E-ORDO-FINAL-CLOSEOUT.md"
    assert "ISI-24D accepted checkpoint" in master
    assert "ISI-24E current governed slice" in master
    assert "Overall ISI-24 remains `IN PROGRESS`" in master


def test_24e_activation_contract_preserves_boundaries():
    spec = (ROOT / "automation/specs/ISI-24E-ORDO-FINAL-CLOSEOUT.md").read_text()
    for phrase in (
        "DONE / PARTIAL / MISSING / DRIFT",
        "REMOVE_BEFORE_NEXT_SLICE",
        "REMOVE_IN_NAMED_PHASE(<phase>)",
        "overall ISI-24 stays `IN PROGRESS`",
        "ISI-25 stays `PLANNED`",
        "no server/DNS/ingress/production mutation",
        "This is NOT the remediation surface",
    ):
        assert phrase in spec


def test_known_stale_isi11_caption_is_audit_seed_not_silently_removed():
    ui = (ROOT / "src/streamlit_app/ordo_analytics_workspace.py").read_text()
    spec = (ROOT / "automation/specs/ISI-24E-ORDO-FINAL-CLOSEOUT.md").read_text()
    assert "ISI-11 povezuje" in ui
    assert "accepted-main `ISI-11` caption seed finding" in spec
