import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_governance_and_inventory_are_synchronized():
    status = (ROOT / "automation/STATUS.md").read_text()
    tasks = json.loads((ROOT / "automation/tasks.json").read_text())
    master = (ROOT / "docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    assert "04b0738933030f1d69de52f9260c7b2f11042d0e" in status
    assert "35138374174" in status and "Current slice is `ISI-24B" in status
    task = next(item for item in tasks["tasks"] if item["id"] == "ISI-24-ORDO-PRODUCTION-METHODOLOGY")
    assert task["status"] == "in_progress"
    assert task["spec"].endswith("ISI-24B-ORDO-SPATIAL-STATISTICAL-TEMPORAL-CONTRACTS.md")
    for inventory_id in ("INV-C35", "INV-C36", "INV-C37"):
        assert inventory_id in master
    assert "ISI-24A accepted checkpoint" in master and "ISI-24B current governed slice" in master


def test_migration_and_scenario_no_forecast_boundary():
    migration = (ROOT / "migrations/versions/20260916_0031_ordo_spatial_statistical_temporal_contracts.py").read_text()
    assert 'revision = "20260916_0031"' in migration and 'down_revision = "20260916_0030"' in migration
    for table in ("ordo_spatial_aggregation_runs", "ordo_statistical_model_contracts", "ordo_time_series_specs"):
        assert table in migration
    assert "SET status = 'draft' WHERE status = 'proposed'" in migration
    models = (ROOT / "src/domains/ordo/analytics_models.py").read_text()
    assert 'CheckConstraint("forecast_performed = false", name="ck_ordo_scenario_assessment_no_forecast")' in models
    assert "rolling_origin_plan_only" in (ROOT / "src/domains/ordo/time_series_contracts.py").read_text()
