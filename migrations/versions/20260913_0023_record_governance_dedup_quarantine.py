"""Add source-local record governance, deduplication, and quarantine.

Revision ID: 20260913_0023
Revises: 20260913_0022
Create Date: 2026-09-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260913_0023"
down_revision = "20260913_0022"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "core_data_record_governance_policy_versions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "source_id",
            UUID,
            sa.ForeignKey("core_data_sources.id", name="fk_rec_policy_source", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "connector_contract_version_id",
            UUID,
            sa.ForeignKey(
                "core_data_connector_contract_versions.id",
                name="fk_rec_policy_connector",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "schema_mapping_version_id",
            UUID,
            sa.ForeignKey(
                "core_data_source_schema_mapping_versions.id",
                name="fk_rec_policy_mapping",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            UUID,
            sa.ForeignKey("core_organizations.id", name="fk_rec_policy_org", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            UUID,
            sa.ForeignKey("core_workspaces.id", name="fk_rec_policy_workspace", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_code",
            sa.String(16),
            sa.ForeignKey("core_products.code", name="fk_rec_policy_product"),
            nullable=False,
        ),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("contract_format_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("identity_field_keys_json", sa.Text(), nullable=False),
        sa.Column("missing_identity_policy", sa.String(24), nullable=False, server_default="QUARANTINE"),
        sa.Column("exact_duplicate_policy", sa.String(24), nullable=False, server_default="LINK_EXISTING"),
        sa.Column("conflict_policy", sa.String(24), nullable=False, server_default="QUARANTINE"),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("lifecycle_state", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column(
            "created_by_membership_id",
            UUID,
            sa.ForeignKey("core_memberships.id", name="fk_rec_policy_created_by", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "activated_by_membership_id",
            UUID,
            sa.ForeignKey("core_memberships.id", name="fk_rec_policy_activated_by", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "retired_by_membership_id",
            UUID,
            sa.ForeignKey("core_memberships.id", name="fk_rec_policy_retired_by", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("activated_at", TS, nullable=True),
        sa.Column("retired_at", TS, nullable=True),
        sa.UniqueConstraint("source_id", "version_no", name="uq_rec_policy_source_version"),
        sa.CheckConstraint("version_no >= 1", name="ck_rec_policy_version_no"),
        sa.CheckConstraint("contract_format_version = 1", name="ck_rec_policy_format"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_rec_policy_product"),
        sa.CheckConstraint("missing_identity_policy = 'QUARANTINE'", name="ck_rec_policy_missing"),
        sa.CheckConstraint("exact_duplicate_policy = 'LINK_EXISTING'", name="ck_rec_policy_duplicate"),
        sa.CheckConstraint("conflict_policy = 'QUARANTINE'", name="ck_rec_policy_conflict"),
        sa.CheckConstraint(
            "lifecycle_state IN ('DRAFT', 'ACTIVE', 'RETIRED')",
            name="ck_rec_policy_lifecycle",
        ),
    )
    op.create_index(
        "ix_rec_policy_scope",
        "core_data_record_governance_policy_versions",
        ["organization_id", "workspace_id", "product_code"],
    )
    op.create_index(
        "ix_rec_policy_binding",
        "core_data_record_governance_policy_versions",
        ["source_id", "connector_contract_version_id", "schema_mapping_version_id"],
    )
    op.create_index(
        "ix_rec_policy_source_state",
        "core_data_record_governance_policy_versions",
        ["source_id", "lifecycle_state"],
    )
    op.create_index(
        "uq_rec_policy_active_source",
        "core_data_record_governance_policy_versions",
        ["source_id"],
        unique=True,
        postgresql_where=sa.text("lifecycle_state = 'ACTIVE'"),
        sqlite_where=sa.text("lifecycle_state = 'ACTIVE'"),
    )

    op.add_column(
        "core_data_ingestion_runs",
        sa.Column("record_governance_policy_version_id", UUID, nullable=True),
    )
    op.create_foreign_key(
        "fk_ing_run_rec_policy",
        "core_data_ingestion_runs",
        "core_data_record_governance_policy_versions",
        ["record_governance_policy_version_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_ing_run_rec_policy",
        "core_data_ingestion_runs",
        ["record_governance_policy_version_id"],
    )

    op.create_table(
        "core_data_record_entities",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "source_id",
            UUID,
            sa.ForeignKey("core_data_sources.id", name="fk_rec_entity_source", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "record_governance_policy_version_id",
            UUID,
            sa.ForeignKey(
                "core_data_record_governance_policy_versions.id",
                name="fk_rec_entity_policy",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            UUID,
            sa.ForeignKey("core_organizations.id", name="fk_rec_entity_org", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            UUID,
            sa.ForeignKey("core_workspaces.id", name="fk_rec_entity_workspace", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_code",
            sa.String(16),
            sa.ForeignKey("core_products.code", name="fk_rec_entity_product"),
            nullable=False,
        ),
        sa.Column("identity_fingerprint", sa.String(64), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint(
            "source_id",
            "record_governance_policy_version_id",
            "identity_fingerprint",
            name="uq_rec_entity_source_policy_identity",
        ),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_rec_entity_product"),
        sa.CheckConstraint("state IN ('ACTIVE', 'QUARANTINED', 'EMPTY')", name="ck_rec_entity_state"),
    )
    op.create_index(
        "ix_rec_entity_scope",
        "core_data_record_entities",
        ["organization_id", "workspace_id", "product_code"],
    )
    op.create_index(
        "ix_rec_entity_source_policy",
        "core_data_record_entities",
        ["source_id", "record_governance_policy_version_id"],
    )

    op.create_table(
        "core_data_normalized_records",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "source_id",
            UUID,
            sa.ForeignKey("core_data_sources.id", name="fk_norm_rec_source", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_version_id",
            UUID,
            sa.ForeignKey("core_data_source_versions.id", name="fk_norm_rec_version", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "ingestion_run_id",
            UUID,
            sa.ForeignKey("core_data_ingestion_runs.id", name="fk_norm_rec_run", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "connector_contract_version_id",
            UUID,
            sa.ForeignKey(
                "core_data_connector_contract_versions.id",
                name="fk_norm_rec_connector",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "schema_mapping_version_id",
            UUID,
            sa.ForeignKey(
                "core_data_source_schema_mapping_versions.id",
                name="fk_norm_rec_mapping",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "record_governance_policy_version_id",
            UUID,
            sa.ForeignKey(
                "core_data_record_governance_policy_versions.id",
                name="fk_norm_rec_policy",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            UUID,
            sa.ForeignKey("core_organizations.id", name="fk_norm_rec_org", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            UUID,
            sa.ForeignKey("core_workspaces.id", name="fk_norm_rec_workspace", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_code",
            sa.String(16),
            sa.ForeignKey("core_products.code", name="fk_norm_rec_product"),
            nullable=False,
        ),
        sa.Column("source_record_ordinal", sa.Integer(), nullable=False),
        sa.Column("source_locator", sa.String(1000), nullable=False),
        sa.Column(
            "entity_id",
            UUID,
            sa.ForeignKey("core_data_record_entities.id", name="fk_norm_rec_entity", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("normalized_record_json", sa.Text(), nullable=False),
        sa.Column("identity_fingerprint", sa.String(64), nullable=False),
        sa.Column("content_fingerprint", sa.String(64), nullable=False),
        sa.Column("disposition", sa.String(16), nullable=False),
        sa.Column(
            "duplicate_of_record_id",
            UUID,
            sa.ForeignKey("core_data_normalized_records.id", name="fk_norm_rec_duplicate", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "conflict_with_record_id",
            UUID,
            sa.ForeignKey("core_data_normalized_records.id", name="fk_norm_rec_conflict", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("quarantine_reason", sa.String(120), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("ingestion_run_id", "source_record_ordinal", name="uq_norm_rec_run_ordinal"),
        sa.CheckConstraint("source_record_ordinal >= 1", name="ck_norm_rec_ordinal"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_norm_rec_product"),
        sa.CheckConstraint(
            "disposition IN ('ACCEPTED', 'DUPLICATE', 'QUARANTINED', 'REJECTED', 'SUPERSEDED', 'PURGED')",
            name="ck_norm_rec_disposition",
        ),
    )
    op.create_index(
        "ix_norm_rec_scope",
        "core_data_normalized_records",
        ["organization_id", "workspace_id", "product_code"],
    )
    op.create_index("ix_norm_rec_source_version", "core_data_normalized_records", ["source_id", "source_version_id"])
    op.create_index("ix_norm_rec_run", "core_data_normalized_records", ["ingestion_run_id"])
    op.create_index("ix_norm_rec_entity", "core_data_normalized_records", ["entity_id"])
    op.create_index(
        "ix_norm_rec_identity_fp",
        "core_data_normalized_records",
        ["source_id", "record_governance_policy_version_id", "identity_fingerprint"],
    )
    op.create_index(
        "ix_norm_rec_content_fp",
        "core_data_normalized_records",
        ["schema_mapping_version_id", "content_fingerprint"],
    )
    op.create_index(
        "uq_norm_rec_accepted_entity",
        "core_data_normalized_records",
        ["entity_id"],
        unique=True,
        postgresql_where=sa.text("entity_id IS NOT NULL AND disposition = 'ACCEPTED'"),
        sqlite_where=sa.text("entity_id IS NOT NULL AND disposition = 'ACCEPTED'"),
    )

    op.create_table(
        "core_data_record_resolutions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "source_id",
            UUID,
            sa.ForeignKey("core_data_sources.id", name="fk_rec_resolution_source", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            UUID,
            sa.ForeignKey("core_organizations.id", name="fk_rec_resolution_org", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            UUID,
            sa.ForeignKey("core_workspaces.id", name="fk_rec_resolution_workspace", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_code",
            sa.String(16),
            sa.ForeignKey("core_products.code", name="fk_rec_resolution_product"),
            nullable=False,
        ),
        sa.Column(
            "entity_id",
            UUID,
            sa.ForeignKey("core_data_record_entities.id", name="fk_rec_resolution_entity", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "quarantined_record_id",
            UUID,
            sa.ForeignKey(
                "core_data_normalized_records.id",
                name="fk_rec_resolution_quarantine",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "existing_accepted_record_id",
            UUID,
            sa.ForeignKey(
                "core_data_normalized_records.id",
                name="fk_rec_resolution_accepted",
                ondelete="RESTRICT",
            ),
            nullable=True,
        ),
        sa.Column("decision", sa.String(24), nullable=False),
        sa.Column("resolution_reference", sa.String(1000), nullable=False),
        sa.Column("reason", sa.String(1000), nullable=True),
        sa.Column(
            "resolved_by_membership_id",
            UUID,
            sa.ForeignKey("core_memberships.id", name="fk_rec_resolution_actor", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolved_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("quarantined_record_id", name="uq_rec_resolution_quarantine"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_rec_resolution_product"),
        sa.CheckConstraint(
            "decision IN ('REJECT_INCOMING', 'ACCEPT_INCOMING')",
            name="ck_rec_resolution_decision",
        ),
    )
    op.create_index(
        "ix_rec_resolution_scope",
        "core_data_record_resolutions",
        ["organization_id", "workspace_id", "product_code"],
    )
    op.create_index(
        "ix_rec_resolution_entity",
        "core_data_record_resolutions",
        ["entity_id", "resolved_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_rec_resolution_entity", table_name="core_data_record_resolutions")
    op.drop_index("ix_rec_resolution_scope", table_name="core_data_record_resolutions")
    op.drop_table("core_data_record_resolutions")

    op.drop_index("uq_norm_rec_accepted_entity", table_name="core_data_normalized_records")
    op.drop_index("ix_norm_rec_content_fp", table_name="core_data_normalized_records")
    op.drop_index("ix_norm_rec_identity_fp", table_name="core_data_normalized_records")
    op.drop_index("ix_norm_rec_entity", table_name="core_data_normalized_records")
    op.drop_index("ix_norm_rec_run", table_name="core_data_normalized_records")
    op.drop_index("ix_norm_rec_source_version", table_name="core_data_normalized_records")
    op.drop_index("ix_norm_rec_scope", table_name="core_data_normalized_records")
    op.drop_table("core_data_normalized_records")

    op.drop_index("ix_rec_entity_source_policy", table_name="core_data_record_entities")
    op.drop_index("ix_rec_entity_scope", table_name="core_data_record_entities")
    op.drop_table("core_data_record_entities")

    op.drop_index("ix_ing_run_rec_policy", table_name="core_data_ingestion_runs")
    op.drop_constraint("fk_ing_run_rec_policy", "core_data_ingestion_runs", type_="foreignkey")
    op.drop_column("core_data_ingestion_runs", "record_governance_policy_version_id")

    op.drop_index("uq_rec_policy_active_source", table_name="core_data_record_governance_policy_versions")
    op.drop_index("ix_rec_policy_source_state", table_name="core_data_record_governance_policy_versions")
    op.drop_index("ix_rec_policy_binding", table_name="core_data_record_governance_policy_versions")
    op.drop_index("ix_rec_policy_scope", table_name="core_data_record_governance_policy_versions")
    op.drop_table("core_data_record_governance_policy_versions")
