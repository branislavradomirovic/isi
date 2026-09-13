"""Add governed ingestion operations, quality, backfill, and provenance.

Revision ID: 20260913_0024
Revises: 20260913_0023
Create Date: 2026-09-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260913_0024"
down_revision = "20260913_0023"
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
        "core_data_ingestion_operational_policy_versions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("core_data_sources.id", name="fk_ing_op_policy_source", ondelete="RESTRICT"), nullable=False),
        sa.Column("connector_contract_version_id", UUID, sa.ForeignKey("core_data_connector_contract_versions.id", name="fk_ing_op_policy_connector", ondelete="RESTRICT"), nullable=False),
        sa.Column("schema_mapping_version_id", UUID, sa.ForeignKey("core_data_source_schema_mapping_versions.id", name="fk_ing_op_policy_mapping", ondelete="RESTRICT"), nullable=False),
        sa.Column("record_governance_policy_version_id", UUID, sa.ForeignKey("core_data_record_governance_policy_versions.id", name="fk_ing_op_policy_rec_policy", ondelete="RESTRICT"), nullable=False),
        *_scope_columns("ing_op_policy"),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("contract_format_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("freshness_contract_json", sa.Text(), nullable=False),
        sa.Column("quality_contract_json", sa.Text(), nullable=False),
        sa.Column("backfill_contract_json", sa.Text(), nullable=False),
        sa.Column("dead_letter_contract_json", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("lifecycle_state", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", name="fk_ing_op_policy_created_by", ondelete="SET NULL"), nullable=True),
        sa.Column("activated_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", name="fk_ing_op_policy_activated_by", ondelete="SET NULL"), nullable=True),
        sa.Column("retired_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", name="fk_ing_op_policy_retired_by", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("activated_at", TS, nullable=True), sa.Column("retired_at", TS, nullable=True),
        sa.UniqueConstraint("source_id", "version_no", name="uq_ing_op_policy_source_version"),
        sa.CheckConstraint("version_no >= 1", name="ck_ing_op_policy_version_no"),
        sa.CheckConstraint("contract_format_version = 1", name="ck_ing_op_policy_format"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_ing_op_policy_product"),
        sa.CheckConstraint("lifecycle_state IN ('DRAFT', 'ACTIVE', 'RETIRED')", name="ck_ing_op_policy_lifecycle"),
    )
    op.create_index("ix_ing_op_policy_scope", "core_data_ingestion_operational_policy_versions", ["organization_id", "workspace_id", "product_code"])
    op.create_index("ix_ing_op_policy_binding", "core_data_ingestion_operational_policy_versions", ["source_id", "connector_contract_version_id", "schema_mapping_version_id", "record_governance_policy_version_id"])
    op.create_index("ix_ing_op_policy_source_state", "core_data_ingestion_operational_policy_versions", ["source_id", "lifecycle_state"])
    op.create_index("uq_ing_op_policy_active_source", "core_data_ingestion_operational_policy_versions", ["source_id"], unique=True,
                    postgresql_where=sa.text("lifecycle_state = 'ACTIVE'"), sqlite_where=sa.text("lifecycle_state = 'ACTIVE'"))

    op.add_column("core_data_ingestion_runs", sa.Column("operational_policy_version_id", UUID, nullable=True))
    op.add_column("core_data_ingestion_runs", sa.Column("execution_mode", sa.String(16), nullable=False, server_default="INCREMENTAL"))
    op.add_column("core_data_ingestion_runs", sa.Column("window_start_cursor", sa.String(1000), nullable=False, server_default=""))
    op.add_column("core_data_ingestion_runs", sa.Column("window_end_cursor", sa.String(1000), nullable=False, server_default=""))
    op.add_column("core_data_ingestion_runs", sa.Column("replay_of_run_id", UUID, nullable=True))
    op.add_column("core_data_ingestion_runs", sa.Column("source_observed_at", TS, nullable=True))
    op.add_column("core_data_ingestion_runs", sa.Column("forward_cursor_committed", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_foreign_key("fk_ing_run_op_policy", "core_data_ingestion_runs", "core_data_ingestion_operational_policy_versions", ["operational_policy_version_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_ing_run_replay_parent", "core_data_ingestion_runs", "core_data_ingestion_runs", ["replay_of_run_id"], ["id"], ondelete="RESTRICT")
    op.create_check_constraint("ck_ing_run_execution_mode", "core_data_ingestion_runs", "execution_mode IN ('INCREMENTAL', 'BACKFILL', 'REPLAY')")
    op.create_index("ix_ing_run_op_policy", "core_data_ingestion_runs", ["operational_policy_version_id"])
    op.create_index("ix_ing_run_replay_parent", "core_data_ingestion_runs", ["replay_of_run_id"])
    op.execute("UPDATE core_data_ingestion_runs SET execution_mode = 'INCREMENTAL', forward_cursor_committed = CASE WHEN status = 'SUCCEEDED' THEN true ELSE false END")

    op.create_table(
        "core_data_ingestion_evaluations",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("core_data_sources.id", name="fk_ing_eval_source", ondelete="RESTRICT"), nullable=False),
        sa.Column("ingestion_run_id", UUID, sa.ForeignKey("core_data_ingestion_runs.id", name="fk_ing_eval_run", ondelete="RESTRICT"), nullable=False),
        sa.Column("operational_policy_version_id", UUID, sa.ForeignKey("core_data_ingestion_operational_policy_versions.id", name="fk_ing_eval_policy", ondelete="RESTRICT"), nullable=False),
        *_scope_columns("ing_eval"),
        sa.Column("freshness_status", sa.String(24), nullable=False), sa.Column("quality_status", sa.String(16), nullable=False),
        sa.Column("decision", sa.String(24), nullable=False), sa.Column("freshness_details_json", sa.Text(), nullable=False),
        sa.Column("quality_details_json", sa.Text(), nullable=False), sa.Column("record_metrics_json", sa.Text(), nullable=False),
        sa.Column("evidence_fingerprint", sa.String(64), nullable=False),
        sa.Column("evaluated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("ingestion_run_id", name="uq_ing_eval_run"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_ing_eval_product"),
        sa.CheckConstraint("freshness_status IN ('FRESH', 'STALE_WARNING', 'STALE_REJECTED', 'UNKNOWN', 'NOT_APPLICABLE')", name="ck_ing_eval_freshness"),
        sa.CheckConstraint("quality_status IN ('PASS', 'WARNING', 'REJECTED', 'UNKNOWN')", name="ck_ing_eval_quality"),
        sa.CheckConstraint("decision IN ('ACCEPTED', 'ACCEPTED_WITH_WARNING', 'REJECTED', 'DEAD_LETTERED')", name="ck_ing_eval_decision"),
    )
    op.create_index("ix_ing_eval_scope", "core_data_ingestion_evaluations", ["organization_id", "workspace_id", "product_code"])

    op.create_table(
        "core_data_ingestion_dead_letters",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("core_data_sources.id", name="fk_ing_dead_source", ondelete="RESTRICT"), nullable=False),
        sa.Column("ingestion_run_id", UUID, sa.ForeignKey("core_data_ingestion_runs.id", name="fk_ing_dead_run", ondelete="RESTRICT"), nullable=False),
        sa.Column("evaluation_id", UUID, sa.ForeignKey("core_data_ingestion_evaluations.id", name="fk_ing_dead_eval", ondelete="RESTRICT"), nullable=True),
        sa.Column("operational_policy_version_id", UUID, sa.ForeignKey("core_data_ingestion_operational_policy_versions.id", name="fk_ing_dead_policy", ondelete="RESTRICT"), nullable=False),
        *_scope_columns("ing_dead"),
        sa.Column("reason_code", sa.String(120), nullable=False), sa.Column("error_category", sa.String(120), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(16), nullable=False, server_default="OPEN"),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")), sa.Column("resolved_at", TS, nullable=True),
        sa.Column("resolver_membership_id", UUID, sa.ForeignKey("core_memberships.id", name="fk_ing_dead_resolver", ondelete="SET NULL"), nullable=True),
        sa.Column("resolution_note", sa.String(1000), nullable=False, server_default=""),
        sa.Column("replacement_run_id", UUID, sa.ForeignKey("core_data_ingestion_runs.id", name="fk_ing_dead_replacement", ondelete="RESTRICT"), nullable=True),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_ing_dead_product"),
        sa.CheckConstraint("status IN ('OPEN', 'REQUEUED', 'RESOLVED', 'DISCARDED')", name="ck_ing_dead_status"),
    )
    op.create_index("ix_ing_dead_scope", "core_data_ingestion_dead_letters", ["organization_id", "workspace_id", "product_code"])
    op.create_index("ix_ing_dead_run_reason", "core_data_ingestion_dead_letters", ["ingestion_run_id", "reason_code"])
    op.create_index("uq_ing_dead_open_run_reason", "core_data_ingestion_dead_letters", ["ingestion_run_id", "reason_code"], unique=True,
                    postgresql_where=sa.text("status = 'OPEN'"), sqlite_where=sa.text("status = 'OPEN'"))

    op.create_table(
        "core_data_governed_ingestion_outputs",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("core_data_sources.id", name="fk_gov_ing_output_source", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_version_id", UUID, sa.ForeignKey("core_data_source_versions.id", name="fk_gov_ing_output_version", ondelete="RESTRICT"), nullable=False),
        sa.Column("ingestion_run_id", UUID, sa.ForeignKey("core_data_ingestion_runs.id", name="fk_gov_ing_output_run", ondelete="RESTRICT"), nullable=False),
        sa.Column("evaluation_id", UUID, sa.ForeignKey("core_data_ingestion_evaluations.id", name="fk_gov_ing_output_eval", ondelete="RESTRICT"), nullable=False),
        sa.Column("connector_contract_version_id", UUID, sa.ForeignKey("core_data_connector_contract_versions.id", name="fk_gov_ing_output_connector", ondelete="RESTRICT"), nullable=False),
        sa.Column("schema_mapping_version_id", UUID, sa.ForeignKey("core_data_source_schema_mapping_versions.id", name="fk_gov_ing_output_mapping", ondelete="RESTRICT"), nullable=False),
        sa.Column("record_governance_policy_version_id", UUID, sa.ForeignKey("core_data_record_governance_policy_versions.id", name="fk_gov_ing_output_rec_policy", ondelete="RESTRICT"), nullable=False),
        sa.Column("operational_policy_version_id", UUID, sa.ForeignKey("core_data_ingestion_operational_policy_versions.id", name="fk_gov_ing_output_op_policy", ondelete="RESTRICT"), nullable=False),
        *_scope_columns("gov_ing_output"),
        sa.Column("contract_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("record_count", sa.Integer(), nullable=False), sa.Column("current_record_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_record_count", sa.Integer(), nullable=False), sa.Column("quarantined_record_count", sa.Integer(), nullable=False),
        sa.Column("superseded_record_count", sa.Integer(), nullable=False), sa.Column("output_fingerprint", sa.String(64), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("ingestion_run_id", name="uq_gov_ing_output_run"),
        sa.UniqueConstraint("evaluation_id", name="uq_gov_ing_output_evaluation"),
        sa.CheckConstraint("contract_version = 1", name="ck_gov_ing_output_contract"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_gov_ing_output_product"),
        sa.CheckConstraint("record_count >= 0 AND current_record_count >= 0 AND duplicate_record_count >= 0 AND quarantined_record_count >= 0 AND superseded_record_count >= 0", name="ck_gov_ing_output_counts"),
    )
    op.create_index("ix_gov_ing_output_scope", "core_data_governed_ingestion_outputs", ["organization_id", "workspace_id", "product_code"])


def downgrade() -> None:
    op.drop_table("core_data_governed_ingestion_outputs")
    op.drop_table("core_data_ingestion_dead_letters")
    op.drop_table("core_data_ingestion_evaluations")
    op.drop_index("ix_ing_run_replay_parent", table_name="core_data_ingestion_runs")
    op.drop_index("ix_ing_run_op_policy", table_name="core_data_ingestion_runs")
    op.drop_constraint("ck_ing_run_execution_mode", "core_data_ingestion_runs", type_="check")
    op.drop_constraint("fk_ing_run_replay_parent", "core_data_ingestion_runs", type_="foreignkey")
    op.drop_constraint("fk_ing_run_op_policy", "core_data_ingestion_runs", type_="foreignkey")
    for column in ("forward_cursor_committed", "source_observed_at", "replay_of_run_id", "window_end_cursor", "window_start_cursor", "execution_mode", "operational_policy_version_id"):
        op.drop_column("core_data_ingestion_runs", column)
    op.drop_table("core_data_ingestion_operational_policy_versions")
