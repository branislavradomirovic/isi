import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_24c_is_current_and_24b_is_an_accepted_checkpoint():
    status = (ROOT / "automation/STATUS.md").read_text()
    tasks = json.loads((ROOT / "automation/tasks.json").read_text())
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    task = next(item for item in tasks["tasks"] if item["id"] == "ISI-24-ORDO-PRODUCTION-METHODOLOGY")
    assert task["status"] == "in_progress"
    assert task["spec"].endswith("ISI-24C-ORDO-FORECAST-BACKTEST-UNCERTAINTY-CONTRACTS.md")
    assert "0ad913db23cea44033e8adf693eb179edfa8fb5d" in status
    assert "35147730914" in status and "Current slice is `ISI-24C" in status
    assert "ISI-24B accepted checkpoint" in master and "ISI-24C current governed slice" in master
    assert "INV-C38" in master and "INV-C39" in master


def test_scope_and_dependency_surfaces_are_locked():
    spec = (ROOT / "automation/specs/ISI-24C-ORDO-FORECAST-BACKTEST-UNCERTAINTY-CONTRACTS.md").read_text()
    assert "Exact mutable surface" in spec and "FROZEN 21" in spec
    assert "NO dependency changes" in spec and "NO stage/commit/push" in spec
