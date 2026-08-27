"""shared data platform

Revision ID: 20260828_0005
Revises: 20260827_0004
Create Date: 2026-08-28
"""

from alembic import op
import sqlalchemy as sa

revision = "20260828_0005"
down_revision = "20260827_0004"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "core_data_sources",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("source_kind", sa.String(24), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="active"),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("workspace_id", "name", name="uq_core_data_sources_workspace_name"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_sources_product"),
        sa.CheckConstraint("source_kind IN ('dataset', 'document')", name="ck_core_data_sources_kind"),
        sa.CheckConstraint("status IN ('active', 'archived')", name="ck_core_data_sources_status"),
    )
    op.create_index("ix_core_data_sources_organization_id", "core_data_sources", ["organization_id"])
    op.create_index("ix_core_data_sources_workspace_id", "core_data_sources", ["workspace_id"])
    op.create_index("ix_core_data_sources_product_code", "core_data_sources", ["product_code"])

    op.create_table(
        "core_data_source_versions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("core_data_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("extension", sa.String(32), nullable=False),
        sa.Column("content_type", sa.String(200), nullable=False, server_default="application/octet-stream"),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("storage_key", sa.String(1200), nullable=False),
        sa.Column("ingest_status", sa.String(24), nullable=False, server_default="uploaded"),
        sa.Column("detected_format", sa.String(32), nullable=False, server_default=""),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("column_count", sa.Integer(), nullable=True),
        sa.Column("sheet_count", sa.Integer(), nullable=True),
        sa.Column("schema_fingerprint", sa.String(64), nullable=False, server_default=""),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("source_id", "version_no", name="uq_core_data_source_versions_source_version"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_source_versions_product"),
        sa.CheckConstraint("ingest_status IN ('uploaded', 'queued', 'running', 'succeeded', 'failed')", name="ck_core_data_source_versions_ingest_status"),
    )
    op.create_index("ix_core_data_source_versions_source_id", "core_data_source_versions", ["source_id"])
    op.create_index("ix_core_data_source_versions_organization_id", "core_data_source_versions", ["organization_id"])
    op.create_index("ix_core_data_source_versions_workspace_id", "core_data_source_versions", ["workspace_id"])
    op.create_index("ix_core_data_source_versions_product_code", "core_data_source_versions", ["product_code"])
    op.create_index("ix_core_data_source_versions_sha256", "core_data_source_versions", ["sha256"])

    op.create_table(
        "core_ingestion_jobs",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("version_id", UUID, sa.ForeignKey("core_data_source_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("job_type", sa.String(24), nullable=False, server_default="inspect"),
        sa.Column("status", sa.String(24), nullable=False, server_default="queued"),
        sa.Column("backend", sa.String(16), nullable=False, server_default="inline"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rq_job_id", sa.String(160), nullable=False, server_default=""),
        sa.Column("error_code", sa.String(120), nullable=False, server_default=""),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("queued_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("started_at", TS, nullable=True),
        sa.Column("finished_at", TS, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ingestion_jobs_product"),
        sa.CheckConstraint("job_type IN ('inspect', 'validate')", name="ck_core_ingestion_jobs_type"),
        sa.CheckConstraint("status IN ('queued', 'running', 'succeeded', 'failed')", name="ck_core_ingestion_jobs_status"),
        sa.CheckConstraint("backend IN ('inline', 'rq')", name="ck_core_ingestion_jobs_backend"),
        sa.CheckConstraint("progress >= 0 AND progress <= 100", name="ck_core_ingestion_jobs_progress"),
    )
    op.create_index("ix_core_ingestion_jobs_version_id", "core_ingestion_jobs", ["version_id"])
    op.create_index("ix_core_ingestion_jobs_organization_id", "core_ingestion_jobs", ["organization_id"])
    op.create_index("ix_core_ingestion_jobs_workspace_id", "core_ingestion_jobs", ["workspace_id"])
    op.create_index("ix_core_ingestion_jobs_product_code", "core_ingestion_jobs", ["product_code"])

    op.create_table(
        "core_data_quality_results",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("version_id", UUID, sa.ForeignKey("core_data_source_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("check_code", sa.String(120), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("metric_name", sa.String(120), nullable=False, server_default=""),
        sa.Column("metric_value", sa.String(300), nullable=False, server_default=""),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("status IN ('pass', 'warn', 'fail')", name="ck_core_data_quality_results_status"),
    )
    op.create_index("ix_core_data_quality_results_version_id", "core_data_quality_results", ["version_id"])

    op.create_table(
        "core_data_audit_events",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("actor_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", UUID, nullable=False),
        sa.Column("detail", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_data_audit_events_product"),
    )
    op.create_index("ix_core_data_audit_events_organization_id", "core_data_audit_events", ["organization_id"])
    op.create_index("ix_core_data_audit_events_workspace_id", "core_data_audit_events", ["workspace_id"])
    op.create_index("ix_core_data_audit_events_product_code", "core_data_audit_events", ["product_code"])
    op.create_index("ix_core_data_audit_events_event_type", "core_data_audit_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_core_data_audit_events_event_type", table_name="core_data_audit_events")
    op.drop_index("ix_core_data_audit_events_product_code", table_name="core_data_audit_events")
    op.drop_index("ix_core_data_audit_events_workspace_id", table_name="core_data_audit_events")
    op.drop_index("ix_core_data_audit_events_organization_id", table_name="core_data_audit_events")
    op.drop_table("core_data_audit_events")
    op.drop_index("ix_core_data_quality_results_version_id", table_name="core_data_quality_results")
    op.drop_table("core_data_quality_results")
    op.drop_index("ix_core_ingestion_jobs_product_code", table_name="core_ingestion_jobs")
    op.drop_index("ix_core_ingestion_jobs_workspace_id", table_name="core_ingestion_jobs")
    op.drop_index("ix_core_ingestion_jobs_organization_id", table_name="core_ingestion_jobs")
    op.drop_index("ix_core_ingestion_jobs_version_id", table_name="core_ingestion_jobs")
    op.drop_table("core_ingestion_jobs")
    op.drop_index("ix_core_data_source_versions_sha256", table_name="core_data_source_versions")
    op.drop_index("ix_core_data_source_versions_product_code", table_name="core_data_source_versions")
    op.drop_index("ix_core_data_source_versions_workspace_id", table_name="core_data_source_versions")
    op.drop_index("ix_core_data_source_versions_organization_id", table_name="core_data_source_versions")
    op.drop_index("ix_core_data_source_versions_source_id", table_name="core_data_source_versions")
    op.drop_table("core_data_source_versions")
    op.drop_index("ix_core_data_sources_product_code", table_name="core_data_sources")
    op.drop_index("ix_core_data_sources_workspace_id", table_name="core_data_sources")
    op.drop_index("ix_core_data_sources_organization_id", table_name="core_data_sources")
    op.drop_table("core_data_sources")
