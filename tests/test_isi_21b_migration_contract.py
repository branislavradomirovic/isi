from pathlib import Path
import re
import subprocess


MIGRATION = Path("migrations/versions/20260912_0018_data_privacy_enforcement.py")


def test_exact_identity_parent_tables_columns_and_backfills():
    text = MIGRATION.read_text()
    assert 'revision = "20260912_0018"' in text
    assert 'down_revision = "20260912_0017"' in text
    for table in (
        "core_data_anonymization_records",
        "core_data_export_manifests",
        "core_data_governance_invalidations",
    ):
        assert f'"{table}"' in text
    for column in ("content_state", "revision", "purge_status", "hold_placed_at", "hold_released_at"):
        assert f'"{column}"' in text
    assert 'server_default="AVAILABLE"' in text
    assert 'server_default="NONE"' in text
    assert 'server_default="1"' in text
    assert "GOVERNED_EXPORT_ALLOWED" in text
    assert "export_policy = 'PROHIBITED'" in text.split("def downgrade()", 1)[1]


def test_exact_export_values_permission_seed_and_no_reviewer_viewer_broadening():
    text = MIGRATION.read_text()
    export_constraint = text.split('"ck_core_data_source_governance_profiles_export"', 2)[2].split(")", 1)[0]
    assert "PROHIBITED" in export_constraint and "GOVERNED_EXPORT_ALLOWED" in export_constraint
    upgrade = text.split("def upgrade()", 1)[1].split("def downgrade()", 1)[0]
    assert "('data.governance.manage')" in upgrade
    assert "('data.export')" in upgrade
    for role in ("organization_admin", "domain_manager", "data_manager"):
        assert f"('{role}', 'data.governance.manage')" in upgrade
        assert f"('{role}', 'data.export')" in upgrade
    assert "('analyst', 'data.export')" in upgrade
    assert "('analyst', 'data.governance.manage')" not in upgrade
    assert "('reviewer', 'data.export')" not in upgrade
    assert "('viewer', 'data.export')" not in upgrade


def test_constraints_immutability_identifier_lengths_and_reverse_downgrade():
    text = MIGRATION.read_text()
    for token in ("AVAILABLE', 'PURGED", "REQUESTED", "EXECUTING", "FAILED", "PROPOSED", "VERIFIED", "REJECTED"):
        assert token in text
    assert "core_data_export_manifests_immutable" in text
    names = re.findall(r'"((?:ck|fk|ix|uq|tr)_[a-z0-9_]+)"', text)
    assert names and max(map(len, names)) <= 63
    downgrade = text.split("def downgrade()", 1)[1]
    positions = [
        downgrade.index('op.drop_table("core_data_governance_invalidations")'),
        downgrade.index('op.drop_table("core_data_export_manifests")'),
        downgrade.index('op.drop_table("core_data_anonymization_records")'),
        downgrade.index('op.drop_column("core_data_source_versions", "content_state")'),
    ]
    assert positions == sorted(positions)


def test_0018_remains_in_single_head_alembic_history():
    heads = subprocess.run(["alembic", "heads"], check=True, capture_output=True, text=True)
    assert len([line for line in heads.stdout.splitlines() if line.strip()]) == 1
    history = subprocess.run(["alembic", "history"], check=True, capture_output=True, text=True)
    assert "20260912_0018" in history.stdout
