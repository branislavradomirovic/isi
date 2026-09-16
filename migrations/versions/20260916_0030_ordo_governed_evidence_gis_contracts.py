"""Add ORDO governed evidence, GIS and scenario contracts.

Revision ID: 20260916_0030
Revises: 20260915_0029
Create Date: 2026-09-16
"""

from alembic import op
import sqlalchemy as sa

revision = "20260916_0030"
down_revision = "20260915_0029"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def _lifecycle_columns():
    return [
        sa.Column("lifecycle_status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("lifecycle_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("proposed_by_membership_id", UUID, nullable=True),
        sa.Column("proposed_at", TS, nullable=True),
        sa.Column("validated_by_membership_id", UUID, nullable=True),
        sa.Column("validated_at", TS, nullable=True),
        sa.Column("retired_by_membership_id", UUID, nullable=True),
        sa.Column("retired_at", TS, nullable=True),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.func.now()),
    ]


def upgrade() -> None:
    op.create_table(
        "ordo_reference_evidence",
        sa.Column("id", UUID, nullable=False),
        sa.Column("organization_id", UUID, nullable=False),
        sa.Column("workspace_id", UUID, nullable=False),
        sa.Column("evidence_key", sa.String(160), nullable=False),
        sa.Column("indicator_id", UUID, nullable=True),
        sa.Column("source_version_id", UUID, nullable=True),
        sa.Column("source_identity", sa.String(300), nullable=False, server_default=""),
        sa.Column("source_version", sa.String(160), nullable=False, server_default=""),
        sa.Column("external_identity", sa.String(300), nullable=False, server_default=""),
        sa.Column("artifact_sha256", sa.String(64), nullable=False, server_default=""),
        sa.Column("content_sha256", sa.String(64), nullable=False, server_default=""),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("provenance_lineage", sa.JSON(), nullable=False),
        *_lifecycle_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_ordo_reference_evidence"),
        sa.UniqueConstraint("workspace_id", "evidence_key", name="uq_ordo_reference_evidence_workspace_key"),
        sa.CheckConstraint("lifecycle_status IN ('draft','proposed','validated','retired')", name="ck_ordo_reference_evidence_lifecycle"),
        sa.CheckConstraint("valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from", name="ck_ordo_reference_evidence_validity"),
        sa.CheckConstraint("artifact_sha256 = '' OR length(artifact_sha256) = 64", name="ck_ordo_reference_evidence_artifact_sha"),
        sa.CheckConstraint("content_sha256 = '' OR length(content_sha256) = 64", name="ck_ordo_reference_evidence_content_sha"),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["core_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["indicator_id"], ["ordo_indicator_definitions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_version_id"], ["core_data_source_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["proposed_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["validated_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["retired_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ordo_reference_evidence_scope_lifecycle", "ordo_reference_evidence", ["organization_id", "workspace_id", "lifecycle_status"])

    op.create_table(
        "ordo_spatial_units",
        sa.Column("id", UUID, nullable=False),
        sa.Column("organization_id", UUID, nullable=False),
        sa.Column("workspace_id", UUID, nullable=False),
        sa.Column("spatial_unit_key", sa.String(160), nullable=False),
        sa.Column("spatial_unit_type", sa.String(40), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("boundary_source", sa.String(300), nullable=False, server_default=""),
        sa.Column("boundary_version", sa.String(160), nullable=False, server_default=""),
        sa.Column("geometry_id", sa.String(300), nullable=False, server_default=""),
        sa.Column("crs", sa.String(80), nullable=False, server_default=""),
        sa.Column("artifact_sha256", sa.String(64), nullable=False, server_default=""),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        *_lifecycle_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_ordo_spatial_units"),
        sa.UniqueConstraint("workspace_id", "spatial_unit_key", "boundary_version", name="uq_ordo_spatial_unit_boundary_version"),
        sa.CheckConstraint("spatial_unit_type IN ('national','macro_region','region','local_government','custom')", name="ck_ordo_spatial_unit_type"),
        sa.CheckConstraint("lifecycle_status IN ('draft','proposed','validated','retired')", name="ck_ordo_spatial_unit_lifecycle"),
        sa.CheckConstraint("valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from", name="ck_ordo_spatial_unit_validity"),
        sa.CheckConstraint("artifact_sha256 = '' OR length(artifact_sha256) = 64", name="ck_ordo_spatial_unit_artifact_sha"),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["core_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["proposed_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["validated_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["retired_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ordo_spatial_unit_scope_lifecycle", "ordo_spatial_units", ["organization_id", "workspace_id", "lifecycle_status"])

    with op.batch_alter_table("ordo_scenario_assessments") as batch:
        batch.add_column(sa.Column("scenario_contract_version", sa.String(64), nullable=False, server_default="LEGACY_UNVERSIONED"))
        batch.add_column(sa.Column("methodology_key", sa.String(160), nullable=False, server_default="legacy_evidence_readiness"))
        batch.add_column(sa.Column("methodology_version", sa.String(80), nullable=False, server_default="0"))
        batch.add_column(sa.Column("input_reference_identities", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
        batch.add_column(sa.Column("input_snapshot_sha256", sa.String(64), nullable=False, server_default=""))
        batch.add_column(sa.Column("limitations", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
        batch.add_column(sa.Column("uncertainty_semantics", sa.String(80), nullable=False, server_default="not_applicable_scenario_not_forecast"))
        batch.add_column(sa.Column("human_review_state", sa.String(24), nullable=False, server_default="pending"))
        batch.create_check_constraint("ck_ordo_scenario_assessment_snapshot_sha", "input_snapshot_sha256 = '' OR length(input_snapshot_sha256) = 64")
        batch.create_check_constraint("ck_ordo_scenario_assessment_human_review", "human_review_state IN ('pending','reviewed','rejected')")
        batch.create_check_constraint("ck_ordo_scenario_assessment_uncertainty", "uncertainty_semantics = 'not_applicable_scenario_not_forecast'")

    op.execute(
        "UPDATE ordo_scenario_assessments SET human_review_state = "
        "CASE WHEN status = 'reviewed' THEN 'reviewed' "
        "WHEN status = 'rejected' THEN 'rejected' ELSE 'pending' END"
    )
    with op.batch_alter_table("ordo_scenario_assessments") as batch:
        batch.alter_column("scenario_contract_version", server_default="ORDO-SCENARIO-CONTRACT-v1")
        batch.alter_column("methodology_key", server_default="ordo_evidence_readiness_v1")
        batch.alter_column("methodology_version", server_default="1")


def downgrade() -> None:
    with op.batch_alter_table("ordo_scenario_assessments") as batch:
        batch.drop_constraint("ck_ordo_scenario_assessment_uncertainty", type_="check")
        batch.drop_constraint("ck_ordo_scenario_assessment_human_review", type_="check")
        batch.drop_constraint("ck_ordo_scenario_assessment_snapshot_sha", type_="check")
        for column in ["human_review_state", "uncertainty_semantics", "limitations", "input_snapshot_sha256", "input_reference_identities", "methodology_version", "methodology_key", "scenario_contract_version"]:
            batch.drop_column(column)
    op.drop_index("ix_ordo_spatial_unit_scope_lifecycle", table_name="ordo_spatial_units")
    op.drop_table("ordo_spatial_units")
    op.drop_index("ix_ordo_reference_evidence_scope_lifecycle", table_name="ordo_reference_evidence")
    op.drop_table("ordo_reference_evidence")
