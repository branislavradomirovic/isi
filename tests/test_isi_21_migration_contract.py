from pathlib import Path


MIGRATION = Path("migrations/versions/20260912_0017_data_governance_foundation.py")


def test_governance_migration_identity_tables_and_backfill_contract():
    assert MIGRATION.exists()
    text = MIGRATION.read_text()
    assert 'revision = "20260912_0017"' in text
    assert 'down_revision = "20260911_0016"' in text
    for table in (
        "core_data_retention_policies",
        "core_data_source_governance_profiles",
        "core_data_retention_states",
    ):
        assert table in text
    governance_backfill = text.split("INSERT INTO core_data_source_governance_profiles", 1)[1].split(
        "INSERT INTO core_data_retention_states", 1
    )[0]
    for token in ("'UNCLASSIFIED'", "'UNKNOWN'", "'PROHIBITED'", "'DRAFT'", "NULL", "1"):
        assert token in governance_backfill
    assert "'PUBLIC'" not in governance_backfill
    assert "'AGGREGATE_NON_PERSONAL'" not in governance_backfill
    retention_backfill = text.split("INSERT INTO core_data_retention_states", 1)[1]
    assert "version.created_at" in retention_backfill
    assert "version.source_id" in retention_backfill


def test_governance_migration_downgrade_is_reverse_dependency_order():
    downgrade = MIGRATION.read_text().split("def downgrade()", 1)[1]
    positions = [
        downgrade.index('op.drop_table("core_data_retention_states")'),
        downgrade.index('op.drop_table("core_data_source_governance_profiles")'),
        downgrade.index('op.drop_table("core_data_retention_policies")'),
    ]
    assert positions == sorted(positions)
