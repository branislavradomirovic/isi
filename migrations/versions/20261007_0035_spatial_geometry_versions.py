"""Add private versioned geometry metadata, preserving domain identity v1.
Revision ID: 20261007_0035
Revises: 20260918_0034
"""

from alembic import op
import sqlalchemy as sa

revision = "20261007_0035"
down_revision = "20260918_0034"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "core_spatial_geometry_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id", sa.Uuid(), sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("domain_kind", sa.String(40), nullable=False),
        sa.Column("domain_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(120), nullable=False),
        sa.Column("source_uri", sa.String(500), nullable=False),
        sa.Column("source_version", sa.String(120), nullable=False),
        sa.Column("declared_source_sha256", sa.String(64), nullable=False),
        sa.Column("license_identifier", sa.String(120), nullable=False),
        sa.Column("original_crs", sa.String(40), nullable=False),
        sa.Column("axis_order", sa.String(40), nullable=False),
        sa.Column("render_crs", sa.String(40), nullable=False),
        sa.Column("transformation", sa.String(80), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("geometry_type", sa.String(32), nullable=False),
        sa.Column("geometry_sha256", sa.String(64), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("domain_binding", sa.JSON(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column(
            "created_by_membership_id",
            sa.Uuid(),
            sa.ForeignKey("core_memberships.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "reviewed_by_membership_id",
            sa.Uuid(),
            sa.ForeignKey("core_memberships.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "organization_id",
            "workspace_id",
            "product_code",
            "domain_kind",
            "domain_id",
            "version",
            name="uq_spatial_geometry_version",
        ),
        sa.CheckConstraint("product_code IN ('SIMPA','ORDO')", name="ck_spatial_geometry_product"),
        sa.CheckConstraint("state IN ('DRAFT','PROPOSED','VALIDATED','RETIRED')", name="ck_spatial_geometry_state"),
        sa.CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="ck_spatial_geometry_validity"),
        sa.CheckConstraint("revision >= 1", name="ck_spatial_geometry_revision"),
        sa.CheckConstraint("geometry_type IN ('Point','Polygon','MultiPolygon')", name="ck_spatial_geometry_type"),
        sa.CheckConstraint(
            "(product_code = 'SIMPA' AND domain_kind IN ('local_system','local_actor')) OR (product_code = 'ORDO' AND domain_kind IN ('spatial_unit','asset'))",
            name="ck_spatial_geometry_domain",
        ),
    )
    op.create_index(
        "ix_core_spatial_geometry_versions_organization_id", "core_spatial_geometry_versions", ["organization_id"]
    )
    op.create_index(
        "ix_core_spatial_geometry_versions_workspace_id", "core_spatial_geometry_versions", ["workspace_id"]
    )


def downgrade():
    op.drop_table("core_spatial_geometry_versions")
