from __future__ import annotations

from pathlib import Path

from src.streamlit_app.simpa_help_workspace import HELP_REQUIRED_FIELDS, SIMPA_HELP_TOPICS


ROOT = Path(".")


def test_simpa_help_topics_fulfil_ten_point_contract_and_are_verified():
    assert len(SIMPA_HELP_TOPICS) == 12
    ids = [topic["id"] for topic in SIMPA_HELP_TOPICS]
    assert ids == [f"SIMPA-H{index:02d}" for index in range(1, 13)]
    assert len(ids) == len(set(ids))
    for topic in SIMPA_HELP_TOPICS:
        assert topic["coverage"] == "VERIFIED"
        for field in HELP_REQUIRED_FIELDS:
            assert field in topic
            assert isinstance(topic[field], str) and topic[field].strip()


def test_simpa_help_navigation_is_product_scoped_and_routed():
    app = Path("src/streamlit_app/app.py").read_text()
    assert 'code": "simpa_help"' in app
    assert 'shell.get("product", {}).get("code") == "SIMPA"' in app
    assert 'if nav_code == "simpa_help"' in app
    assert "render_simpa_help" in app


def test_help_matrix_user_guide_and_inventory_are_synchronized():
    matrix = Path("docs/help/ISI-HELP-COVERAGE-MATRIX.md").read_text()
    guide = Path("docs/help/SIMPA-USER-GUIDE.md").read_text()
    master = Path("docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    for index in range(1, 22):
        assert f"INV-A{index:02d}" in matrix
    for row_id in ("INV-A10", "INV-A11", "INV-A18"):
        row = next(line for line in matrix.splitlines() if line.startswith(f"| {row_id} |"))
        assert "| VERIFIED |" in row
    global_row = next(line for line in matrix.splitlines() if line.startswith("| INV-A21 |"))
    assert "| PARTIAL |" in global_row
    for phrase in (
        "DRAFT -> PROPOSED -> VALIDATED -> RETIRED",
        "unavailable_legacy_result",
        "production_eligible=true",
        "Complete-case",
        "Poisson GLM",
        "Fractional Logit",
        "not causality",
        "human review",
    ):
        assert phrase.casefold() in guide.casefold()
    a18 = next(line for line in master.splitlines() if line.startswith("| INV-A18 |"))
    a21 = next(line for line in master.splitlines() if line.startswith("| INV-A21 |"))
    assert "| CURRENT_AS_BUILT |" in a18
    assert "| CURRENT_AS_BUILT |" in a21
    assert "ISI-23D implementation boundary:" in master


def test_simpa_analytics_ui_uses_deterministic_xai_and_exposes_ai_provenance():
    ui = Path("src/streamlit_app/simpa_analytics_workspace.py").read_text()
    assert "build_statistical_xai" in ui
    xai = Path("src/domains/simpa/statistical_xai.py").read_text()
    assert 'xai["coefficients"]' in ui
    assert '"p_value_status"' in xai
    assert "source_snapshot_sha256" in ui
    assert "structured_output_state" in ui
    assert "Detailed SIMPA Help/User Guide remains planned for ISI-23E" not in ui
    assert "statistical_to_ai" not in ui.casefold()


def test_historical_23c_test_no_longer_freezes_future_help_status():
    historical = Path("tests/test_isi_23c_api_ui_contract.py").read_text()
    assert "Detailed SIMPA Help/User Guide remains planned for ISI-23E" not in historical
    assert 'assert "| PLANNED |" in help_row' not in historical
