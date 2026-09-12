"""Add governed analytical datasets, snapshots, features, and typed lineage.

Revision ID: 20260912_0019
Revises: 20260912_0018
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260912_0019"
down_revision = "20260912_0018"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def _scope_columns():
    return (
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
    )


def _audit_columns(*, updated: bool = True):
    values = [
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]
    if updated:
        values.extend([
            sa.Column("updated_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
            sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        ])
    return tuple(values)


def upgrade() -> None:
    op.create_table(
        "core_analytical_datasets",
        sa.Column("id", UUID, primary_key=True, nullable=False), *_scope_columns(),
        sa.Column("code", sa.String(120), nullable=False), sa.Column("name", sa.String(240), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False, server_default=""),
        sa.Column("methodology_reference", sa.String(500), nullable=False),
        sa.Column("methodology_version", sa.String(120), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"), *_audit_columns(),
        sa.UniqueConstraint("workspace_id", "product_code", "code", name="uq_analytical_dataset_scope_code"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_dataset_product"),
        sa.CheckConstraint("revision >= 1", name="ck_analytical_dataset_revision"),
    )
    op.create_index("ix_analytical_dataset_scope", "core_analytical_datasets", ["organization_id", "workspace_id", "product_code"])

    op.create_table(
        "core_analytical_dataset_snapshots",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("dataset_id", UUID, sa.ForeignKey("core_analytical_datasets.id", ondelete="CASCADE"), nullable=False),
        *_scope_columns(), sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("methodology_reference", sa.String(500), nullable=False),
        sa.Column("methodology_version", sa.String(120), nullable=False),
        sa.Column("build_reference", sa.String(500), nullable=False, server_default=""),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("privacy_category", sa.String(40), nullable=False),
        sa.Column("ai_use_policy", sa.String(64), nullable=False),
        sa.Column("state", sa.String(24), nullable=False, server_default="DRAFT"),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("invalidated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("invalidation_reason", sa.String(120), nullable=False, server_default=""),
        sa.Column("invalidated_at", TS, nullable=True),
        sa.Column("invalidated_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("frozen_at", TS, nullable=True), *_audit_columns(),
        sa.UniqueConstraint("dataset_id", "version_no", name="uq_analytical_snapshot_dataset_version"),
        sa.CheckConstraint("version_no >= 1", name="ck_analytical_snapshot_version"),
        sa.CheckConstraint("revision >= 1", name="ck_analytical_snapshot_revision"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_snapshot_product"),
        sa.CheckConstraint("state IN ('DRAFT', 'VALIDATED', 'FROZEN', 'RETIRED')", name="ck_analytical_snapshot_state"),
    )
    op.create_index("ix_analytical_snapshot_scope", "core_analytical_dataset_snapshots", ["organization_id", "workspace_id", "product_code"])
    op.create_index("ix_core_analytical_dataset_snapshots_dataset_id", "core_analytical_dataset_snapshots", ["dataset_id"])

    op.create_table(
        "core_analytical_snapshot_source_versions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("snapshot_id", UUID, sa.ForeignKey("core_analytical_dataset_snapshots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_version_id", UUID, sa.ForeignKey("core_data_source_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("core_data_sources.id", ondelete="RESTRICT"), nullable=False),
        *_scope_columns(), sa.Column("source_version_no", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("privacy_category", sa.String(40), nullable=False),
        sa.Column("ai_use_policy", sa.String(64), nullable=False),
        sa.Column("source_fingerprint", sa.String(64), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("snapshot_id", "source_version_id", name="uq_analytical_snapshot_source_edge"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_snapshot_source_product"),
    )
    op.create_index("ix_analytical_snapshot_source_lineage", "core_analytical_snapshot_source_versions", ["source_version_id", "snapshot_id"])

    op.create_table(
        "core_analytical_features",
        sa.Column("id", UUID, primary_key=True, nullable=False), *_scope_columns(),
        sa.Column("code", sa.String(120), nullable=False), sa.Column("name", sa.String(240), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False, server_default=""),
        sa.Column("methodology_reference", sa.String(500), nullable=False),
        sa.Column("methodology_version", sa.String(120), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"), *_audit_columns(),
        sa.UniqueConstraint("workspace_id", "product_code", "code", name="uq_analytical_feature_scope_code"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_feature_product"),
        sa.CheckConstraint("revision >= 1", name="ck_analytical_feature_revision"),
    )
    op.create_index("ix_analytical_feature_scope", "core_analytical_features", ["organization_id", "workspace_id", "product_code"])

    op.create_table(
        "core_analytical_feature_versions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("feature_id", UUID, sa.ForeignKey("core_analytical_features.id", ondelete="CASCADE"), nullable=False),
        *_scope_columns(), sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("methodology_reference", sa.String(500), nullable=False),
        sa.Column("methodology_version", sa.String(120), nullable=False),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("privacy_category", sa.String(40), nullable=False),
        sa.Column("ai_use_policy", sa.String(64), nullable=False),
        sa.Column("state", sa.String(24), nullable=False, server_default="DRAFT"),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("invalidated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("invalidation_reason", sa.String(120), nullable=False, server_default=""),
        sa.Column("invalidated_at", TS, nullable=True),
        sa.Column("invalidated_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("frozen_at", TS, nullable=True), *_audit_columns(),
        sa.UniqueConstraint("feature_id", "version_no", name="uq_analytical_feature_version"),
        sa.CheckConstraint("version_no >= 1", name="ck_analytical_feature_version_number"),
        sa.CheckConstraint("revision >= 1", name="ck_analytical_feature_version_revision"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_feature_version_product"),
        sa.CheckConstraint("state IN ('DRAFT', 'GOVERNED', 'FROZEN', 'RETIRED')", name="ck_analytical_feature_version_state"),
    )
    op.create_index("ix_analytical_feature_version_scope", "core_analytical_feature_versions", ["organization_id", "workspace_id", "product_code"])
    op.create_index("ix_core_analytical_feature_versions_feature_id", "core_analytical_feature_versions", ["feature_id"])

    op.create_table(
        "core_analytical_feature_snapshot_inputs",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("feature_version_id", UUID, sa.ForeignKey("core_analytical_feature_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_id", UUID, sa.ForeignKey("core_analytical_dataset_snapshots.id", ondelete="RESTRICT"), nullable=False),
        *_scope_columns(), sa.Column("snapshot_version_no", sa.Integer(), nullable=False),
        sa.Column("snapshot_fingerprint", sa.String(64), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("feature_version_id", "snapshot_id", name="uq_analytical_feature_snapshot_edge"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_analytical_feature_snapshot_product"),
    )
    op.create_index("ix_analytical_feature_snapshot_lineage", "core_analytical_feature_snapshot_inputs", ["snapshot_id", "feature_version_id"])


def downgrade() -> None:
    op.drop_index("ix_analytical_feature_snapshot_lineage", table_name="core_analytical_feature_snapshot_inputs")
    op.drop_table("core_analytical_feature_snapshot_inputs")
    op.drop_index("ix_core_analytical_feature_versions_feature_id", table_name="core_analytical_feature_versions")
    op.drop_index("ix_analytical_feature_version_scope", table_name="core_analytical_feature_versions")
    op.drop_table("core_analytical_feature_versions")
    op.drop_index("ix_analytical_feature_scope", table_name="core_analytical_features")
    op.drop_table("core_analytical_features")
    op.drop_index("ix_analytical_snapshot_source_lineage", table_name="core_analytical_snapshot_source_versions")
    op.drop_table("core_analytical_snapshot_source_versions")
    op.drop_index("ix_core_analytical_dataset_snapshots_dataset_id", table_name="core_analytical_dataset_snapshots")
    op.drop_index("ix_analytical_snapshot_scope", table_name="core_analytical_dataset_snapshots")
    op.drop_table("core_analytical_dataset_snapshots")
    op.drop_index("ix_analytical_dataset_scope", table_name="core_analytical_datasets")
    op.drop_table("core_analytical_datasets")
