from pathlib import Path
import re
import subprocess


MIGRATION = Path(
    "migrations/versions/20260913_0022_incremental_idempotent_ingestion_runs.py"
)
TABLE = "core_data_ingestion_runs"


def test_0022_identity_single_table_columns_foreign_keys_and_constraints():
    text = MIGRATION.read_text()
    assert 'revision = "20260913_0022"' in text
    assert 'down_revision = "20260913_0021"' in text
    assert text.count("op.create_table(") == 1
    assert TABLE in text
    for column in (
        "id",
        "source_id",
        "organization_id",
        "workspace_id",
        "product_code",
        "run_no",
        "connector_contract_version_id",
        "schema_mapping_version_id",
        "source_version_id",
        "inspection_job_id",
        "idempotency_key",
        "request_fingerprint",
        "payload_sha256",
        "cursor_before",
        "cursor_after",
        "status",
        "attempts",
        "error_code",
        "error_message",
        "created_by_membership_id",
        "queued_at",
        "started_at",
        "finished_at",
        "created_at",
        "updated_at",
    ):
        assert f'"{column}"' in text
    for target in (
        "core_data_sources.id",
        "core_organizations.id",
        "core_workspaces.id",
        "core_products.code",
        "core_data_connector_contract_versions.id",
        "core_data_source_schema_mapping_versions.id",
        "core_data_source_versions.id",
        "core_ingestion_jobs.id",
        "core_memberships.id",
    ):
        assert f'"{target}"' in text
    assert text.count('ondelete="RESTRICT"') == 4
    for contract in (
        "uq_ing_run_source_no",
        "uq_ing_run_source_idem",
        "uq_ing_run_source_fp",
        "uq_ing_run_source_version",
        "uq_ing_run_inspection_job",
        "ck_ing_run_no",
        "ck_ing_run_attempts",
        "ck_ing_run_product",
        "ck_ing_run_status",
    ):
        assert contract in text
    assert "run_no >= 1" in text
    assert "attempts >= 0" in text
    assert "product_code IN ('SIMPA', 'ORDO')" in text
    assert "status IN ('QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED')" in text


def test_0022_scope_binding_and_cross_dialect_live_source_indexes():
    text = MIGRATION.read_text()
    for index in (
        "ix_ing_run_scope",
        "ix_ing_run_source_status",
        "ix_ing_run_binding",
        "uq_ing_run_live_source",
    ):
        assert index in text
    live_index = text.split('"uq_ing_run_live_source"', 1)[1].split(
        "def downgrade", 1
    )[0]
    assert "unique=True" in live_index
    predicate = "status IN ('QUEUED', 'RUNNING')"
    assert f'postgresql_where=sa.text("{predicate}")' in live_index
    assert f'sqlite_where=sa.text("{predicate}")' in live_index


def test_0022_identifiers_fit_postgres_limit_and_is_sole_head():
    text = MIGRATION.read_text()
    identifiers = re.findall(r'"((?:ck|fk|ix|pk|uq|tr)_[a-z0-9_]+)"', text)
    assert identifiers
    assert max(map(len, identifiers)) <= 63
    result = subprocess.run(["alembic", "heads"], check=True, capture_output=True, text=True)
    assert result.stdout.strip() == "20260913_0022 (head)"


def test_0022_downgrade_removes_only_owned_indexes_and_table():
    text = MIGRATION.read_text()
    downgrade = text.split("def downgrade()", 1)[1]
    assert downgrade.count("op.drop_table(") == 1
    assert downgrade.count("op.drop_index(") == 4
    for index in (
        "uq_ing_run_live_source",
        "ix_ing_run_binding",
        "ix_ing_run_source_status",
        "ix_ing_run_scope",
    ):
        assert f'"{index}"' in downgrade
    for existing_table in (
        "core_data_sources",
        "core_data_source_versions",
        "core_ingestion_jobs",
        "core_data_connector_contract_versions",
        "core_data_source_schema_mapping_versions",
        "core_data_audit_events",
        "core_organizations",
        "core_workspaces",
        "core_products",
        "core_memberships",
    ):
        assert f'op.drop_table("{existing_table}")' not in downgrade
