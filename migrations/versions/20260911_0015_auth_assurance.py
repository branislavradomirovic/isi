"""Add persistent authentication assurance to sessions.

Revision ID: 20260911_0015
Revises: 20260910_0014
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa


revision = "20260911_0015"
down_revision = "20260910_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "core_auth_sessions",
        sa.Column("password_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "core_auth_sessions",
        sa.Column("mfa_verified_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("core_auth_sessions", "mfa_verified_at")
    op.drop_column("core_auth_sessions", "password_verified_at")
