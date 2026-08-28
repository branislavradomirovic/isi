from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_migration_is_0009_to_0010_and_offline_safe():
    text = (ROOT / "migrations/versions/20260828_0010_ordo_analytics_ai.py").read_text()
    assert 'revision = "20260828_0010"' in text
    assert 'down_revision = "20260828_0009"' in text
    for table in (
        "ordo_indicator_methodologies",
        "ordo_analytics_runs",
        "ordo_indicator_results",
        "ordo_development_goals",
        "ordo_scenarios",
        "ordo_scenario_assessments",
        "ordo_ai_syntheses",
    ):
        assert table in text
    assert "ordo.decision_support.synthesis" in text
    assert "ordo-decision-support-local" in text
    assert "CAST(:output_schema AS JSON)" in text
