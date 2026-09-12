"""Add versioned source connector contracts.

Revision ID: 20260912_0020
Revises: 20260912_0019
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260912_0020"
down_revision = "20260912_0019"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "core_data_connector_contract_versions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "source_id",
            UUID,
            sa.ForeignKey("core_data_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            UUID,
            sa.ForeignKey("core_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            UUID,
            sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("connector_kind", sa.String(120), nullable=False),
        sa.Column("transport", sa.String(120), nullable=False),
        sa.Column("configuration_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("credential_reference", sa.String(500), nullable=False, server_default=""),
        sa.Column("capabilities_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("lifecycle_state", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column(
            "created_by_membership_id",
            UUID,
            sa.ForeignKey("core_memberships.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "activated_by_membership_id",
            UUID,
            sa.ForeignKey("core_memberships.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "retired_by_membership_id",
            UUID,
            sa.ForeignKey("core_memberships.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("activated_at", TS, nullable=True),
        sa.Column("retired_at", TS, nullable=True),
        sa.UniqueConstraint("source_id", "version_no", name="uq_connector_contract_source_version"),
        sa.CheckConstraint("version_no >= 1", name="ck_connector_contract_version_no"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_connector_contract_product"),
        sa.CheckConstraint(
            "lifecycle_state IN ('DRAFT', 'ACTIVE', 'RETIRED')",
            name="ck_connector_contract_state",
        ),
    )
    op.create_index(
        "ix_connector_contract_scope",
        "core_data_connector_contract_versions",
        ["organization_id", "workspace_id", "product_code"],
    )
    op.create_index(
        "ix_connector_contract_source_state",
        "core_data_connector_contract_versions",
        ["source_id", "lifecycle_state"],
    )


def downgrade() -> None:
    op.drop_index("ix_connector_contract_source_state", table_name="core_data_connector_contract_versions")
    op.drop_index("ix_connector_contract_scope", table_name="core_data_connector_contract_versions")
    op.drop_table("core_data_connector_contract_versions")
