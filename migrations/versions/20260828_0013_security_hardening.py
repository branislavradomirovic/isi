"""security hardening

Revision ID: 20260828_0013
Revises: 20260828_0012
Create Date: 2026-08-28
"""
from alembic import op
import sqlalchemy as sa


revision = "20260828_0013"
down_revision = "20260828_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("core_auth_sessions", sa.Column("remote_ip_hash", sa.String(length=64), nullable=True))
    op.add_column("core_auth_sessions", sa.Column("user_agent_hash", sa.String(length=64), nullable=True))
    op.add_column("core_auth_sessions", sa.Column("revoked_reason", sa.String(length=80), nullable=True))

    op.create_table(
        "core_security_rate_limits",
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("blocked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key_hash"),
    )
    op.create_index("ix_core_security_rate_limits_action", "core_security_rate_limits", ["action"])
    op.create_index("ix_core_security_rate_limits_blocked_until", "core_security_rate_limits", ["blocked_until"])

    op.create_table(
        "core_security_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("subject_hash", sa.String(length=64), nullable=True),
        sa.Column("remote_ip_hash", sa.String(length=64), nullable=True),
        sa.Column("user_agent_hash", sa.String(length=64), nullable=True),
        sa.Column("event_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["core_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_core_security_events_event_type", "core_security_events", ["event_type"])
    op.create_index("ix_core_security_events_outcome", "core_security_events", ["outcome"])
    op.create_index("ix_core_security_events_user_id", "core_security_events", ["user_id"])
    op.create_index("ix_core_security_events_created_at", "core_security_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_core_security_events_created_at", table_name="core_security_events")
    op.drop_index("ix_core_security_events_user_id", table_name="core_security_events")
    op.drop_index("ix_core_security_events_outcome", table_name="core_security_events")
    op.drop_index("ix_core_security_events_event_type", table_name="core_security_events")
    op.drop_table("core_security_events")
    op.drop_index("ix_core_security_rate_limits_blocked_until", table_name="core_security_rate_limits")
    op.drop_index("ix_core_security_rate_limits_action", table_name="core_security_rate_limits")
    op.drop_table("core_security_rate_limits")
    op.drop_column("core_auth_sessions", "revoked_reason")
    op.drop_column("core_auth_sessions", "user_agent_hash")
    op.drop_column("core_auth_sessions", "remote_ip_hash")
