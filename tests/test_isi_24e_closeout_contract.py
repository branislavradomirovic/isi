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


def test_24e_remediation_contract_preserves_boundaries():
    spec = (ROOT / "automation/specs/ISI-24E-ORDO-FINAL-CLOSEOUT.md").read_text()
    for phrase in (
        "dac9f488ad650330ce258d44617d4b897a31f6aa",
        "bb78978298cd5232cf402c03c9949e20804bd7bc",
        "run #89 / `35227300000`",
        "F01: `DRIFT / REMOVE_BEFORE_NEXT_SLICE`",
        "F02: `PARTIAL / REMOVE_BEFORE_NEXT_SLICE`",
        "F08: `PARTIAL / REMOVE_IN_NAMED_PHASE(ISI-25/ISI-27)`",
        "REMOVE_BEFORE_NEXT_SLICE",
        "overall ISI-24 stays `IN PROGRESS`",
        "ISI-25 stays `PLANNED`",
        "no server/DNS/ingress/production mutation",
        "Exact mutable surface - FROZEN 12",
        "analysis.read",
        "indicator.manage",
        "analysis.run",
        "There is no `analysis.review` permission",
        "NOT COMPLETE / NOT CI_VERIFIED",
    ):
        assert phrase in spec


def test_f01_stale_isi11_caption_is_removed_as_remediation_truth():
    ui = (ROOT / "src/streamlit_app/ordo_analytics_workspace.py").read_text()
    spec = (ROOT / "automation/specs/ISI-24E-ORDO-FINAL-CLOSEOUT.md").read_text()
    assert "ISI-11 povezuje" not in ui
    assert "F01 and F02 are the only remediation targets" in spec
