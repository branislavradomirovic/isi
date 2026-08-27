"""identity organization access and workspace foundation

Revision ID: 20260827_0001
Revises:
Create Date: 2026-08-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260827_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "core_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=True),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_platform_admin", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_core_users_email", "core_users", ["email"], unique=True)

    op.create_table(
        "core_organizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('active', 'suspended', 'archived')", name="ck_core_organizations_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_core_organizations_slug", "core_organizations", ["slug"], unique=True)

    op.create_table(
        "core_products",
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )

    op.create_table(
        "core_roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.String(length=500), server_default="", nullable=False),
        sa.Column("is_system", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_core_roles_code", "core_roles", ["code"], unique=True)

    op.create_table(
        "core_permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), server_default="", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_core_permissions_code", "core_permissions", ["code"], unique=True)

    op.create_table(
        "core_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('active', 'suspended', 'revoked')", name="ck_core_memberships_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["core_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "organization_id", name="uq_core_memberships_user_org"),
    )
    op.create_index("ix_core_memberships_organization_id", "core_memberships", ["organization_id"])
    op.create_index("ix_core_memberships_user_id", "core_memberships", ["user_id"])

    op.create_table(
        "core_organization_entitlements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_code", sa.String(length=16), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_code"], ["core_products.code"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "product_code", name="uq_core_org_entitlement_product"),
    )
    op.create_index("ix_core_organization_entitlements_organization_id", "core_organization_entitlements", ["organization_id"])
    op.create_index("ix_core_organization_entitlements_product_code", "core_organization_entitlements", ["product_code"])

    op.create_table(
        "core_membership_product_access",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("membership_id", sa.Uuid(), nullable=False),
        sa.Column("product_code", sa.String(length=16), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["membership_id"], ["core_memberships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_code"], ["core_products.code"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("membership_id", "product_code", name="uq_core_member_product_access"),
    )
    op.create_index("ix_core_membership_product_access_membership_id", "core_membership_product_access", ["membership_id"])
    op.create_index("ix_core_membership_product_access_product_code", "core_membership_product_access", ["product_code"])

    op.create_table(
        "core_role_permissions",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["core_permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["core_roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    op.create_table(
        "core_role_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("membership_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("product_code", sa.String(length=16), server_default="*", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("product_code IN ('*', 'SIMPA', 'ORDO')", name="ck_core_role_assignment_product_scope"),
        sa.ForeignKeyConstraint(["membership_id"], ["core_memberships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["core_roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("membership_id", "role_id", "product_code", name="uq_core_role_assignment_scope"),
    )
    op.create_index("ix_core_role_assignments_membership_id", "core_role_assignments", ["membership_id"])

    op.create_table(
        "core_workspaces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_code", sa.String(length=16), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("created_by_membership_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('active', 'archived')", name="ck_core_workspaces_status"),
        sa.ForeignKeyConstraint(["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_code"], ["core_products.code"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "product_code", "slug", name="uq_core_workspace_org_product_slug"),
    )
    op.create_index("ix_core_workspaces_organization_id", "core_workspaces", ["organization_id"])
    op.create_index("ix_core_workspaces_product_code", "core_workspaces", ["product_code"])


def downgrade() -> None:
    op.drop_index("ix_core_workspaces_product_code", table_name="core_workspaces")
    op.drop_index("ix_core_workspaces_organization_id", table_name="core_workspaces")
    op.drop_table("core_workspaces")
    op.drop_index("ix_core_role_assignments_membership_id", table_name="core_role_assignments")
    op.drop_table("core_role_assignments")
    op.drop_table("core_role_permissions")
    op.drop_index("ix_core_membership_product_access_product_code", table_name="core_membership_product_access")
    op.drop_index("ix_core_membership_product_access_membership_id", table_name="core_membership_product_access")
    op.drop_table("core_membership_product_access")
    op.drop_index("ix_core_organization_entitlements_product_code", table_name="core_organization_entitlements")
    op.drop_index("ix_core_organization_entitlements_organization_id", table_name="core_organization_entitlements")
    op.drop_table("core_organization_entitlements")
    op.drop_index("ix_core_memberships_user_id", table_name="core_memberships")
    op.drop_index("ix_core_memberships_organization_id", table_name="core_memberships")
    op.drop_table("core_memberships")
    op.drop_index("ix_core_permissions_code", table_name="core_permissions")
    op.drop_table("core_permissions")
    op.drop_index("ix_core_roles_code", table_name="core_roles")
    op.drop_table("core_roles")
    op.drop_table("core_products")
    op.drop_index("ix_core_organizations_slug", table_name="core_organizations")
    op.drop_table("core_organizations")
    op.drop_index("ix_core_users_email", table_name="core_users")
    op.drop_table("core_users")
