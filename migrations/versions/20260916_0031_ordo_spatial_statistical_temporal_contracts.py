"""Add ORDO spatial, statistical and temporal specification contracts.

Revision ID: 20260916_0031
Revises: 20260916_0030
Create Date: 2026-09-16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260916_0031"
down_revision = "20260916_0030"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def _human_lifecycle_columns() -> list[sa.Column]:
    return [
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("proposed_by_membership_id", UUID, nullable=True),
        sa.Column("proposed_at", TS, nullable=True),
        sa.Column("approved_by_membership_id", UUID, nullable=True),
        sa.Column("approved_at", TS, nullable=True),
        sa.Column("validation_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("validation_evidence_reference", sa.Text(), nullable=False, server_default=""),
        sa.Column("retired_by_membership_id", UUID, nullable=True),
        sa.Column("retired_at", TS, nullable=True),
        sa.Column("retirement_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
    ]


def _human_lifecycle_fks() -> list[sa.ForeignKeyConstraint]:
    return [
        sa.ForeignKeyConstraint([column], ["core_memberships.id"], ondelete="SET NULL")
        for column in (
            "created_by_membership_id", "proposed_by_membership_id", "approved_by_membership_id",
            "retired_by_membership_id",
        )
    ]


def upgrade() -> None:
    with op.batch_alter_table("ordo_indicator_methodologies") as batch:
        batch.drop_constraint("ck_ordo_indicator_methodology_status", type_="check")
        batch.add_column(sa.Column("proposed_by_membership_id", UUID, nullable=True))
        batch.add_column(sa.Column("proposed_at", TS, nullable=True))
        batch.add_column(sa.Column("retired_by_membership_id", UUID, nullable=True))
        batch.add_column(sa.Column("retired_at", TS, nullable=True))
        batch.add_column(sa.Column("retirement_note", sa.Text(), nullable=False, server_default=""))
        batch.create_foreign_key("fk_ordo_methodology_proposed_membership", "core_memberships", ["proposed_by_membership_id"], ["id"], ondelete="SET NULL")
        batch.create_foreign_key("fk_ordo_methodology_retired_membership", "core_memberships", ["retired_by_membership_id"], ["id"], ondelete="SET NULL")
        batch.create_check_constraint("ck_ordo_indicator_methodology_status", "status IN ('draft','proposed','validated','retired')")

    op.create_table(
        "ordo_spatial_aggregation_runs",
        sa.Column("id", UUID, nullable=False), sa.Column("organization_id", UUID, nullable=False),
        sa.Column("workspace_id", UUID, nullable=False), sa.Column("analytics_run_id", UUID, nullable=False),
        sa.Column("indicator_id", UUID, nullable=False), sa.Column("methodology_id", UUID, nullable=False),
        sa.Column("methodology_version", sa.Integer(), nullable=False),
        sa.Column("methodology_fingerprint", sa.String(64), nullable=False),
        sa.Column("target_spatial_unit_id", UUID, nullable=False),
        sa.Column("schema_version", sa.String(64), nullable=False),
        sa.Column("aggregation_rule", sa.String(16), nullable=False),
        sa.Column("boundary_version", sa.String(160), nullable=False),
        sa.Column("crs", sa.String(80), nullable=False),
        sa.Column("spatial_unit_type", sa.String(40), nullable=False),
        sa.Column("input_snapshot_sha256", sa.String(64), nullable=False),
        sa.Column("input_record_count", sa.Integer(), nullable=False),
        sa.Column("matched_record_count", sa.Integer(), nullable=False),
        sa.Column("dropped_missing_numeric_count", sa.Integer(), nullable=False),
        sa.Column("aggregate_numeric_value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(80), nullable=False, server_default=""),
        sa.Column("computation_trace", sa.JSON(), nullable=False),
        sa.Column("run_fingerprint", sa.String(64), nullable=False),
        sa.Column("weighted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("spatial_join_performed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("forecast_performed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("causal_claim", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("automatic_policy_recommendation", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_ordo_spatial_aggregation_runs"),
        sa.UniqueConstraint("analytics_run_id", "indicator_id", "target_spatial_unit_id", "methodology_id", name="uq_ordo_spatial_run_identity"),
        sa.CheckConstraint("schema_version = 'ORDO-SPATIAL-AGGREGATION-v1'", name="ck_ordo_spatial_run_schema"),
        sa.CheckConstraint("aggregation_rule IN ('count','sum','mean','min','max')", name="ck_ordo_spatial_run_rule"),
        sa.CheckConstraint("input_record_count >= 0 AND matched_record_count >= 0 AND dropped_missing_numeric_count >= 0", name="ck_ordo_spatial_run_counts"),
        sa.CheckConstraint("spatial_join_performed = false AND weighted = false AND forecast_performed = false AND causal_claim = false AND automatic_policy_recommendation = false", name="ck_ordo_spatial_run_locked_semantics"),
        sa.CheckConstraint("length(methodology_fingerprint) = 64 AND length(input_snapshot_sha256) = 64 AND length(run_fingerprint) = 64", name="ck_ordo_spatial_run_fingerprints"),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["core_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analytics_run_id"], ["ordo_analytics_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["indicator_id"], ["ordo_indicator_definitions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["methodology_id"], ["ordo_indicator_methodologies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_spatial_unit_id"], ["ordo_spatial_units.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ordo_spatial_run_scope_created", "ordo_spatial_aggregation_runs", ["organization_id", "workspace_id", "created_at"])

    op.create_table(
        "ordo_statistical_model_contracts",
        sa.Column("id", UUID, nullable=False), sa.Column("organization_id", UUID, nullable=False),
        sa.Column("workspace_id", UUID, nullable=False), sa.Column("analytics_run_id", UUID, nullable=False),
        sa.Column("target_indicator_id", UUID, nullable=False), sa.Column("target_methodology_id", UUID, nullable=False),
        sa.Column("target_methodology_version", sa.Integer(), nullable=False),
        sa.Column("methodology_fingerprint", sa.String(64), nullable=False),
        sa.Column("input_snapshot_sha256", sa.String(64), nullable=False),
        sa.Column("analysis_key", sa.String(140), nullable=False), sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(64), nullable=False),
        sa.Column("target_semantic", sa.String(40), nullable=False),
        sa.Column("analysis_structure", sa.String(32), nullable=False),
        sa.Column("model_family", sa.String(40), nullable=False),
        sa.Column("response_family", sa.String(40), nullable=False),
        sa.Column("contract_json", sa.JSON(), nullable=False),
        sa.Column("contract_fingerprint", sa.String(64), nullable=False),
        *_human_lifecycle_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_ordo_statistical_model_contracts"),
        sa.UniqueConstraint("workspace_id", "analysis_key", "version_no", name="uq_ordo_statistical_contract_version"),
        sa.CheckConstraint("status IN ('draft','proposed','validated','retired')", name="ck_ordo_statistical_contract_status"),
        sa.CheckConstraint("schema_version = 'ORDO-STATISTICAL-MODEL-CONTRACT-v1'", name="ck_ordo_statistical_contract_schema"),
        sa.CheckConstraint("version_no >= 1 AND target_methodology_version >= 1", name="ck_ordo_statistical_contract_versions"),
        sa.CheckConstraint("length(methodology_fingerprint) = 64 AND length(input_snapshot_sha256) = 64 AND length(contract_fingerprint) = 64", name="ck_ordo_statistical_contract_fingerprints"),
        sa.CheckConstraint("status != 'validated' OR (length(validation_note) > 0 AND length(validation_evidence_reference) > 0 AND approved_by_membership_id IS NOT NULL AND approved_at IS NOT NULL)", name="ck_ordo_statistical_contract_validation_trace"),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["core_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analytics_run_id"], ["ordo_analytics_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_indicator_id"], ["ordo_indicator_definitions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_methodology_id"], ["ordo_indicator_methodologies.id"], ondelete="RESTRICT"),
        *_human_lifecycle_fks(),
    )
    op.create_index("ix_ordo_statistical_contract_scope_status", "ordo_statistical_model_contracts", ["organization_id", "workspace_id", "status"])

    op.create_table(
        "ordo_time_series_specs",
        sa.Column("id", UUID, nullable=False), sa.Column("organization_id", UUID, nullable=False),
        sa.Column("workspace_id", UUID, nullable=False), sa.Column("analytics_run_id", UUID, nullable=False),
        sa.Column("target_indicator_id", UUID, nullable=False), sa.Column("target_methodology_id", UUID, nullable=False),
        sa.Column("target_methodology_version", sa.Integer(), nullable=False),
        sa.Column("methodology_fingerprint", sa.String(64), nullable=False),
        sa.Column("input_snapshot_sha256", sa.String(64), nullable=False),
        sa.Column("series_key", sa.String(140), nullable=False), sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(64), nullable=False),
        sa.Column("target_semantic", sa.String(40), nullable=False),
        sa.Column("frequency", sa.String(24), nullable=False),
        sa.Column("transformation", sa.String(32), nullable=False),
        sa.Column("contract_json", sa.JSON(), nullable=False),
        sa.Column("contract_fingerprint", sa.String(64), nullable=False),
        sa.Column("forecast_execution", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("automatic_model_selection", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("non_causal", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_human_lifecycle_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_ordo_time_series_specs"),
        sa.UniqueConstraint("workspace_id", "series_key", "version_no", name="uq_ordo_time_series_spec_version"),
        sa.CheckConstraint("status IN ('draft','proposed','validated','retired')", name="ck_ordo_time_series_spec_status"),
        sa.CheckConstraint("schema_version = 'ORDO-TIME-SERIES-SPEC-v1'", name="ck_ordo_time_series_spec_schema"),
        sa.CheckConstraint("version_no >= 1 AND target_methodology_version >= 1", name="ck_ordo_time_series_spec_versions"),
        sa.CheckConstraint("length(methodology_fingerprint) = 64 AND length(input_snapshot_sha256) = 64 AND length(contract_fingerprint) = 64", name="ck_ordo_time_series_spec_fingerprints"),
        sa.CheckConstraint("forecast_execution = false AND automatic_model_selection = false AND non_causal = true", name="ck_ordo_time_series_spec_locked_semantics"),
        sa.CheckConstraint("status != 'validated' OR (length(validation_note) > 0 AND length(validation_evidence_reference) > 0 AND approved_by_membership_id IS NOT NULL AND approved_at IS NOT NULL)", name="ck_ordo_time_series_spec_validation_trace"),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["core_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analytics_run_id"], ["ordo_analytics_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_indicator_id"], ["ordo_indicator_definitions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_methodology_id"], ["ordo_indicator_methodologies.id"], ondelete="RESTRICT"),
        *_human_lifecycle_fks(),
    )
    op.create_index("ix_ordo_time_series_spec_scope_status", "ordo_time_series_specs", ["organization_id", "workspace_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_ordo_time_series_spec_scope_status", table_name="ordo_time_series_specs")
    op.drop_table("ordo_time_series_specs")
    op.drop_index("ix_ordo_statistical_contract_scope_status", table_name="ordo_statistical_model_contracts")
    op.drop_table("ordo_statistical_model_contracts")
    op.drop_index("ix_ordo_spatial_run_scope_created", table_name="ordo_spatial_aggregation_runs")
    op.drop_table("ordo_spatial_aggregation_runs")
    op.execute("UPDATE ordo_indicator_methodologies SET status = 'draft' WHERE status = 'proposed'")
    with op.batch_alter_table("ordo_indicator_methodologies") as batch:
        batch.drop_constraint("ck_ordo_indicator_methodology_status", type_="check")
        batch.drop_constraint("fk_ordo_methodology_retired_membership", type_="foreignkey")
        batch.drop_constraint("fk_ordo_methodology_proposed_membership", type_="foreignkey")
        batch.drop_column("retirement_note")
        batch.drop_column("retired_at")
        batch.drop_column("retired_by_membership_id")
        batch.drop_column("proposed_at")
        batch.drop_column("proposed_by_membership_id")
        batch.create_check_constraint("ck_ordo_indicator_methodology_status", "status IN ('draft','validated','retired')")
