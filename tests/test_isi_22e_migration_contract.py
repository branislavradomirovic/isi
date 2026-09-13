from pathlib import Path
import re
import subprocess

from src.platform.data.models import DataIngestionRun


MIGRATION = Path("migrations/versions/20260913_0024_ingestion_operations_quality_backfill.py")


def test_0024_graph_tables_columns_and_constraints():
    text = MIGRATION.read_text()
    assert 'revision = "20260913_0024"' in text
    assert 'down_revision = "20260913_0023"' in text
    assert text.count("op.create_table(") == 4
    for table in ("core_data_ingestion_operational_policy_versions", "core_data_ingestion_evaluations",
                  "core_data_ingestion_dead_letters", "core_data_governed_ingestion_outputs"):
        assert f'"{table}"' in text
    for column in ("operational_policy_version_id", "execution_mode", "window_start_cursor",
                   "window_end_cursor", "replay_of_run_id", "source_observed_at",
                   "forward_cursor_committed"):
        assert column in text
    for contract in ("uq_ing_op_policy_active_source", "uq_ing_eval_run",
                     "uq_ing_dead_open_run_reason", "uq_gov_ing_output_run",
                     "uq_gov_ing_output_evaluation", "ck_ing_run_execution_mode"):
        assert contract in text


def test_0024_offline_sql_and_identifiers_are_postgres_safe():
    sql = subprocess.run(["alembic", "upgrade", "20260913_0024", "--sql"],
                         check=True, capture_output=True, text=True).stdout
    assert "core_data_ingestion_operational_policy_versions" in sql
    assert "UPDATE core_data_ingestion_runs" in sql
    identifiers = re.findall(r'"((?:ck|fk|ix|pk|uq|tr)_[a-z0-9_]+)"', MIGRATION.read_text())
    assert identifiers and max(map(len, identifiers)) <= 63


def test_0024_preserves_22c_uniqueness_and_backfills_historical_state():
    constraint_names = {constraint.name for constraint in DataIngestionRun.__table__.constraints}
    assert {"uq_ing_run_source_fp", "uq_ing_run_source_version"} <= constraint_names
    text = MIGRATION.read_text()
    assert 'status = \'SUCCEEDED\' THEN true ELSE false' in text
    assert 'execution_mode = \'INCREMENTAL\'' in text
    assert "drop_constraint(\"uq_ing_run_source_fp\"" not in text
    assert "drop_constraint(\"uq_ing_run_source_version\"" not in text


def test_0024_downgrade_is_dependency_safe_and_does_not_drop_historical_tables():
    downgrade = MIGRATION.read_text().split("def downgrade()", 1)[1]
    assert downgrade.index('op.drop_table("core_data_governed_ingestion_outputs")') < downgrade.index(
        'op.drop_table("core_data_ingestion_evaluations")')
    assert downgrade.index('op.drop_table("core_data_ingestion_evaluations")') < downgrade.index(
        'op.drop_table("core_data_ingestion_operational_policy_versions")')
    for historical in ("core_data_ingestion_runs", "core_data_normalized_records",
                       "core_data_source_versions", "core_data_record_governance_policy_versions"):
        assert f'op.drop_table("{historical}")' not in downgrade
