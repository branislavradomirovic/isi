from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_24b_accepted_checkpoint_and_inventory_are_preserved():
    status = (ROOT / "automation/STATUS.md").read_text()
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    assert "0ad913db23cea44033e8adf693eb179edfa8fb5d" in status
    assert "1008022ebe4cf95b4d45a12ff746188e6c8efa11" in status
    assert "35147730914" in status and "ISI-24B is `COMPLETE / CI_VERIFIED`" in status
    for inventory_id in ("INV-C35", "INV-C36", "INV-C37"):
        assert inventory_id in master
    assert "ISI-24A accepted checkpoint" in master and "ISI-24B accepted checkpoint" in master


def test_migration_and_scenario_no_forecast_boundary():
    migration = (ROOT / "migrations/versions/20260916_0031_ordo_spatial_statistical_temporal_contracts.py").read_text()
    assert 'revision = "20260916_0031"' in migration and 'down_revision = "20260916_0030"' in migration
    for table in ("ordo_spatial_aggregation_runs", "ordo_statistical_model_contracts", "ordo_time_series_specs"):
        assert table in migration
    assert "SET status = 'draft' WHERE status = 'proposed'" in migration
    models = (ROOT / "src/domains/ordo/analytics_models.py").read_text()
    assert 'CheckConstraint("forecast_performed = false", name="ck_ordo_scenario_assessment_no_forecast")' in models
    assert "rolling_origin_plan_only" in (ROOT / "src/domains/ordo/time_series_contracts.py").read_text()
