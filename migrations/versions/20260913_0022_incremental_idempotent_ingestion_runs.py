"""Add incremental and idempotent ingestion runs.

Revision ID: 20260913_0022
Revises: 20260913_0021
Create Date: 2026-09-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260913_0022"
down_revision = "20260913_0021"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "core_data_ingestion_runs",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "source_id",
            UUID,
            sa.ForeignKey(
                "core_data_sources.id",
                name="fk_ing_run_source",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            UUID,
            sa.ForeignKey(
                "core_organizations.id",
                name="fk_ing_run_organization",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            UUID,
            sa.ForeignKey(
                "core_workspaces.id",
                name="fk_ing_run_workspace",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "product_code",
            sa.String(16),
            sa.ForeignKey("core_products.code", name="fk_ing_run_product"),
            nullable=False,
        ),
        sa.Column("run_no", sa.Integer(), nullable=False),
        sa.Column(
            "connector_contract_version_id",
            UUID,
            sa.ForeignKey(
                "core_data_connector_contract_versions.id",
                name="fk_ing_run_connector",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "schema_mapping_version_id",
            UUID,
            sa.ForeignKey(
                "core_data_source_schema_mapping_versions.id",
                name="fk_ing_run_mapping",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "source_version_id",
            UUID,
            sa.ForeignKey(
                "core_data_source_versions.id",
                name="fk_ing_run_source_version",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "inspection_job_id",
            UUID,
            sa.ForeignKey(
                "core_ingestion_jobs.id",
                name="fk_ing_run_inspection_job",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("cursor_before", sa.String(1000), nullable=False, server_default=""),
        sa.Column("cursor_after", sa.String(1000), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="QUEUED"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(120), nullable=False, server_default=""),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_by_membership_id",
            UUID,
            sa.ForeignKey(
                "core_memberships.id",
                name="fk_ing_run_created_by",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
        sa.Column("queued_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("started_at", TS, nullable=True),
        sa.Column("finished_at", TS, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("source_id", "run_no", name="uq_ing_run_source_no"),
        sa.UniqueConstraint("source_id", "idempotency_key", name="uq_ing_run_source_idem"),
        sa.UniqueConstraint("source_id", "request_fingerprint", name="uq_ing_run_source_fp"),
        sa.UniqueConstraint("source_version_id", name="uq_ing_run_source_version"),
        sa.UniqueConstraint("inspection_job_id", name="uq_ing_run_inspection_job"),
        sa.CheckConstraint("run_no >= 1", name="ck_ing_run_no"),
        sa.CheckConstraint("attempts >= 0", name="ck_ing_run_attempts"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_ing_run_product"),
        sa.CheckConstraint(
            "status IN ('QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED')",
            name="ck_ing_run_status",
        ),
    )
    op.create_index(
        "ix_ing_run_scope",
        "core_data_ingestion_runs",
        ["organization_id", "workspace_id", "product_code"],
    )
    op.create_index(
        "ix_ing_run_source_status",
        "core_data_ingestion_runs",
        ["source_id", "status"],
    )
    op.create_index(
        "ix_ing_run_binding",
        "core_data_ingestion_runs",
        ["source_id", "connector_contract_version_id", "schema_mapping_version_id"],
    )
    op.create_index(
        "uq_ing_run_live_source",
        "core_data_ingestion_runs",
        ["source_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('QUEUED', 'RUNNING')"),
        sqlite_where=sa.text("status IN ('QUEUED', 'RUNNING')"),
    )


def downgrade() -> None:
    op.drop_index("uq_ing_run_live_source", table_name="core_data_ingestion_runs")
    op.drop_index("ix_ing_run_binding", table_name="core_data_ingestion_runs")
    op.drop_index("ix_ing_run_source_status", table_name="core_data_ingestion_runs")
    op.drop_index("ix_ing_run_scope", table_name="core_data_ingestion_runs")
    op.drop_table("core_data_ingestion_runs")
