from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_scenario_assessment_is_evidence_only_and_never_forecasts():
    service = (ROOT / "src/domains/ordo/analytics_service.py").read_text()
    models = (ROOT / "src/domains/ordo/analytics_models.py").read_text()
    migration = (ROOT / "migrations/versions/20260828_0010_ordo_analytics_ai.py").read_text()
    assert '"assessment_mode": "evidence_readiness_only"' in service
    assert '"forecast_performed": False' in service
    assert "No causal, predictive, financial, visitor-volume, employment" in service
    assert "forecast_performed = false" in models
    assert "forecast_performed = false" in migration


def test_development_goal_and_scenario_are_user_authored_planning_objects():
    schemas = (ROOT / "src/domains/ordo/analytics_schemas.py").read_text()
    assert "DevelopmentGoalCreateRequest" in schemas
    assert "ScenarioCreateRequest" in schemas
    assert "assumptions: list[str]" in schemas
    assert "measures: list[str]" in schemas
