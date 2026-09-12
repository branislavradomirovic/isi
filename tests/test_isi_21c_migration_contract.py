from pathlib import Path
import re
import subprocess


MIGRATION = Path("migrations/versions/20260912_0019_analytical_data_governance.py")


def test_0019_identity_tables_constraints_and_typed_edges():
    text = MIGRATION.read_text()
    assert 'revision = "20260912_0019"' in text and 'down_revision = "20260912_0018"' in text
    for table in ("core_analytical_datasets", "core_analytical_dataset_snapshots",
                  "core_analytical_snapshot_source_versions", "core_analytical_features",
                  "core_analytical_feature_versions", "core_analytical_feature_snapshot_inputs"):
        assert f'"{table}"' in text
    for constraint in ("uq_analytical_dataset_scope_code", "uq_analytical_snapshot_dataset_version",
                       "uq_analytical_snapshot_source_edge", "uq_analytical_feature_version",
                       "uq_analytical_feature_snapshot_edge"):
        assert constraint in text
    assert 'ForeignKey("core_data_source_versions.id"' in text
    assert 'ForeignKey("core_analytical_dataset_snapshots.id"' in text
    assert "version_no >= 1" in text
    names = re.findall(r'"((?:ck|fk|ix|uq|tr)_[a-z0-9_]+)"', text)
    assert names and max(map(len, names)) <= 63


def test_0019_remains_in_history_and_downgrade_is_scoped():
    result = subprocess.run(["alembic", "heads"], check=True, capture_output=True, text=True)
    head_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert len(head_lines) == 1
    assert head_lines[0].endswith("(head)")
    history = subprocess.run(["alembic", "history"], check=True, capture_output=True, text=True)
    assert "20260912_0019" in history.stdout
    downgrade = MIGRATION.read_text().split("def downgrade()", 1)[1]
    assert downgrade.count("op.drop_table(") == 6
    assert "core_data_source_versions" not in downgrade
