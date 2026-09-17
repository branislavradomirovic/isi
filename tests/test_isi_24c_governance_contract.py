import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_24c_is_an_accepted_checkpoint_in_history():
    status = (ROOT / "automation/STATUS.md").read_text()
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    assert "Accepted ISI-24C implementation SHA: `76e4ca5265f48a096d2253c88898e1aaedbff991`." in status
    assert "Accepted ISI-24C implementation tree: `0a6ec7b7ab4db5d43c570c714c065f8fef7093f4`." in status
    assert "run #87" in status and "run ID `35153774409`" in status
    assert "ISI-24C accepted checkpoint" in master
    assert "76e4ca5265f48a096d2253c88898e1aaedbff991" in master
    assert "35153774409" in master
    assert "INV-C38" in master and "INV-C39" in master


def test_24c_scope_and_dependency_surfaces_remain_locked_history():
    spec = (ROOT / "automation/specs/ISI-24C-ORDO-FORECAST-BACKTEST-UNCERTAINTY-CONTRACTS.md").read_text()
    assert "Exact mutable surface" in spec and "FROZEN 21" in spec
    assert "NO dependency changes" in spec and "NO stage/commit/push" in spec


def test_24d_scope_lock_and_candidate_as_built_inventory_are_synchronized():
    spec = (ROOT / "automation/specs/ISI-24D-ORDO-HELP-XAI.md").read_text()
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    status = (ROOT / "automation/STATUS.md").read_text()
    assert "OWNER-SCOPE-FROZEN IMPLEMENTATION CONTRACT" in spec
    assert "Exact mutable surface — FROZEN 17" in spec
    assert "No backend forecast service, API route, schema, model, migration, forecast engine or dependency change is authorized" in spec
    inv_a19 = next(line for line in master.splitlines() if line.startswith("| INV-A19 |"))
    assert "| CURRENT_AS_BUILT |" in inv_a19
    assert "tests/test_isi_24d_help_xai_contract.py" in inv_a19
    assert "Accepted ISI-24D implementation SHA: `49377e808845fc8746f0484ea7b452954c9e83b4`." in status
    assert "run #88" in status and "run ID `35220908672`" in status
