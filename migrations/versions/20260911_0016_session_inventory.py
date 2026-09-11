"""Add privacy-safe device labels to authentication sessions.

Revision ID: 20260911_0016
Revises: 20260911_0015
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa


revision = "20260911_0016"
down_revision = "20260911_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "core_auth_sessions",
        sa.Column("device_label", sa.String(length=80), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("core_auth_sessions", "device_label")
