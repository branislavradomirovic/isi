"""Add versioned source schema and field-mapping contracts.

Revision ID: 20260913_0021
Revises: 20260912_0020
Create Date: 2026-09-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260913_0021"
down_revision = "20260912_0020"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "core_data_source_schema_mapping_versions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "source_id",
            UUID,
            sa.ForeignKey(
                "core_data_sources.id",
                name="fk_schema_mapping_source",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "connector_contract_version_id",
            UUID,
            sa.ForeignKey(
                "core_data_connector_contract_versions.id",
                name="fk_schema_mapping_connector",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            UUID,
            sa.ForeignKey(
                "core_organizations.id",
                name="fk_schema_mapping_organization",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            UUID,
            sa.ForeignKey(
                "core_workspaces.id",
                name="fk_schema_mapping_workspace",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "product_code",
            sa.String(16),
            sa.ForeignKey("core_products.code", name="fk_schema_mapping_product"),
            nullable=False,
        ),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("contract_format_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("schema_kind", sa.String(16), nullable=False),
        sa.Column("source_schema_json", sa.Text(), nullable=False),
        sa.Column("field_mapping_json", sa.Text(), nullable=False),
        sa.Column(
            "missing_value_policy",
            sa.String(32),
            nullable=False,
            server_default="PRESERVE_MISSING",
        ),
        sa.Column(
            "unexpected_field_policy",
            sa.String(16),
            nullable=False,
            server_default="REJECT",
        ),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("lifecycle_state", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column(
            "created_by_membership_id",
            UUID,
            sa.ForeignKey(
                "core_memberships.id",
                name="fk_schema_mapping_created_by",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
        sa.Column(
            "activated_by_membership_id",
            UUID,
            sa.ForeignKey(
                "core_memberships.id",
                name="fk_schema_mapping_activated_by",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
        sa.Column(
            "retired_by_membership_id",
            UUID,
            sa.ForeignKey(
                "core_memberships.id",
                name="fk_schema_mapping_retired_by",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("activated_at", TS, nullable=True),
        sa.Column("retired_at", TS, nullable=True),
        sa.UniqueConstraint("source_id", "version_no", name="uq_schema_mapping_source_version"),
        sa.CheckConstraint("version_no >= 1", name="ck_schema_mapping_version_no"),
        sa.CheckConstraint(
            "contract_format_version = 1",
            name="ck_schema_mapping_contract_format",
        ),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_schema_mapping_product"),
        sa.CheckConstraint(
            "schema_kind IN ('TABULAR', 'RECORD')",
            name="ck_schema_mapping_schema_kind",
        ),
        sa.CheckConstraint(
            "missing_value_policy = 'PRESERVE_MISSING'",
            name="ck_schema_mapping_missing_policy",
        ),
        sa.CheckConstraint(
            "unexpected_field_policy IN ('REJECT', 'IGNORE')",
            name="ck_schema_mapping_unexpected_policy",
        ),
        sa.CheckConstraint(
            "lifecycle_state IN ('DRAFT', 'ACTIVE', 'RETIRED')",
            name="ck_schema_mapping_lifecycle",
        ),
    )
    op.create_index(
        "ix_schema_mapping_scope",
        "core_data_source_schema_mapping_versions",
        ["organization_id", "workspace_id", "product_code"],
    )
    op.create_index(
        "ix_schema_mapping_source_state",
        "core_data_source_schema_mapping_versions",
        ["source_id", "lifecycle_state"],
    )
    op.create_index(
        "ix_schema_mapping_connector",
        "core_data_source_schema_mapping_versions",
        ["connector_contract_version_id"],
    )
    op.create_index(
        "uq_schema_mapping_active_source",
        "core_data_source_schema_mapping_versions",
        ["source_id"],
        unique=True,
        postgresql_where=sa.text("lifecycle_state = 'ACTIVE'"),
        sqlite_where=sa.text("lifecycle_state = 'ACTIVE'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_schema_mapping_active_source",
        table_name="core_data_source_schema_mapping_versions",
    )
    op.drop_index(
        "ix_schema_mapping_connector",
        table_name="core_data_source_schema_mapping_versions",
    )
    op.drop_index(
        "ix_schema_mapping_source_state",
        table_name="core_data_source_schema_mapping_versions",
    )
    op.drop_index(
        "ix_schema_mapping_scope",
        table_name="core_data_source_schema_mapping_versions",
    )
    op.drop_table("core_data_source_schema_mapping_versions")
