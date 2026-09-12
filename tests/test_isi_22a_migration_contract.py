from pathlib import Path
import re
import subprocess


MIGRATION = Path("migrations/versions/20260912_0020_source_connector_contracts.py")
TABLE = "core_data_connector_contract_versions"


def test_0020_identity_table_columns_constraints_and_indexes():
    text = MIGRATION.read_text()
    assert 'revision = "20260912_0020"' in text
    assert 'down_revision = "20260912_0019"' in text
    assert text.count("op.create_table(") == 1
    assert f'"{TABLE}"' in text
    for column in (
        "source_id",
        "organization_id",
        "workspace_id",
        "product_code",
        "version_no",
        "connector_kind",
        "transport",
        "configuration_json",
        "credential_reference",
        "capabilities_json",
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
    assert 'sa.ForeignKey("core_data_sources.id", ondelete="CASCADE")' in text
    for contract in (
        "uq_connector_contract_source_version",
        "ck_connector_contract_version_no",
        "ck_connector_contract_product",
        "ck_connector_contract_state",
        "ix_connector_contract_scope",
        "ix_connector_contract_source_state",
    ):
        assert contract in text
    assert "version_no >= 1" in text
    assert "product_code IN ('SIMPA', 'ORDO')" in text
    assert "lifecycle_state IN ('DRAFT', 'ACTIVE', 'RETIRED')" in text


def test_0020_postgres_identifiers_fit_limit_and_migration_is_single_head():
    text = MIGRATION.read_text()
    identifiers = re.findall(r'"((?:ck|fk|ix|pk|uq|tr)_[a-z0-9_]+)"', text)
    assert identifiers
    assert max(map(len, identifiers)) <= 63
    result = subprocess.run(["alembic", "heads"], check=True, capture_output=True, text=True)
    heads = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(heads) == 1
    assert heads[0].endswith("(head)")
    history = subprocess.run(["alembic", "history"], check=True, capture_output=True, text=True)
    assert "20260912_0020" in history.stdout


def test_0020_downgrade_removes_only_its_table_and_indexes():
    text = MIGRATION.read_text()
    downgrade = text.split("def downgrade()", 1)[1]
    assert downgrade.count("op.drop_table(") == 1
    assert f'op.drop_table("{TABLE}")' in downgrade
    assert downgrade.count("op.drop_index(") == 2
    for existing_table in (
        "core_data_sources",
        "core_data_source_versions",
        "core_data_audit_events",
        "core_data_source_governance_profiles",
        "core_analytical_datasets",
        "core_analytical_dataset_snapshots",
        "core_analytical_features",
        "core_organizations",
        "core_workspaces",
        "core_products",
        "core_memberships",
    ):
        assert f'op.drop_table("{existing_table}")' not in downgrade
