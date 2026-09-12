"""Enforce governed retention, purge, anonymization, and export controls.

Revision ID: 20260912_0018
Revises: 20260912_0017
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260912_0018"
down_revision = "20260912_0017"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def _uuid_sql(seed_sql: str) -> str:
    digest = f"md5({seed_sql})"
    return (
        "CAST(substr({0}, 1, 8) || '-' || substr({0}, 9, 4) || '-' || "
        "substr({0}, 13, 4) || '-' || substr({0}, 17, 4) || '-' || substr({0}, 21, 12) AS UUID)"
    ).format(digest)


def upgrade() -> None:
    op.add_column("core_data_source_versions", sa.Column("content_state", sa.String(16), nullable=False, server_default="AVAILABLE"))
    op.create_check_constraint("ck_core_data_source_versions_content_state", "core_data_source_versions", "content_state IN ('AVAILABLE', 'PURGED')")
    op.create_index(
        "ix_data_versions_scope_storage_content", "core_data_source_versions",
        ["organization_id", "workspace_id", "product_code", "storage_key", "content_state"],
    )

    op.add_column("core_data_retention_states", sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("core_data_retention_states", sa.Column("purge_status", sa.String(16), nullable=False, server_default="NONE"))
    op.add_column("core_data_retention_states", sa.Column("hold_placed_at", TS, nullable=True))
    op.add_column("core_data_retention_states", sa.Column("hold_placed_by_membership_id", UUID, nullable=True))
    op.add_column("core_data_retention_states", sa.Column("hold_released_at", TS, nullable=True))
    op.add_column("core_data_retention_states", sa.Column("hold_released_by_membership_id", UUID, nullable=True))
    op.create_foreign_key("fk_retention_hold_placed_member", "core_data_retention_states", "core_memberships", ["hold_placed_by_membership_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_retention_hold_released_member", "core_data_retention_states", "core_memberships", ["hold_released_by_membership_id"], ["id"], ondelete="SET NULL")
    op.create_check_constraint("ck_core_data_retention_states_revision", "core_data_retention_states", "revision >= 1")
    op.create_check_constraint(
        "ck_core_data_retention_states_purge_status", "core_data_retention_states",
        "purge_status IN ('NONE', 'REQUESTED', 'APPROVED', 'EXECUTING', 'EXECUTED', 'FAILED')",
    )

    op.drop_constraint("ck_core_data_source_governance_profiles_export", "core_data_source_governance_profiles", type_="check")
    op.create_check_constraint(
        "ck_core_data_source_governance_profiles_export", "core_data_source_governance_profiles",
        "export_policy IN ('PROHIBITED', 'GOVERNED_EXPORT_ALLOWED')",
    )

    op.create_table(
        "core_data_anonymization_records",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("input_version_id", UUID, sa.ForeignKey("core_data_source_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("output_version_id", UUID, sa.ForeignKey("core_data_source_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("method_code", sa.String(120), nullable=False),
        sa.Column("method_version", sa.String(120), nullable=False),
        sa.Column("method_reference", sa.String(500), nullable=False),
        sa.Column("parameter_reference", sa.String(1000), nullable=False, server_default=""),
        sa.Column("evidence_checksum", sa.String(64), nullable=False, server_default=""),
        sa.Column("evidence_reference", sa.String(1000), nullable=False),
        sa.Column("classification_before", sa.String(32), nullable=False),
        sa.Column("classification_after", sa.String(32), nullable=False),
        sa.Column("privacy_category_before", sa.String(40), nullable=False),
        sa.Column("privacy_category_after", sa.String(40), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="PROPOSED"),
        sa.Column("proposed_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("proposed_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("reviewed_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", TS, nullable=True),
        sa.Column("review_reference", sa.String(1000), nullable=False, server_default=""),
        sa.Column("review_reason", sa.String(1000), nullable=False, server_default=""),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_anonymization_product"),
        sa.CheckConstraint("status IN ('PROPOSED', 'VERIFIED', 'REJECTED')", name="ck_core_data_anonymization_status"),
        sa.CheckConstraint("input_version_id <> output_version_id", name="ck_core_data_anonymization_versions"),
        sa.CheckConstraint(
            "classification_before IN ('UNCLASSIFIED', 'PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED') "
            "AND classification_after IN ('UNCLASSIFIED', 'PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED')",
            name="ck_core_data_anonymization_classification",
        ),
        sa.CheckConstraint(
            "privacy_category_before IN ('NONE_DECLARED', 'AGGREGATE_NON_PERSONAL', 'PSEUDONYMOUS_OR_LINKABLE', "
            "'PERSONAL_DATA', 'SENSITIVE_PERSONAL_DATA', 'UNKNOWN') AND privacy_category_after IN "
            "('NONE_DECLARED', 'AGGREGATE_NON_PERSONAL', 'PSEUDONYMOUS_OR_LINKABLE', 'PERSONAL_DATA', "
            "'SENSITIVE_PERSONAL_DATA', 'UNKNOWN')",
            name="ck_core_data_anonymization_privacy",
        ),
    )
    for column in ("organization_id", "workspace_id", "product_code", "input_version_id", "output_version_id"):
        op.create_index(f"ix_core_data_anonymization_records_{column}", "core_data_anonymization_records", [column])

    op.create_table(
        "core_data_export_manifests",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("core_data_sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_version_id", UUID, sa.ForeignKey("core_data_source_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("purpose_reference", sa.String(1000), nullable=False),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("privacy_category", sa.String(40), nullable=False),
        sa.Column("governance_revision", sa.Integer(), nullable=False),
        sa.Column("content_checksum", sa.String(64), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("assurance_method", sa.String(24), nullable=False, server_default=""),
        sa.Column("assurance_reference", sa.String(200), nullable=False, server_default=""),
        sa.Column("result_code", sa.String(120), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("completed_at", TS, nullable=True),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_export_manifests_product"),
        sa.CheckConstraint("outcome IN ('COMPLETED', 'DENIED', 'FAILED')", name="ck_core_data_export_manifests_outcome"),
    )
    for column in ("organization_id", "workspace_id", "product_code", "source_id", "source_version_id"):
        op.create_index(f"ix_core_data_export_manifests_{column}", "core_data_export_manifests", [column])
    op.execute(sa.text("""
        CREATE FUNCTION core_data_export_manifests_immutable() RETURNS trigger AS $$
        BEGIN RAISE EXCEPTION 'data export manifests are immutable'; END; $$ LANGUAGE plpgsql
    """))
    op.execute(sa.text("""
        CREATE TRIGGER tr_core_data_export_manifests_immutable
        BEFORE UPDATE OR DELETE ON core_data_export_manifests
        FOR EACH ROW EXECUTE FUNCTION core_data_export_manifests_immutable()
    """))

    op.create_table(
        "core_data_governance_invalidations",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("upstream_entity_type", sa.String(40), nullable=False, server_default="source_version"),
        sa.Column("upstream_version_id", UUID, sa.ForeignKey("core_data_source_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reason", sa.String(24), nullable=False, server_default="PURGED"),
        sa.Column("actor_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("upstream_version_id", "reason", name="uq_core_data_governance_invalidation_version_reason"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_invalidation_product"),
        sa.CheckConstraint("upstream_entity_type = 'source_version'", name="ck_core_data_invalidation_entity"),
        sa.CheckConstraint("reason = 'PURGED'", name="ck_core_data_invalidation_reason"),
    )
    for column in ("organization_id", "workspace_id", "product_code", "upstream_version_id"):
        op.create_index(f"ix_core_data_governance_invalidations_{column}", "core_data_governance_invalidations", [column])

    permission_id = _uuid_sql("'isi21b-permission:' || permission_code")
    op.execute(sa.text(f"""
        INSERT INTO core_permissions (id, code, description)
        SELECT {permission_id}, permission_code, permission_code
        FROM (VALUES ('data.governance.manage'), ('data.export')) AS requested(permission_code)
        WHERE NOT EXISTS (SELECT 1 FROM core_permissions existing WHERE existing.code = requested.permission_code)
    """))
    op.execute(sa.text("""
        INSERT INTO core_role_permissions (role_id, permission_id)
        SELECT role.id, permission.id
        FROM core_roles role
        JOIN (VALUES
            ('organization_admin', 'data.governance.manage'),
            ('organization_admin', 'data.export'),
            ('domain_manager', 'data.governance.manage'),
            ('domain_manager', 'data.export'),
            ('data_manager', 'data.governance.manage'),
            ('data_manager', 'data.export'),
            ('analyst', 'data.export')
        ) AS requested(role_code, permission_code) ON requested.role_code = role.code
        JOIN core_permissions permission ON permission.code = requested.permission_code
        WHERE NOT EXISTS (
            SELECT 1 FROM core_role_permissions existing
            WHERE existing.role_id = role.id AND existing.permission_id = permission.id
        )
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DELETE FROM core_role_permissions
        WHERE permission_id IN (SELECT id FROM core_permissions WHERE code IN ('data.governance.manage', 'data.export'))
    """))
    op.execute(sa.text("DELETE FROM core_permissions WHERE code IN ('data.governance.manage', 'data.export')"))

    for column in reversed(("organization_id", "workspace_id", "product_code", "upstream_version_id")):
        op.drop_index(f"ix_core_data_governance_invalidations_{column}", table_name="core_data_governance_invalidations")
    op.drop_table("core_data_governance_invalidations")

    op.execute(sa.text("DROP TRIGGER tr_core_data_export_manifests_immutable ON core_data_export_manifests"))
    op.execute(sa.text("DROP FUNCTION core_data_export_manifests_immutable()"))
    for column in reversed(("organization_id", "workspace_id", "product_code", "source_id", "source_version_id")):
        op.drop_index(f"ix_core_data_export_manifests_{column}", table_name="core_data_export_manifests")
    op.drop_table("core_data_export_manifests")

    for column in reversed(("organization_id", "workspace_id", "product_code", "input_version_id", "output_version_id")):
        op.drop_index(f"ix_core_data_anonymization_records_{column}", table_name="core_data_anonymization_records")
    op.drop_table("core_data_anonymization_records")

    op.execute(sa.text("UPDATE core_data_source_governance_profiles SET export_policy = 'PROHIBITED'"))
    op.drop_constraint("ck_core_data_source_governance_profiles_export", "core_data_source_governance_profiles", type_="check")
    op.create_check_constraint("ck_core_data_source_governance_profiles_export", "core_data_source_governance_profiles", "export_policy = 'PROHIBITED'")

    op.drop_constraint("ck_core_data_retention_states_purge_status", "core_data_retention_states", type_="check")
    op.drop_constraint("ck_core_data_retention_states_revision", "core_data_retention_states", type_="check")
    op.drop_constraint("fk_retention_hold_released_member", "core_data_retention_states", type_="foreignkey")
    op.drop_constraint("fk_retention_hold_placed_member", "core_data_retention_states", type_="foreignkey")
    for column in ("hold_released_by_membership_id", "hold_released_at", "hold_placed_by_membership_id", "hold_placed_at", "purge_status", "revision"):
        op.drop_column("core_data_retention_states", column)

    op.drop_index("ix_data_versions_scope_storage_content", table_name="core_data_source_versions")
    op.drop_constraint("ck_core_data_source_versions_content_state", "core_data_source_versions", type_="check")
    op.drop_column("core_data_source_versions", "content_state")
