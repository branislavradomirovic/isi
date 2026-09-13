from pathlib import Path
import re


MIGRATION = Path(
    "migrations/versions/20260913_0023_record_governance_dedup_quarantine.py"
)


def test_0023_identity_tables_column_and_constraint_contract():
    text = MIGRATION.read_text()
    assert 'revision = "20260913_0023"' in text
    assert 'down_revision = "20260913_0022"' in text
    assert text.count("op.create_table(") == 4
    for table in (
        "core_data_record_governance_policy_versions",
        "core_data_record_entities",
        "core_data_normalized_records",
        "core_data_record_resolutions",
    ):
        assert f'"{table}"' in text
    for contract in (
        "uq_rec_policy_source_version",
        "ck_rec_policy_version_no",
        "ck_rec_policy_format",
        "ck_rec_policy_product",
        "ck_rec_policy_missing",
        "ck_rec_policy_duplicate",
        "ck_rec_policy_conflict",
        "ck_rec_policy_lifecycle",
        "uq_rec_policy_active_source",
        "uq_rec_entity_source_policy_identity",
        "ck_rec_entity_state",
        "uq_norm_rec_run_ordinal",
        "ck_norm_rec_ordinal",
        "ck_norm_rec_disposition",
        "uq_norm_rec_accepted_entity",
        "uq_rec_resolution_quarantine",
        "ck_rec_resolution_decision",
    ):
        assert contract in text
    assert "record_governance_policy_version_id" in text
    assert "fk_ing_run_rec_policy" in text
    assert "ix_ing_run_rec_policy" in text
    assert text.count('ondelete="RESTRICT"') >= 14


def test_0023_partial_indexes_are_cross_dialect_identifiers_fit_and_is_sole_head():
    text = MIGRATION.read_text()
    for index, predicate in (
        ("uq_rec_policy_active_source", "lifecycle_state = 'ACTIVE'"),
        (
            "uq_norm_rec_accepted_entity",
            "entity_id IS NOT NULL AND disposition = 'ACCEPTED'",
        ),
    ):
        block = text.split(f'"{index}"', 1)[1].split("sqlite_where", 1)[0]
        assert "unique=True" in block
        assert f'postgresql_where=sa.text("{predicate}")' in text
        assert f'sqlite_where=sa.text("{predicate}")' in text
    identifiers = re.findall(r'"((?:ck|fk|ix|pk|uq|tr)_[a-z0-9_]+)"', text)
    assert identifiers and max(map(len, identifiers)) <= 63


def test_0023_downgrade_removes_only_owned_surface_in_dependency_order():
    text = MIGRATION.read_text()
    downgrade = text.split("def downgrade()", 1)[1]
    assert downgrade.count("op.drop_table(") == 4
    assert downgrade.index('op.drop_table("core_data_record_resolutions")') < downgrade.index(
        'op.drop_table("core_data_normalized_records")'
    )
    assert downgrade.index('op.drop_table("core_data_normalized_records")') < downgrade.index(
        'op.drop_table("core_data_record_entities")'
    )
    assert downgrade.index('op.drop_constraint("fk_ing_run_rec_policy"') < downgrade.index(
        'op.drop_table("core_data_record_governance_policy_versions")'
    )
    assert 'op.drop_column("core_data_ingestion_runs", "record_governance_policy_version_id")' in downgrade
    for historical in (
        "core_data_ingestion_runs",
        "core_data_sources",
        "core_data_source_versions",
        "core_data_connector_contract_versions",
        "core_data_source_schema_mapping_versions",
    ):
        assert f'op.drop_table("{historical}")' not in downgrade
