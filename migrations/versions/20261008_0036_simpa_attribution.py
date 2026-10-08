"""Add immutable scope-bound SIMPA OLS attribution artifacts."""

from alembic import op
import sqlalchemy as sa

revision = "20261008_0036"
down_revision = "20261007_0035"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "simpa_attribution_artifacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("statistical_result_id", sa.Uuid(), nullable=False),
        sa.Column("result_fingerprint", sa.String(64), nullable=False),
        sa.Column("schema_version", sa.String(64), nullable=False),
        sa.Column("artifact", sa.JSON(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("created_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["core_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["statistical_result_id"], ["simpa_statistical_model_results.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_membership_id"], ["core_memberships.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("statistical_result_id", "schema_version", name="uq_simpa_attribution_result_schema"),
        sa.CheckConstraint("schema_version = 'SIMPA-LINEAR-SHAP-v1'", name="ck_simpa_attribution_schema"),
        sa.CheckConstraint(
            "length(fingerprint) = 64 AND length(result_fingerprint) = 64", name="ck_simpa_attribution_hash"
        ),
    )
    op.create_index("ix_simpa_attribution_scope", "simpa_attribution_artifacts", ["organization_id", "workspace_id"])


def downgrade():
    op.drop_table("simpa_attribution_artifacts")
