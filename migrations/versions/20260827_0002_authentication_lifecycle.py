"""authentication lifecycle

Revision ID: 20260827_0002
Revises: 20260827_0001
Create Date: 2026-08-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260827_0002"
down_revision: str | None = "20260827_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("core_users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("core_users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("core_users", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("uq_core_users_email_normalized", "core_users", [sa.text("lower(email)")], unique=True)

    op.create_table(
        "core_auth_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("remote_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["core_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_core_auth_sessions_user_id", "core_auth_sessions", ["user_id"])
    op.create_index("ix_core_auth_sessions_token_hash", "core_auth_sessions", ["token_hash"], unique=True)
    op.create_index("ix_core_auth_sessions_expires_at", "core_auth_sessions", ["expires_at"])

    op.create_table(
        "core_auth_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "purpose IN ('email_verification', 'password_reset')",
            name="ck_core_auth_tokens_purpose",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["core_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_core_auth_tokens_user_id", "core_auth_tokens", ["user_id"])
    op.create_index("ix_core_auth_tokens_purpose", "core_auth_tokens", ["purpose"])
    op.create_index("ix_core_auth_tokens_token_hash", "core_auth_tokens", ["token_hash"], unique=True)
    op.create_index("ix_core_auth_tokens_expires_at", "core_auth_tokens", ["expires_at"])

    op.create_table(
        "core_invitations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("invited_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'accepted', 'revoked')", name="ck_core_invitations_status"),
        sa.ForeignKeyConstraint(["invited_by_user_id"], ["core_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_core_invitations_organization_id", "core_invitations", ["organization_id"])
    op.create_index("ix_core_invitations_email", "core_invitations", ["email"])
    op.create_index("ix_core_invitations_token_hash", "core_invitations", ["token_hash"], unique=True)
    op.create_index("ix_core_invitations_expires_at", "core_invitations", ["expires_at"])
    op.create_index(
        "uq_core_invitations_pending_org_email",
        "core_invitations",
        ["organization_id", "email"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index("uq_core_invitations_pending_org_email", table_name="core_invitations")
    op.drop_index("ix_core_invitations_expires_at", table_name="core_invitations")
    op.drop_index("ix_core_invitations_token_hash", table_name="core_invitations")
    op.drop_index("ix_core_invitations_email", table_name="core_invitations")
    op.drop_index("ix_core_invitations_organization_id", table_name="core_invitations")
    op.drop_table("core_invitations")

    op.drop_index("ix_core_auth_tokens_expires_at", table_name="core_auth_tokens")
    op.drop_index("ix_core_auth_tokens_token_hash", table_name="core_auth_tokens")
    op.drop_index("ix_core_auth_tokens_purpose", table_name="core_auth_tokens")
    op.drop_index("ix_core_auth_tokens_user_id", table_name="core_auth_tokens")
    op.drop_table("core_auth_tokens")

    op.drop_index("ix_core_auth_sessions_expires_at", table_name="core_auth_sessions")
    op.drop_index("ix_core_auth_sessions_token_hash", table_name="core_auth_sessions")
    op.drop_index("ix_core_auth_sessions_user_id", table_name="core_auth_sessions")
    op.drop_table("core_auth_sessions")

    op.drop_index("uq_core_users_email_normalized", table_name="core_users")
    op.drop_column("core_users", "password_changed_at")
    op.drop_column("core_users", "last_login_at")
    op.drop_column("core_users", "email_verified_at")
