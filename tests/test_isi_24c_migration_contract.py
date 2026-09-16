from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "migrations/versions/20260916_0032_ordo_forecast_backtest_uncertainty.py"


def test_migration_0032_has_forecast_and_truthful_scenario_semantics():
    text = MIGRATION.read_text()
    assert 'revision = "20260916_0032"' in text
    assert 'down_revision = "20260916_0031"' in text
    assert '"ordo_forecast_runs"' in text
    assert "LEGACY_NOT_EVALUATED" in text
    assert "NO_APPROVED_RESPONSE_MODEL" in text
    assert 'drop_constraint("ck_ordo_scenario_assessment_no_forecast"' not in text
    assert 'op.drop_table("ordo_forecast_runs")' in text


def test_model_and_migration_columns_stay_synchronized():
    from src.domains.ordo.analytics_models import OrdoForecastRun

    for name in (
        "request_fingerprint", "result_fingerprint", "series_identity", "backtest_records",
        "aggregate_backtest_metrics", "metric_availability", "diagnostics", "forecast_points",
        "non_causal", "automatic_model_selection", "automatic_policy_recommendation",
    ):
        assert name in OrdoForecastRun.__table__.columns
