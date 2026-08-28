"""shared reporting engine

Revision ID: 20260828_0011
Revises: 20260828_0010
Create Date: 2026-08-28
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260828_0011"
down_revision = "20260828_0010"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "core_reports",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("report_type", sa.String(80), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="active"),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("product_code IN ('SIMPA','ORDO')", name="ck_core_reports_product"),
        sa.CheckConstraint("status IN ('active','archived')", name="ck_core_reports_status"),
    )
    for col in ("organization_id", "workspace_id", "product_code"):
        op.create_index(f"ix_core_reports_{col}", "core_reports", [col])

    op.create_table(
        "core_report_versions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("report_id", UUID, sa.ForeignKey("core_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("source_manifest", sa.JSON(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("source_manifest_sha256", sa.String(64), nullable=False),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("submitted_at", TS, nullable=True),
        sa.Column("approved_at", TS, nullable=True),
        sa.Column("published_at", TS, nullable=True),
        sa.UniqueConstraint("report_id", "version_no", name="uq_core_report_versions_report_version"),
        sa.CheckConstraint(
            "status IN ('draft','in_review','approved','rejected','published','superseded')",
            name="ck_core_report_versions_status",
        ),
    )
    op.create_index("ix_core_report_versions_report_id", "core_report_versions", ["report_id"])
    op.create_index("ix_core_report_versions_status", "core_report_versions", ["status"])

    op.create_table(
        "core_report_reviews",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("report_version_id", UUID, sa.ForeignKey("core_report_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decision", sa.String(24), nullable=False),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("decision IN ('approved','rejected')", name="ck_core_report_reviews_decision"),
    )
    op.create_index("ix_core_report_reviews_report_version_id", "core_report_reviews", ["report_version_id"])
    op.create_index("ix_core_report_reviews_reviewer_membership_id", "core_report_reviews", ["reviewer_membership_id"])

    op.create_table(
        "core_report_exports",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("report_version_id", UUID, sa.ForeignKey("core_report_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("format", sa.String(24), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(120), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("generated_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("format IN ('json','markdown','html')", name="ck_core_report_exports_format"),
        sa.UniqueConstraint("report_version_id", "format", "sha256", name="uq_core_report_exports_version_format_sha"),
    )
    op.create_index("ix_core_report_exports_report_version_id", "core_report_exports", ["report_version_id"])
    op.create_index("ix_core_report_exports_sha256", "core_report_exports", ["sha256"])


def downgrade() -> None:
    op.drop_index("ix_core_report_exports_sha256", table_name="core_report_exports")
    op.drop_index("ix_core_report_exports_report_version_id", table_name="core_report_exports")
    op.drop_table("core_report_exports")
    op.drop_index("ix_core_report_reviews_reviewer_membership_id", table_name="core_report_reviews")
    op.drop_index("ix_core_report_reviews_report_version_id", table_name="core_report_reviews")
    op.drop_table("core_report_reviews")
    op.drop_index("ix_core_report_versions_status", table_name="core_report_versions")
    op.drop_index("ix_core_report_versions_report_id", table_name="core_report_versions")
    op.drop_table("core_report_versions")
    for col in ("product_code", "workspace_id", "organization_id"):
        op.drop_index(f"ix_core_reports_{col}", table_name="core_reports")
    op.drop_table("core_reports")
