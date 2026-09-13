"""Add the reproducible governed analytical data boundary.

Revision ID: 20260913_0025
Revises: 20260913_0024
Create Date: 2026-09-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260913_0025"
down_revision = "20260913_0024"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def _scope_columns(prefix: str):
    return (
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", name=f"fk_{prefix}_org", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", name=f"fk_{prefix}_workspace", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code", name=f"fk_{prefix}_product"), nullable=False),
    )


def upgrade() -> None:
    op.create_table(
        "core_analytical_dataset_contract_versions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("dataset_id", UUID, sa.ForeignKey("core_analytical_datasets.id", name="fk_analytical_contract_dataset", ondelete="CASCADE"), nullable=False),
        *_scope_columns("analytical_contract"),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("contract_format_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("field_contract_json", sa.Text(), nullable=False),
        sa.Column("temporal_mode", sa.String(24), nullable=False),
        sa.Column("temporal_key_fields_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("granularity_key_fields_json", sa.Text(), nullable=False),
        sa.Column("missing_value_policy", sa.String(32), nullable=False, server_default="PRESERVE_MISSING"),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("lifecycle_state", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", name="fk_analytical_contract_created", ondelete="SET NULL"), nullable=True),
        sa.Column("activated_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", name="fk_analytical_contract_activated", ondelete="SET NULL"), nullable=True),
        sa.Column("retired_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", name="fk_analytical_contract_retired", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("activated_at", TS, nullable=True),
        sa.Column("retired_at", TS, nullable=True),
        sa.UniqueConstraint("dataset_id", "version_no", name="uq_analytical_contract_dataset_version"),
        sa.UniqueConstraint("dataset_id", "fingerprint", name="uq_analytical_contract_dataset_fingerprint"),
        sa.CheckConstraint("version_no >= 1", name="ck_analytical_contract_version"),
        sa.CheckConstraint("contract_format_version = 1", name="ck_analytical_contract_format"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_contract_product"),
        sa.CheckConstraint("temporal_mode IN ('STATIC', 'POINT_IN_TIME', 'PERIOD')", name="ck_analytical_contract_temporal"),
        sa.CheckConstraint("missing_value_policy = 'PRESERVE_MISSING'", name="ck_analytical_contract_missing"),
        sa.CheckConstraint("lifecycle_state IN ('DRAFT', 'ACTIVE', 'RETIRED')", name="ck_analytical_contract_lifecycle"),
    )
    op.create_index("ix_analytical_contract_scope", "core_analytical_dataset_contract_versions", ["organization_id", "workspace_id", "product_code"])
    op.create_index("ix_analytical_contract_dataset_state", "core_analytical_dataset_contract_versions", ["dataset_id", "lifecycle_state"])
    op.create_index("ix_core_analytical_dataset_contract_versions_dataset_id", "core_analytical_dataset_contract_versions", ["dataset_id"])
    op.create_index("uq_analytical_contract_active_dataset", "core_analytical_dataset_contract_versions", ["dataset_id"], unique=True,
                    postgresql_where=sa.text("lifecycle_state = 'ACTIVE'"), sqlite_where=sa.text("lifecycle_state = 'ACTIVE'"))

    op.add_column("core_analytical_dataset_snapshots", sa.Column("dataset_contract_version_id", UUID, nullable=True))
    op.add_column("core_analytical_dataset_snapshots", sa.Column("dataset_contract_fingerprint", sa.String(64), nullable=False, server_default=""))
    op.add_column("core_analytical_dataset_snapshots", sa.Column("lineage_mode", sa.String(32), nullable=False, server_default="LEGACY_SOURCE_VERSION"))
    op.add_column("core_analytical_dataset_snapshots", sa.Column("temporal_mode", sa.String(24), nullable=False, server_default=""))
    op.add_column("core_analytical_dataset_snapshots", sa.Column("temporal_key_fields_json", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("core_analytical_dataset_snapshots", sa.Column("granularity_key_fields_json", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("core_analytical_dataset_snapshots", sa.Column("missing_value_policy", sa.String(32), nullable=False, server_default=""))
    op.add_column("core_analytical_dataset_snapshots", sa.Column("analytical_quality_state", sa.String(32), nullable=False, server_default="LEGACY_UNKNOWN"))
    op.add_column("core_analytical_dataset_snapshots", sa.Column("record_count", sa.Integer(), nullable=False, server_default="0"))
    op.create_foreign_key("fk_analytical_snapshot_contract", "core_analytical_dataset_snapshots", "core_analytical_dataset_contract_versions", ["dataset_contract_version_id"], ["id"], ondelete="RESTRICT")
    op.create_check_constraint("ck_analytical_snapshot_lineage_mode", "core_analytical_dataset_snapshots", "lineage_mode IN ('LEGACY_SOURCE_VERSION', 'GOVERNED_OUTPUT_V1')")
    op.create_check_constraint("ck_analytical_snapshot_quality", "core_analytical_dataset_snapshots", "analytical_quality_state IN ('LEGACY_UNKNOWN', 'ACCEPTED_CLEAN', 'ACCEPTED_WITH_WARNING')")
    op.create_check_constraint("ck_analytical_snapshot_record_count", "core_analytical_dataset_snapshots", "record_count >= 0")
    op.create_index("ix_analytical_snapshot_contract", "core_analytical_dataset_snapshots", ["dataset_contract_version_id"])
    op.execute("UPDATE core_analytical_dataset_snapshots SET lineage_mode = 'LEGACY_SOURCE_VERSION', analytical_quality_state = 'LEGACY_UNKNOWN', record_count = 0 WHERE dataset_contract_version_id IS NULL")

    op.create_table(
        "core_analytical_snapshot_governed_outputs",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("snapshot_id", UUID, sa.ForeignKey("core_analytical_dataset_snapshots.id", name="fk_analytical_output_snapshot", ondelete="CASCADE"), nullable=False),
        sa.Column("governed_output_id", UUID, sa.ForeignKey("core_data_governed_ingestion_outputs.id", name="fk_analytical_output_governed", ondelete="RESTRICT"), nullable=False),
        sa.Column("governed_output_fingerprint", sa.String(64), nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("core_data_sources.id", name="fk_analytical_output_source", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_version_id", UUID, sa.ForeignKey("core_data_source_versions.id", name="fk_analytical_output_source_version", ondelete="RESTRICT"), nullable=False),
        sa.Column("ingestion_run_id", UUID, sa.ForeignKey("core_data_ingestion_runs.id", name="fk_analytical_output_run", ondelete="RESTRICT"), nullable=False),
        sa.Column("evaluation_id", UUID, sa.ForeignKey("core_data_ingestion_evaluations.id", name="fk_analytical_output_evaluation", ondelete="RESTRICT"), nullable=False),
        sa.Column("evaluation_fingerprint", sa.String(64), nullable=False),
        sa.Column("evaluation_decision", sa.String(24), nullable=False),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("privacy_category", sa.String(40), nullable=False),
        sa.Column("ai_use_policy", sa.String(64), nullable=False),
        *_scope_columns("analytical_output"),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("snapshot_id", "governed_output_id", name="uq_analytical_snapshot_output_edge"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_snapshot_output_product"),
        sa.CheckConstraint("evaluation_decision IN ('ACCEPTED', 'ACCEPTED_WITH_WARNING')", name="ck_analytical_snapshot_output_decision"),
    )
    op.create_index("ix_analytical_snapshot_output_lineage", "core_analytical_snapshot_governed_outputs", ["governed_output_id", "snapshot_id"])
    op.create_index("ix_analytical_snapshot_output_source", "core_analytical_snapshot_governed_outputs", ["source_version_id", "snapshot_id"])
    op.create_index("ix_core_analytical_snapshot_governed_outputs_snapshot_id", "core_analytical_snapshot_governed_outputs", ["snapshot_id"])

    op.create_table(
        "core_analytical_snapshot_record_inputs",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("snapshot_id", UUID, sa.ForeignKey("core_analytical_dataset_snapshots.id", name="fk_analytical_record_snapshot", ondelete="CASCADE"), nullable=False),
        sa.Column("governed_output_id", UUID, sa.ForeignKey("core_data_governed_ingestion_outputs.id", name="fk_analytical_record_output", ondelete="RESTRICT"), nullable=False),
        sa.Column("normalized_record_id", UUID, sa.ForeignKey("core_data_normalized_records.id", name="fk_analytical_record_normalized", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("core_data_sources.id", name="fk_analytical_record_source", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_version_id", UUID, sa.ForeignKey("core_data_source_versions.id", name="fk_analytical_record_source_version", ondelete="RESTRICT"), nullable=False),
        sa.Column("ingestion_run_id", UUID, sa.ForeignKey("core_data_ingestion_runs.id", name="fk_analytical_record_run", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_record_ordinal", sa.Integer(), nullable=False),
        sa.Column("source_locator", sa.String(1000), nullable=False),
        sa.Column("identity_fingerprint", sa.String(64), nullable=False),
        sa.Column("content_fingerprint", sa.String(64), nullable=False),
        *_scope_columns("analytical_record"),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("snapshot_id", "normalized_record_id", name="uq_analytical_snapshot_record_edge"),
        sa.CheckConstraint("source_record_ordinal >= 1", name="ck_analytical_snapshot_record_ordinal"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_snapshot_record_product"),
    )
    op.create_index("ix_analytical_snapshot_record_membership", "core_analytical_snapshot_record_inputs", ["snapshot_id", "source_id", "source_record_ordinal"])
    op.create_index("ix_analytical_snapshot_record_input", "core_analytical_snapshot_record_inputs", ["normalized_record_id", "snapshot_id"])
    op.create_index("ix_core_analytical_snapshot_record_inputs_snapshot_id", "core_analytical_snapshot_record_inputs", ["snapshot_id"])

    op.add_column("core_analytical_feature_snapshot_inputs", sa.Column("snapshot_lineage_mode", sa.String(32), nullable=False, server_default="LEGACY_SOURCE_VERSION"))
    op.add_column("core_analytical_feature_snapshot_inputs", sa.Column("dataset_contract_version_id", UUID, nullable=True))
    op.add_column("core_analytical_feature_snapshot_inputs", sa.Column("dataset_contract_fingerprint", sa.String(64), nullable=False, server_default=""))
    op.add_column("core_analytical_feature_snapshot_inputs", sa.Column("analytical_quality_state", sa.String(32), nullable=False, server_default="LEGACY_UNKNOWN"))
    op.create_foreign_key("fk_analytical_feature_input_contract", "core_analytical_feature_snapshot_inputs", "core_analytical_dataset_contract_versions", ["dataset_contract_version_id"], ["id"], ondelete="RESTRICT")


def downgrade() -> None:
    op.drop_constraint("fk_analytical_feature_input_contract", "core_analytical_feature_snapshot_inputs", type_="foreignkey")
    for column in ("analytical_quality_state", "dataset_contract_fingerprint", "dataset_contract_version_id", "snapshot_lineage_mode"):
        op.drop_column("core_analytical_feature_snapshot_inputs", column)
    op.drop_table("core_analytical_snapshot_record_inputs")
    op.drop_table("core_analytical_snapshot_governed_outputs")
    op.drop_index("ix_analytical_snapshot_contract", table_name="core_analytical_dataset_snapshots")
    op.drop_constraint("ck_analytical_snapshot_record_count", "core_analytical_dataset_snapshots", type_="check")
    op.drop_constraint("ck_analytical_snapshot_quality", "core_analytical_dataset_snapshots", type_="check")
    op.drop_constraint("ck_analytical_snapshot_lineage_mode", "core_analytical_dataset_snapshots", type_="check")
    op.drop_constraint("fk_analytical_snapshot_contract", "core_analytical_dataset_snapshots", type_="foreignkey")
    for column in ("record_count", "analytical_quality_state", "missing_value_policy", "granularity_key_fields_json", "temporal_key_fields_json", "temporal_mode", "lineage_mode", "dataset_contract_fingerprint", "dataset_contract_version_id"):
        op.drop_column("core_analytical_dataset_snapshots", column)
    op.drop_table("core_analytical_dataset_contract_versions")
