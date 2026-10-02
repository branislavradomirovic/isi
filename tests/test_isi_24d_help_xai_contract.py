from __future__ import annotations

import json
from pathlib import Path

from src.streamlit_app.ordo_help_workspace import HELP_REQUIRED_FIELDS, ORDO_HELP_TOPICS


ROOT = Path(__file__).resolve().parents[1]


def test_ordo_help_topics_are_product_complete_and_verified():
    assert len(ORDO_HELP_TOPICS) == 12
    assert [topic["id"] for topic in ORDO_HELP_TOPICS] == [
        f"ORDO-H{index:02d}" for index in range(1, 13)
    ]
    for topic in ORDO_HELP_TOPICS:
        assert topic["coverage"] == "VERIFIED"
        for field in HELP_REQUIRED_FIELDS:
            assert isinstance(topic.get(field), str) and topic[field].strip()


def test_help_navigation_is_strictly_product_isolated():
    app = (ROOT / "src/streamlit_app/app.py").read_text()
    assert 'code": "simpa_help"' in app and 'code": "ordo_help"' in app
    assert 'shell.get("product", {}).get("code") == "SIMPA"' in app
    assert 'shell.get("product", {}).get("code") == "ORDO"' in app
    assert 'if nav_code == "ordo_help"' in app and "render_ordo_help" in app
    help_source = (ROOT / "src/streamlit_app/ordo_help_workspace.py").read_text()
    assert '!= "ORDO"' in help_source


def test_user_guide_and_matrix_cover_ordo_without_promoting_shared_surfaces():
    guide = (ROOT / "docs/help/ORDO-USER-GUIDE.md").read_text()
    matrix = (ROOT / "docs/help/ISI-HELP-COVERAGE-MATRIX.md").read_text()
    for topic_id in (f"ORDO-H{index:02d}" for index in range(1, 13)):
        assert topic_id in guide or topic_id in matrix
    for phrase in (
        "scenario assessment is not a forecast",
        "NOT_ESTIMATED",
        "NO_APPROVED_RESPONSE_MODEL",
        "LEGACY_NOT_EVALUATED",
        "Rolling-origin",
        "interval level",
        "fingerprint",
        "permission",
        "Safe recovery",
        "non-goals",
        "human review",
    ):
        assert phrase.casefold() in guide.casefold()
    for row_id in ("INV-A12", "INV-A13", "INV-A19"):
        row = next(line for line in matrix.splitlines() if line.startswith(f"| {row_id} |"))
        assert "| VERIFIED |" in row
    assert "| VERIFIED |" in next(
        line for line in matrix.splitlines() if line.startswith("| INV-A21 |")
    )
    # INV-A09 was intentionally PARTIAL during ISI-24D, but ISI-25 owns the
    # shared AI workspace Help/XAI contract and may legitimately promote it later.
    # Preserve ownership/isolation rather than freezing the historical coverage state.
    ai_workspace_row = next(
        line for line in matrix.splitlines() if line.startswith("| INV-A09 |")
    )
    assert "| VERIFIED |" in ai_workspace_row
    assert "| ISI-25 |" in ai_workspace_row
    assert "ISI-AI-USER-GUIDE.md" in ai_workspace_row
    for row_id in ("INV-A02", "INV-A08", "INV-A14", "INV-A15", "INV-A16"):
        row = next(line for line in matrix.splitlines() if line.startswith(f"| {row_id} |"))
        assert "| VERIFIED |" in row
        assert "test_isi_27a_shared_help_contract.py" in row


def test_inventory_policy_harness_and_governance_history_are_synchronized():
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    policy = (ROOT / "tools/ci/policy_check.py").read_text()
    harness = (ROOT / "tests/test_isi_17_harness_contract.py").read_text()
    status = (ROOT / "automation/STATUS.md").read_text()
    tasks = json.loads((ROOT / "automation/tasks.json").read_text())["tasks"]
    row = next(line for line in master.splitlines() if line.startswith("| INV-A19 |"))
    assert "| CURRENT_AS_BUILT |" in row
    assert '"INV-A19": "CURRENT_AS_BUILT"' in policy
    assert 'by_id["INV-A19"][3] == "CURRENT_AS_BUILT"' in harness
    assert "Accepted ISI-24C implementation SHA: `76e4ca5265f48a096d2253c88898e1aaedbff991`." in status
    assert "run #87" in status and "35153774409" in status
    assert "Accepted ISI-24D implementation SHA: `49377e808845fc8746f0484ea7b452954c9e83b4`." in status
    assert "Accepted ISI-24D implementation tree: `c8ea52299d80551ee303dbeef95d343b59448892`." in status
    assert "run #88" in status and "35220908672" in status
    task = next(item for item in tasks if item["id"] == "ISI-24-ORDO-PRODUCTION-METHODOLOGY")
    assert task["status"] == "done"
    assert "5937daa2ea7ff9c476bd6a05a04841d1534aefe2" in task["note"]


def test_forecast_presentation_is_read_only_and_uses_only_accepted_get_endpoints():
    client = (ROOT / "src/streamlit_app/ordo_analytics_api.py").read_text()
    ui = (ROOT / "src/streamlit_app/ordo_analytics_workspace.py").read_text()
    assert 'request(\n            "GET",\n            "/api/v1/ordo/analytics/forecasts"' in client
    assert 'f"/api/v1/ordo/analytics/forecasts/{forecast_run_id}"' in client
    forecast_client_section = client[client.index("def forecasts"):client.index("def create_run")]
    assert '"POST"' not in forecast_client_section
    assert "build_forecast_xai" in ui and "build_scenario_xai" in ui
    assert "forecast_points" in ui and "metric_availability" in ui
    assert "source_snapshot_sha256" in ui and "human_review_status" in ui
    assert "time_series_spec_id = st.text_input" not in ui
    assert "forecast execution form" in ui.casefold()
