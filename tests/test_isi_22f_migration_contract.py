from pathlib import Path
import re
import subprocess


MIGRATION = Path("migrations/versions/20260913_0025_reproducible_analytical_boundary.py")


def test_0025_exact_graph_and_additive_schema_contract():
    text = MIGRATION.read_text()
    assert 'revision = "20260913_0025"' in text
    assert 'down_revision = "20260913_0024"' in text
    for table in ("core_analytical_dataset_contract_versions",
                  "core_analytical_snapshot_governed_outputs",
                  "core_analytical_snapshot_record_inputs"):
        assert f'"{table}"' in text
    for marker in ("LEGACY_SOURCE_VERSION", "GOVERNED_OUTPUT_V1", "PRESERVE_MISSING",
                   "uq_analytical_contract_active_dataset", "analytical_quality_state"):
        assert marker in text


def test_0025_upgrade_offline_sql_is_renderable():
    sql = subprocess.run(["alembic", "upgrade", "20260913_0025", "--sql"],
                         check=True, capture_output=True, text=True).stdout
    assert "core_analytical_snapshot_record_inputs" in sql
    identifiers = re.findall(r'"((?:ck|fk|ix|pk|uq|tr)_[a-z0-9_]+)"', MIGRATION.read_text())
    assert identifiers and max(map(len, identifiers)) <= 63


def test_0025_downgrade_removes_only_owned_schema_in_dependency_order():
    downgrade = MIGRATION.read_text().split("def downgrade()", 1)[1]
    assert downgrade.index('op.drop_table("core_analytical_snapshot_record_inputs")') < downgrade.index(
        'op.drop_table("core_analytical_dataset_contract_versions")')
    for historical in ("core_analytical_datasets", "core_analytical_dataset_snapshots",
                       "core_analytical_snapshot_source_versions", "core_data_governed_ingestion_outputs",
                       "core_data_normalized_records"):
        assert f'op.drop_table("{historical}")' not in downgrade
