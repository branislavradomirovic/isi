"""Add deterministic SIMPA statistical model contracts and results.

Revision ID: 20260915_0029
Revises: 20260915_0028
Create Date: 2026-09-15
"""

from alembic import op
import sqlalchemy as sa


revision = "20260915_0029"
down_revision = "20260915_0028"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "simpa_statistical_model_contracts",
        sa.Column("id", UUID, nullable=False),
        sa.Column("target_indicator_id", UUID, nullable=False),
        sa.Column("target_methodology_id", UUID, nullable=False),
        sa.Column("target_methodology_contract_fingerprint", sa.String(64), nullable=False),
        sa.Column("analysis_key", sa.String(140), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column(
            "schema_version",
            sa.String(64),
            nullable=False,
            server_default="SIMPA-STATISTICAL-MODEL-CONTRACT-v1",
        ),
        sa.Column("target_semantic", sa.String(40), nullable=False),
        sa.Column("model_family", sa.String(40), nullable=False),
        sa.Column("contract_json", sa.JSON(), nullable=False),
        sa.Column("contract_fingerprint", sa.String(64), nullable=False),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("proposed_by_membership_id", UUID, nullable=True),
        sa.Column("proposed_at", TS, nullable=True),
        sa.Column("approved_by_membership_id", UUID, nullable=True),
        sa.Column("approved_at", TS, nullable=True),
        sa.Column("validation_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("validation_evidence_reference", sa.Text(), nullable=False, server_default=""),
        sa.Column("retired_by_membership_id", UUID, nullable=True),
        sa.Column("retired_at", TS, nullable=True),
        sa.Column("retirement_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("version_no >= 1", name="ck_simpa_statistical_contract_version"),
        sa.CheckConstraint("length(analysis_key) > 0", name="ck_simpa_statistical_contract_analysis_key"),
        sa.CheckConstraint(
            "status IN ('draft','proposed','validated','retired')",
            name="ck_simpa_statistical_contract_status",
        ),
        sa.CheckConstraint(
            "schema_version = 'SIMPA-STATISTICAL-MODEL-CONTRACT-v1'",
            name="ck_simpa_statistical_contract_schema_version",
        ),
        sa.CheckConstraint(
            "(target_semantic = 'continuous' AND model_family = 'ols') OR "
            "(target_semantic = 'count' AND model_family = 'poisson_glm') OR "
            "(target_semantic = 'binary_system_state' AND model_family = 'binomial_logit') OR "
            "(target_semantic = 'proportion_rate' AND model_family = 'fractional_logit')",
            name="ck_simpa_statistical_contract_family",
        ),
        sa.CheckConstraint(
            "length(target_methodology_contract_fingerprint) = 64",
            name="ck_simpa_statistical_contract_target_fingerprint",
        ),
        sa.CheckConstraint(
            "length(contract_fingerprint) = 64",
            name="ck_simpa_statistical_contract_fingerprint",
        ),
        sa.CheckConstraint(
            "status != 'validated' OR (length(validation_note) > 0 AND "
            "length(validation_evidence_reference) > 0 AND approved_by_membership_id IS NOT NULL "
            "AND approved_at IS NOT NULL)",
            name="ck_simpa_statistical_contract_validation_trace",
        ),
        sa.ForeignKeyConstraint(
            ["target_indicator_id"],
            ["simpa_indicator_definitions.id"],
            name="fk_simpa_statistical_contract_indicator",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_methodology_id"],
            ["simpa_indicator_methodologies.id"],
            name="fk_simpa_statistical_contract_methodology",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_membership_id"],
            ["core_memberships.id"],
            name="fk_simpa_statistical_contract_creator",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["proposed_by_membership_id"],
            ["core_memberships.id"],
            name="fk_simpa_statistical_contract_proposer",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_membership_id"],
            ["core_memberships.id"],
            name="fk_simpa_statistical_contract_approver",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["retired_by_membership_id"],
            ["core_memberships.id"],
            name="fk_simpa_statistical_contract_retirer",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_simpa_statistical_model_contracts"),
        sa.UniqueConstraint(
            "target_indicator_id",
            "analysis_key",
            "version_no",
            name="uq_simpa_statistical_contract_version",
        ),
    )
    op.create_index(
        "ix_simpa_statistical_contract_target_analysis_status",
        "simpa_statistical_model_contracts",
        ["target_indicator_id", "analysis_key", "status"],
    )

    op.create_table(
        "simpa_statistical_model_results",
        sa.Column("id", UUID, nullable=False),
        sa.Column("organization_id", UUID, nullable=False),
        sa.Column("workspace_id", UUID, nullable=False),
        sa.Column("analytics_run_id", UUID, nullable=False),
        sa.Column("statistical_model_contract_id", UUID, nullable=False),
        sa.Column("target_indicator_id", UUID, nullable=False),
        sa.Column("target_methodology_id", UUID, nullable=False),
        sa.Column("target_methodology_contract_fingerprint", sa.String(64), nullable=False),
        sa.Column("statistical_contract_fingerprint", sa.String(64), nullable=False),
        sa.Column("statistical_contract_version_no", sa.Integer(), nullable=False),
        sa.Column("statistical_contract_status", sa.String(24), nullable=False),
        sa.Column("analytical_artifact_fingerprint", sa.String(64), nullable=False),
        sa.Column("dataset_contract_fingerprint", sa.String(64), nullable=False),
        sa.Column("input_content_fingerprint", sa.String(64), nullable=False),
        sa.Column("engine_schema_version", sa.String(64), nullable=False),
        sa.Column("statsmodels_version", sa.String(64), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("dropped_missing_count", sa.Integer(), nullable=False),
        sa.Column("result_detail", sa.JSON(), nullable=False),
        sa.Column("result_fingerprint", sa.String(64), nullable=False),
        sa.Column("production_eligible", sa.Boolean(), nullable=False),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("sample_size >= 1", name="ck_simpa_statistical_result_sample_size"),
        sa.CheckConstraint("dropped_missing_count >= 0", name="ck_simpa_statistical_result_dropped"),
        sa.CheckConstraint(
            "statistical_contract_version_no >= 1",
            name="ck_simpa_statistical_result_contract_version",
        ),
        sa.CheckConstraint(
            "statistical_contract_status IN ('proposed','validated')",
            name="ck_simpa_statistical_result_contract_status",
        ),
        sa.CheckConstraint(
            "(production_eligible AND statistical_contract_status = 'validated') OR "
            "(NOT production_eligible AND statistical_contract_status = 'proposed')",
            name="ck_simpa_statistical_result_production_eligible",
        ),
        sa.CheckConstraint(
            "engine_schema_version = 'SIMPA-STATISTICAL-MODEL-v1'",
            name="ck_simpa_statistical_result_engine_schema",
        ),
        sa.CheckConstraint(
            "length(target_methodology_contract_fingerprint) = 64 AND "
            "length(statistical_contract_fingerprint) = 64 AND "
            "length(analytical_artifact_fingerprint) = 64 AND "
            "length(dataset_contract_fingerprint) = 64 AND "
            "length(input_content_fingerprint) = 64 AND length(result_fingerprint) = 64",
            name="ck_simpa_statistical_result_fingerprints",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["core_organizations.id"], name="fk_simpa_statistical_result_org", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["core_workspaces.id"], name="fk_simpa_statistical_result_workspace", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["analytics_run_id"], ["simpa_analytics_runs.id"], name="fk_simpa_statistical_result_run", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["statistical_model_contract_id"],
            ["simpa_statistical_model_contracts.id"],
            name="fk_simpa_statistical_result_contract",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_indicator_id"],
            ["simpa_indicator_definitions.id"],
            name="fk_simpa_statistical_result_indicator",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_methodology_id"],
            ["simpa_indicator_methodologies.id"],
            name="fk_simpa_statistical_result_methodology",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_membership_id"],
            ["core_memberships.id"],
            name="fk_simpa_statistical_result_creator",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_simpa_statistical_model_results"),
        sa.UniqueConstraint(
            "analytics_run_id",
            "statistical_model_contract_id",
            name="uq_simpa_statistical_result_run_contract",
        ),
    )
    op.create_index(
        "ix_simpa_statistical_result_scope_created",
        "simpa_statistical_model_results",
        ["organization_id", "workspace_id", "created_at"],
    )
    op.create_index(
        "ix_simpa_statistical_result_contract",
        "simpa_statistical_model_results",
        ["statistical_model_contract_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_simpa_statistical_result_contract", table_name="simpa_statistical_model_results")
    op.drop_index("ix_simpa_statistical_result_scope_created", table_name="simpa_statistical_model_results")
    op.drop_table("simpa_statistical_model_results")
    op.drop_index(
        "ix_simpa_statistical_contract_target_analysis_status",
        table_name="simpa_statistical_model_contracts",
    )
    op.drop_table("simpa_statistical_model_contracts")
