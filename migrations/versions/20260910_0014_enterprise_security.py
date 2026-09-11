"""MFA persistence and challenge lifecycle foundation.

Revision ID: 20260910_0014
Revises: 20260828_0013
Create Date: 2026-09-10
"""

from alembic import op
import sqlalchemy as sa


revision = "20260910_0014"
down_revision = "20260828_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "core_mfa_factors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("method", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'active', 'revoked')", name="ck_core_mfa_factors_status"),
        sa.CheckConstraint(
            "(status = 'pending' AND verified_at IS NULL AND revoked_at IS NULL) OR "
            "(status = 'active' AND verified_at IS NOT NULL AND revoked_at IS NULL) OR "
            "(status = 'revoked' AND revoked_at IS NOT NULL)",
            name="ck_core_mfa_factors_lifecycle",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["core_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "user_id", name="uq_core_mfa_factors_id_user"),
    )
    op.create_index("ix_core_mfa_factors_user_id", "core_mfa_factors", ["user_id"])
    op.create_index("ix_core_mfa_factors_method", "core_mfa_factors", ["method"])
    op.create_index("ix_core_mfa_factors_user_status", "core_mfa_factors", ["user_id", "status"])

    op.create_table(
        "core_mfa_challenges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("factor_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("verifier_digest", sa.String(length=64), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "purpose IN ('enrollment', 'authentication')", name="ck_core_mfa_challenges_purpose"
        ),
        sa.CheckConstraint("attempt_count >= 0", name="ck_core_mfa_challenges_attempt_count_nonnegative"),
        sa.CheckConstraint("max_attempts BETWEEN 1 AND 10", name="ck_core_mfa_challenges_max_attempts"),
        sa.CheckConstraint("attempt_count <= max_attempts", name="ck_core_mfa_challenges_attempts_bounded"),
        sa.CheckConstraint(
            "NOT (consumed_at IS NOT NULL AND revoked_at IS NOT NULL)",
            name="ck_core_mfa_challenges_terminal_state",
        ),
        sa.ForeignKeyConstraint(
            ["factor_id", "user_id"],
            ["core_mfa_factors.id", "core_mfa_factors.user_id"],
            ondelete="CASCADE",
            name="fk_core_mfa_challenges_factor_user",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_core_mfa_challenges_user_id", "core_mfa_challenges", ["user_id"])
    op.create_index("ix_core_mfa_challenges_factor_id", "core_mfa_challenges", ["factor_id"])
    op.create_index("ix_core_mfa_challenges_purpose", "core_mfa_challenges", ["purpose"])
    op.create_index("ix_core_mfa_challenges_expires_at", "core_mfa_challenges", ["expires_at"])
    op.create_index(
        "ix_core_mfa_challenges_user_lifecycle",
        "core_mfa_challenges",
        ["user_id", "consumed_at", "revoked_at", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_core_mfa_challenges_user_lifecycle", table_name="core_mfa_challenges")
    op.drop_index("ix_core_mfa_challenges_expires_at", table_name="core_mfa_challenges")
    op.drop_index("ix_core_mfa_challenges_purpose", table_name="core_mfa_challenges")
    op.drop_index("ix_core_mfa_challenges_factor_id", table_name="core_mfa_challenges")
    op.drop_index("ix_core_mfa_challenges_user_id", table_name="core_mfa_challenges")
    op.drop_table("core_mfa_challenges")
    op.drop_index("ix_core_mfa_factors_user_status", table_name="core_mfa_factors")
    op.drop_index("ix_core_mfa_factors_method", table_name="core_mfa_factors")
    op.drop_index("ix_core_mfa_factors_user_id", table_name="core_mfa_factors")
    op.drop_table("core_mfa_factors")
