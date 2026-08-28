"""administration foundation

Revision ID: 20260828_0012
Revises: 20260828_0011
Create Date: 2026-08-28
"""
from alembic import op
import sqlalchemy as sa


revision = "20260828_0012"
down_revision = "20260828_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "core_invitation_product_grants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("invitation_id", sa.Uuid(), nullable=False),
        sa.Column("product_code", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["invitation_id"], ["core_invitations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_code"], ["core_products.code"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invitation_id", "product_code", name="uq_core_invitation_product_grant"),
    )
    op.create_index("ix_core_invitation_product_grants_invitation_id", "core_invitation_product_grants", ["invitation_id"])
    op.create_index("ix_core_invitation_product_grants_product_code", "core_invitation_product_grants", ["product_code"])

    op.create_table(
        "core_invitation_role_grants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("invitation_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("product_code", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("product_code IN ('*', 'SIMPA', 'ORDO')", name="ck_core_invitation_role_grant_scope"),
        sa.ForeignKeyConstraint(["invitation_id"], ["core_invitations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["core_roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invitation_id", "role_id", "product_code", name="uq_core_invitation_role_grant"),
    )
    op.create_index("ix_core_invitation_role_grants_invitation_id", "core_invitation_role_grants", ["invitation_id"])

    op.create_table(
        "core_admin_audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_membership_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=False),
        sa.Column("target_id", sa.String(length=160), nullable=False),
        sa.Column("product_code", sa.String(length=16), nullable=True),
        sa.Column("before_state", sa.JSON(), nullable=False),
        sa.Column("after_state", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("product_code IS NULL OR product_code IN ('SIMPA', 'ORDO')", name="ck_core_admin_audit_product_scope"),
        sa.ForeignKeyConstraint(["actor_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["core_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_core_admin_audit_events_organization_id", "core_admin_audit_events", ["organization_id"])
    op.create_index("ix_core_admin_audit_events_actor_user_id", "core_admin_audit_events", ["actor_user_id"])
    op.create_index("ix_core_admin_audit_events_actor_membership_id", "core_admin_audit_events", ["actor_membership_id"])
    op.create_index("ix_core_admin_audit_events_action", "core_admin_audit_events", ["action"])
    op.create_index("ix_core_admin_audit_events_product_code", "core_admin_audit_events", ["product_code"])
    op.create_index("ix_core_admin_audit_events_created_at", "core_admin_audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_core_admin_audit_events_created_at", table_name="core_admin_audit_events")
    op.drop_index("ix_core_admin_audit_events_product_code", table_name="core_admin_audit_events")
    op.drop_index("ix_core_admin_audit_events_action", table_name="core_admin_audit_events")
    op.drop_index("ix_core_admin_audit_events_actor_membership_id", table_name="core_admin_audit_events")
    op.drop_index("ix_core_admin_audit_events_actor_user_id", table_name="core_admin_audit_events")
    op.drop_index("ix_core_admin_audit_events_organization_id", table_name="core_admin_audit_events")
    op.drop_table("core_admin_audit_events")
    op.drop_index("ix_core_invitation_role_grants_invitation_id", table_name="core_invitation_role_grants")
    op.drop_table("core_invitation_role_grants")
    op.drop_index("ix_core_invitation_product_grants_product_code", table_name="core_invitation_product_grants")
    op.drop_index("ix_core_invitation_product_grants_invitation_id", table_name="core_invitation_product_grants")
    op.drop_table("core_invitation_product_grants")
