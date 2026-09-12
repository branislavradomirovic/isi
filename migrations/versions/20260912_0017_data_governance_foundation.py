"""Add conservative data governance and retention foundations.

Revision ID: 20260912_0017
Revises: 20260911_0016
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260912_0017"
down_revision = "20260911_0016"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def _derived_uuid_sql(prefix: str, identifier_sql: str) -> str:
    digest = f"md5('{prefix}' || CAST({identifier_sql} AS TEXT))"
    return (
        "CAST(substr({0}, 1, 8) || '-' || substr({0}, 9, 4) || '-' || "
        "substr({0}, 13, 4) || '-' || substr({0}, 17, 4) || '-' || substr({0}, 21, 12) AS UUID)"
    ).format(digest)


def upgrade() -> None:
    op.create_table(
        "core_data_retention_policies",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("policy_code", sa.String(120), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("retention_days", sa.Integer(), nullable=True),
        sa.Column("no_auto_delete", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("manual_review_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("archive_before_purge", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("tombstone_retention_days", sa.Integer(), nullable=True),
        sa.Column("reference_text", sa.String(1000), nullable=False, server_default=""),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint(
            "workspace_id", "policy_code", "version_no", name="uq_core_data_retention_policies_workspace_code_version"
        ),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_retention_policies_product"),
        sa.CheckConstraint("version_no >= 1", name="ck_core_data_retention_policies_version"),
        sa.CheckConstraint("status IN ('active', 'retired')", name="ck_core_data_retention_policies_status"),
        sa.CheckConstraint("retention_days IS NULL OR retention_days >= 0", name="ck_core_data_retention_policies_days"),
        sa.CheckConstraint(
            "tombstone_retention_days IS NULL OR tombstone_retention_days >= 0",
            name="ck_core_data_retention_policies_tombstone_days",
        ),
    )
    op.create_index("ix_core_data_retention_policies_organization_id", "core_data_retention_policies", ["organization_id"])
    op.create_index("ix_core_data_retention_policies_workspace_id", "core_data_retention_policies", ["workspace_id"])
    op.create_index("ix_core_data_retention_policies_product_code", "core_data_retention_policies", ["product_code"])

    op.create_table(
        "core_data_source_governance_profiles",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("core_data_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("classification", sa.String(32), nullable=False, server_default="UNCLASSIFIED"),
        sa.Column("privacy_category", sa.String(40), nullable=False, server_default="UNKNOWN"),
        sa.Column("processing_purpose", sa.String(1000), nullable=False, server_default=""),
        sa.Column("data_owner_ref", sa.String(300), nullable=False, server_default=""),
        sa.Column("data_steward_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("retention_policy_id", UUID, sa.ForeignKey("core_data_retention_policies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ai_use_policy", sa.String(64), nullable=False, server_default="PROHIBITED"),
        sa.Column("export_policy", sa.String(32), nullable=False, server_default="PROHIBITED"),
        sa.Column("governance_state", sa.String(24), nullable=False, server_default="DRAFT"),
        sa.Column("classification_rationale", sa.String(1000), nullable=False, server_default=""),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("source_id", name="uq_core_data_source_governance_profiles_source_id"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_source_governance_profiles_product"),
        sa.CheckConstraint(
            "classification IN ('UNCLASSIFIED', 'PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED')",
            name="ck_core_data_source_governance_profiles_classification",
        ),
        sa.CheckConstraint(
            "privacy_category IN ('NONE_DECLARED', 'AGGREGATE_NON_PERSONAL', 'PSEUDONYMOUS_OR_LINKABLE', "
            "'PERSONAL_DATA', 'SENSITIVE_PERSONAL_DATA', 'UNKNOWN')",
            name="ck_core_data_source_governance_profiles_privacy",
        ),
        sa.CheckConstraint(
            "ai_use_policy IN ('PROHIBITED', 'LOCAL_ANALYSIS_ONLY', 'RAG_RETRIEVAL_ALLOWED', "
            "'MODEL_EVALUATION_ALLOWED', 'MODEL_TRAINING_REQUIRES_SEPARATE_APPROVAL')",
            name="ck_core_data_source_governance_profiles_ai_use",
        ),
        sa.CheckConstraint("export_policy = 'PROHIBITED'", name="ck_core_data_source_governance_profiles_export"),
        sa.CheckConstraint(
            "governance_state IN ('DRAFT', 'GOVERNED', 'FROZEN', 'RETIRED')",
            name="ck_core_data_source_governance_profiles_state",
        ),
        sa.CheckConstraint("revision >= 1", name="ck_core_data_source_governance_profiles_revision"),
    )
    op.create_index("ix_core_data_source_governance_profiles_source_id", "core_data_source_governance_profiles", ["source_id"])
    op.create_index("ix_core_data_source_governance_profiles_organization_id", "core_data_source_governance_profiles", ["organization_id"])
    op.create_index("ix_core_data_source_governance_profiles_workspace_id", "core_data_source_governance_profiles", ["workspace_id"])
    op.create_index("ix_core_data_source_governance_profiles_product_code", "core_data_source_governance_profiles", ["product_code"])

    op.create_table(
        "core_data_retention_states",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("version_id", UUID, sa.ForeignKey("core_data_source_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("core_data_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("retention_start_at", TS, nullable=True),
        sa.Column("retention_due_at", TS, nullable=True),
        sa.Column("hold_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("hold_reason_ref", sa.String(500), nullable=False, server_default=""),
        sa.Column("purge_requested_at", TS, nullable=True),
        sa.Column("purge_requested_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("purge_approved_at", TS, nullable=True),
        sa.Column("purge_approved_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("purge_executed_at", TS, nullable=True),
        sa.Column("purge_executed_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("purge_result", sa.String(500), nullable=False, server_default=""),
        sa.Column("tombstone_checksum", sa.String(64), nullable=False, server_default=""),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("version_id", name="uq_core_data_retention_states_version_id"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_retention_states_product"),
    )
    op.create_index("ix_core_data_retention_states_version_id", "core_data_retention_states", ["version_id"])
    op.create_index("ix_core_data_retention_states_source_id", "core_data_retention_states", ["source_id"])
    op.create_index("ix_core_data_retention_states_organization_id", "core_data_retention_states", ["organization_id"])
    op.create_index("ix_core_data_retention_states_workspace_id", "core_data_retention_states", ["workspace_id"])
    op.create_index("ix_core_data_retention_states_product_code", "core_data_retention_states", ["product_code"])

    governance_id = _derived_uuid_sql("isi21-governance:", "source.id")
    op.execute(
        sa.text(
            f"""
            INSERT INTO core_data_source_governance_profiles (
                id, source_id, organization_id, workspace_id, product_code,
                classification, privacy_category, processing_purpose, data_owner_ref,
                data_steward_membership_id, retention_policy_id, ai_use_policy,
                export_policy, governance_state, classification_rationale, revision,
                created_by_membership_id, updated_by_membership_id, created_at, updated_at
            )
            SELECT
                {governance_id}, source.id, source.organization_id, source.workspace_id, source.product_code,
                'UNCLASSIFIED', 'UNKNOWN', '', '', NULL, NULL, 'PROHIBITED',
                'PROHIBITED', 'DRAFT', '', 1, NULL, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM core_data_sources AS source
            """
        )
    )

    retention_state_id = _derived_uuid_sql("isi21-retention-state:", "version.id")
    op.execute(
        sa.text(
            f"""
            INSERT INTO core_data_retention_states (
                id, version_id, source_id, organization_id, workspace_id, product_code,
                retention_start_at, retention_due_at, hold_active, hold_reason_ref,
                purge_requested_at, purge_requested_by_membership_id,
                purge_approved_at, purge_approved_by_membership_id,
                purge_executed_at, purge_executed_by_membership_id,
                purge_result, tombstone_checksum, created_at, updated_at
            )
            SELECT
                {retention_state_id}, version.id, version.source_id, version.organization_id,
                version.workspace_id, version.product_code, version.created_at, NULL, false, '',
                NULL, NULL, NULL, NULL, NULL, NULL, '', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM core_data_source_versions AS version
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_core_data_retention_states_product_code", table_name="core_data_retention_states")
    op.drop_index("ix_core_data_retention_states_workspace_id", table_name="core_data_retention_states")
    op.drop_index("ix_core_data_retention_states_organization_id", table_name="core_data_retention_states")
    op.drop_index("ix_core_data_retention_states_source_id", table_name="core_data_retention_states")
    op.drop_index("ix_core_data_retention_states_version_id", table_name="core_data_retention_states")
    op.drop_table("core_data_retention_states")
    op.drop_index("ix_core_data_source_governance_profiles_product_code", table_name="core_data_source_governance_profiles")
    op.drop_index("ix_core_data_source_governance_profiles_workspace_id", table_name="core_data_source_governance_profiles")
    op.drop_index("ix_core_data_source_governance_profiles_organization_id", table_name="core_data_source_governance_profiles")
    op.drop_index("ix_core_data_source_governance_profiles_source_id", table_name="core_data_source_governance_profiles")
    op.drop_table("core_data_source_governance_profiles")
    op.drop_index("ix_core_data_retention_policies_product_code", table_name="core_data_retention_policies")
    op.drop_index("ix_core_data_retention_policies_workspace_id", table_name="core_data_retention_policies")
    op.drop_index("ix_core_data_retention_policies_organization_id", table_name="core_data_retention_policies")
    op.drop_table("core_data_retention_policies")
