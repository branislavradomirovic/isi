from pathlib import Path
import re
import subprocess


MIGRATION = Path("migrations/versions/20260913_0021_source_schema_mapping_contracts.py")
TABLE = "core_data_source_schema_mapping_versions"


def test_0021_identity_table_columns_foreign_keys_constraints_and_indexes():
    text = MIGRATION.read_text()
    assert 'revision = "20260913_0021"' in text
    assert 'down_revision = "20260912_0020"' in text
    assert text.count("op.create_table(") == 1
    assert f'"{TABLE}"' in text
    for column in (
        "id",
        "source_id",
        "connector_contract_version_id",
        "organization_id",
        "workspace_id",
        "product_code",
        "version_no",
        "contract_format_version",
        "schema_kind",
        "source_schema_json",
        "field_mapping_json",
        "missing_value_policy",
        "unexpected_field_policy",
        "fingerprint",
        "lifecycle_state",
        "created_by_membership_id",
        "activated_by_membership_id",
        "retired_by_membership_id",
        "created_at",
        "activated_at",
        "retired_at",
    ):
        assert f'"{column}"' in text
    assert '"core_data_sources.id"' in text
    assert '"core_data_connector_contract_versions.id"' in text
    assert text.count('ondelete="CASCADE"') >= 4
    for contract in (
        "uq_schema_mapping_source_version",
        "ck_schema_mapping_version_no",
        "ck_schema_mapping_contract_format",
        "ck_schema_mapping_product",
        "ck_schema_mapping_schema_kind",
        "ck_schema_mapping_missing_policy",
        "ck_schema_mapping_unexpected_policy",
        "ck_schema_mapping_lifecycle",
        "ix_schema_mapping_scope",
        "ix_schema_mapping_source_state",
        "ix_schema_mapping_connector",
        "uq_schema_mapping_active_source",
    ):
        assert contract in text
    assert "version_no >= 1" in text
    assert "contract_format_version = 1" in text
    assert "product_code IN ('SIMPA', 'ORDO')" in text
    assert "schema_kind IN ('TABULAR', 'RECORD')" in text
    assert "missing_value_policy = 'PRESERVE_MISSING'" in text
    assert "unexpected_field_policy IN ('REJECT', 'IGNORE')" in text
    assert "lifecycle_state IN ('DRAFT', 'ACTIVE', 'RETIRED')" in text
    active_index = text.split('"uq_schema_mapping_active_source"', 1)[1].split(
        "def downgrade", 1
    )[0]
    assert "unique=True" in active_index
    assert 'postgresql_where=sa.text("lifecycle_state = \'ACTIVE\'")' in active_index
    assert 'sqlite_where=sa.text("lifecycle_state = \'ACTIVE\'")' in active_index


def test_0021_postgres_identifiers_fit_limit_and_remains_in_history():
    text = MIGRATION.read_text()
    identifiers = re.findall(r'"((?:ck|fk|ix|pk|uq|tr)_[a-z0-9_]+)"', text)
    assert identifiers
    assert max(map(len, identifiers)) <= 63
    history = subprocess.run(
        ["alembic", "history"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "20260913_0021" in history.stdout


def test_0021_downgrade_removes_only_owned_indexes_and_table():
    text = MIGRATION.read_text()
    downgrade = text.split("def downgrade()", 1)[1]
    assert downgrade.count("op.drop_table(") == 1
    assert f'op.drop_table("{TABLE}")' in downgrade
    assert downgrade.count("op.drop_index(") == 4
    for index in (
        "uq_schema_mapping_active_source",
        "ix_schema_mapping_connector",
        "ix_schema_mapping_source_state",
        "ix_schema_mapping_scope",
    ):
        assert f'"{index}"' in downgrade
    assert downgrade.count(f'table_name="{TABLE}"') == 4
    for existing_table in (
        "core_data_sources",
        "core_data_source_versions",
        "core_data_connector_contract_versions",
        "core_data_audit_events",
        "core_data_source_governance_profiles",
        "core_analytical_datasets",
        "core_organizations",
        "core_workspaces",
        "core_products",
        "core_memberships",
    ):
        assert f'op.drop_table("{existing_table}")' not in downgrade
