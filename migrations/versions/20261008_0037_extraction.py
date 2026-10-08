"""Add append-only extraction requests, artifacts and reviews."""

from alembic import op
import sqlalchemy as sa

revision = "20261008_0037"
down_revision = "20261008_0036"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "core_extraction_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("product_code", sa.String(16), nullable=False),
        sa.Column("request_key", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("binding", sa.JSON(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("created_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["core_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_code"], ["core_products.code"]),
        sa.ForeignKeyConstraint(["job_id"], ["core_ai_jobs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_membership_id"], ["core_memberships.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "organization_id", "workspace_id", "product_code", "request_key", name="uq_extraction_request_key"
        ),
        sa.UniqueConstraint("job_id"),
        sa.CheckConstraint("product_code IN ('SIMPA','ORDO')", name="ck_extraction_request_product"),
        sa.CheckConstraint("state IN ('PENDING','CANCELLED')", name="ck_extraction_request_state"),
    )
    op.create_index("ix_core_extraction_requests_organization_id", "core_extraction_requests", ["organization_id"])
    op.create_index("ix_core_extraction_requests_workspace_id", "core_extraction_requests", ["workspace_id"])
    op.create_table(
        "core_extraction_artifacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["request_id"], ["core_extraction_requests.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("request_id"),
    )
    op.create_table(
        "core_extraction_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("reviewer_membership_id", sa.Uuid(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["artifact_id"], ["core_extraction_artifacts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewer_membership_id"], ["core_memberships.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("artifact_id"),
        sa.CheckConstraint("decision IN ('REVIEWED_ACCEPTED','REJECTED')", name="ck_extraction_review_decision"),
    )


def downgrade():
    op.drop_table("core_extraction_reviews")
    op.drop_table("core_extraction_artifacts")
    op.drop_table("core_extraction_requests")
