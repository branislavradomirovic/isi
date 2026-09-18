"""Add AI/MLOps governance and evaluation persistence foundation.

Revision ID: 20260917_0033
Revises: 20260916_0032
Create Date: 2026-09-17
"""

from alembic import op
import sqlalchemy as sa


revision = "20260917_0033"
down_revision = "20260916_0032"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "core_ai_model_registrations",
        sa.Column("id", UUID, nullable=False),
        sa.Column("capability_key", sa.String(180), nullable=False),
        sa.Column("product_scope", sa.String(16), nullable=False),
        sa.Column("model_family", sa.String(32), nullable=False),
        sa.Column("model_key", sa.String(220), nullable=False),
        sa.Column("runtime_model_id", UUID, nullable=True),
        sa.Column("provider_name", sa.String(120), nullable=True),
        sa.Column("runtime_name", sa.String(300), nullable=True),
        sa.Column("version", sa.String(160), nullable=False),
        sa.Column("revision", sa.String(160), nullable=True),
        sa.Column("artifact_uri", sa.String(500), nullable=True),
        sa.Column("artifact_checksum", sa.String(64), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("registry_fingerprint", sa.String(64), nullable=False),
        sa.Column("lifecycle_state", sa.String(24), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("retired_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.Column("retired_at", TS, nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_core_ai_model_registrations"),
        sa.UniqueConstraint("registry_fingerprint", name="uq_core_ai_model_registration_fingerprint"),
        sa.CheckConstraint("product_scope IN ('SHARED', 'SIMPA', 'ORDO')", name="ck_core_ai_model_registration_scope"),
        sa.CheckConstraint(
            "model_family IN ('statistical_ml', 'embedding', 'llm', 'vlm')",
            name="ck_core_ai_model_registration_family",
        ),
        sa.CheckConstraint(
            "lifecycle_state IN ('candidate', 'challenger', 'champion', 'retired')",
            name="ck_core_ai_model_registration_lifecycle",
        ),
        sa.CheckConstraint("length(registry_fingerprint) = 64", name="ck_core_ai_model_registration_fingerprint"),
        sa.CheckConstraint(
            "artifact_checksum IS NULL OR length(artifact_checksum) = 64",
            name="ck_core_ai_model_registration_artifact_checksum",
        ),
        sa.ForeignKeyConstraint(["runtime_model_id"], ["core_ai_models.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["retired_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_core_ai_model_registrations_capability", "core_ai_model_registrations", ["capability_key"])
    op.create_index("ix_core_ai_model_registrations_runtime", "core_ai_model_registrations", ["runtime_model_id"])

    op.create_table(
        "core_ai_model_fallbacks",
        sa.Column("id", UUID, nullable=False),
        sa.Column("source_registration_id", UUID, nullable=False),
        sa.Column("target_registration_id", UUID, nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("trigger_codes", sa.JSON(), nullable=False),
        sa.Column("semantically_equivalent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_core_ai_model_fallbacks"),
        sa.UniqueConstraint(
            "source_registration_id", "target_registration_id", name="uq_core_ai_model_fallback_edge"
        ),
        sa.UniqueConstraint("source_registration_id", "priority", name="uq_core_ai_model_fallback_priority"),
        sa.UniqueConstraint("fingerprint", name="uq_core_ai_model_fallback_fingerprint"),
        sa.CheckConstraint("source_registration_id != target_registration_id", name="ck_core_ai_model_fallback_not_self"),
        sa.CheckConstraint("priority >= 1", name="ck_core_ai_model_fallback_priority"),
        sa.CheckConstraint("length(fingerprint) = 64", name="ck_core_ai_model_fallback_fingerprint"),
        sa.ForeignKeyConstraint(
            ["source_registration_id"], ["core_ai_model_registrations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["target_registration_id"], ["core_ai_model_registrations.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_core_ai_model_fallbacks_source", "core_ai_model_fallbacks", ["source_registration_id"])
    op.create_index("ix_core_ai_model_fallbacks_target", "core_ai_model_fallbacks", ["target_registration_id"])

    op.create_table(
        "core_ai_prompt_rollback_targets",
        sa.Column("id", UUID, nullable=False),
        sa.Column("source_prompt_version_id", UUID, nullable=False),
        sa.Column("target_prompt_version_id", UUID, nullable=False),
        sa.Column("source_checksum", sa.String(64), nullable=False),
        sa.Column("target_checksum", sa.String(64), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_core_ai_prompt_rollback_targets"),
        sa.UniqueConstraint("source_prompt_version_id", name="uq_core_ai_prompt_rollback_source"),
        sa.UniqueConstraint("fingerprint", name="uq_core_ai_prompt_rollback_fingerprint"),
        sa.CheckConstraint(
            "source_prompt_version_id != target_prompt_version_id", name="ck_core_ai_prompt_rollback_not_self"
        ),
        sa.CheckConstraint("length(fingerprint) = 64", name="ck_core_ai_prompt_rollback_fingerprint"),
        sa.ForeignKeyConstraint(
            ["source_prompt_version_id"], ["core_ai_prompt_versions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["target_prompt_version_id"], ["core_ai_prompt_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "ix_core_ai_prompt_rollback_source", "core_ai_prompt_rollback_targets", ["source_prompt_version_id"]
    )
    op.create_index(
        "ix_core_ai_prompt_rollback_target", "core_ai_prompt_rollback_targets", ["target_prompt_version_id"]
    )

    op.create_table(
        "core_ai_evaluation_datasets",
        sa.Column("id", UUID, nullable=False),
        sa.Column("dataset_key", sa.String(180), nullable=False),
        sa.Column("version", sa.String(80), nullable=False),
        sa.Column("product_code", sa.String(16), nullable=False),
        sa.Column("schema_version", sa.String(80), nullable=False),
        sa.Column("capability_coverage", sa.JSON(), nullable=False),
        sa.Column("cases_sha256", sa.String(64), nullable=False),
        sa.Column("case_count", sa.Integer(), nullable=False),
        sa.Column("source_provenance", sa.Text(), nullable=False),
        sa.Column("sensitivity", sa.String(32), nullable=False),
        sa.Column("frozen", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("frozen_at", TS, nullable=False),
        sa.Column("approval_state", sa.String(24), nullable=False),
        sa.Column("owner", sa.String(180), nullable=False),
        sa.Column(
            "foundation_only_not_production_promotion_evidence",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("manifest_json", sa.JSON(), nullable=False),
        sa.Column("dataset_fingerprint", sa.String(64), nullable=False),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_core_ai_evaluation_datasets"),
        sa.UniqueConstraint("dataset_key", "version", name="uq_core_ai_evaluation_dataset_version"),
        sa.UniqueConstraint("dataset_fingerprint", name="uq_core_ai_evaluation_dataset_fingerprint"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ai_evaluation_dataset_product"),
        sa.CheckConstraint(
            "sensitivity IN ('public', 'internal', 'sensitive', 'synthetic_non_production')",
            name="ck_core_ai_evaluation_dataset_sensitivity",
        ),
        sa.CheckConstraint("approval_state IN ('draft', 'approved')", name="ck_core_ai_evaluation_dataset_approval"),
        sa.CheckConstraint("case_count >= 1", name="ck_core_ai_evaluation_dataset_case_count"),
        sa.CheckConstraint(
            "length(cases_sha256) = 64 AND length(dataset_fingerprint) = 64",
            name="ck_core_ai_evaluation_dataset_fingerprints",
        ),
        sa.CheckConstraint(
            "foundation_only_not_production_promotion_evidence = true",
            name="ck_core_ai_evaluation_dataset_foundation_only",
        ),
        sa.ForeignKeyConstraint(["product_code"], ["core_products.code"]),
        sa.ForeignKeyConstraint(
            ["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_core_ai_evaluation_datasets_key", "core_ai_evaluation_datasets", ["dataset_key"])
    op.create_index("ix_core_ai_evaluation_datasets_product", "core_ai_evaluation_datasets", ["product_code"])

    op.create_table(
        "core_ai_evaluation_runs",
        sa.Column("id", UUID, nullable=False),
        sa.Column("organization_id", UUID, nullable=False),
        sa.Column("workspace_id", UUID, nullable=False),
        sa.Column("product_code", sa.String(16), nullable=False),
        sa.Column("dataset_id", UUID, nullable=False),
        sa.Column("model_registration_id", UUID, nullable=False),
        sa.Column("baseline_registration_id", UUID, nullable=True),
        sa.Column("prompt_version_id", UUID, nullable=True),
        sa.Column("policy_profile_id", UUID, nullable=True),
        sa.Column("input_fingerprint", sa.String(64), nullable=False),
        sa.Column("environment_fingerprint", sa.String(64), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="created"),
        sa.Column("result_fingerprint", sa.String(64), nullable=True),
        sa.Column("failure_reason", sa.String(180), nullable=False, server_default=""),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", TS, nullable=True),
        sa.Column("completed_at", TS, nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_core_ai_evaluation_runs"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ai_evaluation_run_product"),
        sa.CheckConstraint(
            "status IN ('created', 'running', 'completed', 'failed')", name="ck_core_ai_evaluation_run_status"
        ),
        sa.CheckConstraint("length(input_fingerprint) = 64", name="ck_core_ai_evaluation_run_input_fingerprint"),
        sa.CheckConstraint(
            "length(environment_fingerprint) = 64", name="ck_core_ai_evaluation_run_environment_fingerprint"
        ),
        sa.CheckConstraint(
            "result_fingerprint IS NULL OR length(result_fingerprint) = 64",
            name="ck_core_ai_evaluation_run_result_fingerprint",
        ),
        sa.CheckConstraint(
            "(status IN ('created', 'running') AND result_fingerprint IS NULL AND completed_at IS NULL) "
            "OR (status IN ('completed', 'failed') AND result_fingerprint IS NOT NULL AND completed_at IS NOT NULL)",
            name="ck_core_ai_evaluation_run_terminal_state",
        ),
        sa.CheckConstraint(
            "(status = 'failed' AND length(failure_reason) > 0) OR "
            "(status != 'failed' AND failure_reason = '')",
            name="ck_core_ai_evaluation_run_failure_state",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["core_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_code"], ["core_products.code"]),
        sa.ForeignKeyConstraint(["dataset_id"], ["core_ai_evaluation_datasets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["model_registration_id"], ["core_ai_model_registrations.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["baseline_registration_id"], ["core_ai_model_registrations.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["prompt_version_id"], ["core_ai_prompt_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["policy_profile_id"], ["core_ai_policy_profiles.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "ix_core_ai_evaluation_runs_scope",
        "core_ai_evaluation_runs",
        ["organization_id", "workspace_id", "product_code", "created_at"],
    )
    op.create_index("ix_core_ai_evaluation_runs_dataset", "core_ai_evaluation_runs", ["dataset_id"])
    op.create_index("ix_core_ai_evaluation_runs_model", "core_ai_evaluation_runs", ["model_registration_id"])

    op.create_table(
        "core_ai_evaluation_results",
        sa.Column("id", UUID, nullable=False),
        sa.Column("evaluation_run_id", UUID, nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("result_type", sa.String(24), nullable=False),
        sa.Column("result_key", sa.String(180), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_core_ai_evaluation_results"),
        sa.UniqueConstraint("evaluation_run_id", "sequence_no", name="uq_core_ai_evaluation_result_sequence"),
        sa.UniqueConstraint("fingerprint", name="uq_core_ai_evaluation_result_fingerprint"),
        sa.CheckConstraint(
            "result_type IN ('metric', 'safety', 'reliability', 'provenance', 'evidence')",
            name="ck_core_ai_evaluation_result_type",
        ),
        sa.CheckConstraint("sequence_no >= 1", name="ck_core_ai_evaluation_result_sequence"),
        sa.CheckConstraint("length(fingerprint) = 64", name="ck_core_ai_evaluation_result_fingerprint"),
        sa.ForeignKeyConstraint(
            ["evaluation_run_id"], ["core_ai_evaluation_runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_core_ai_evaluation_results_run", "core_ai_evaluation_results", ["evaluation_run_id"])

    op.create_table(
        "core_ai_evaluation_reviews",
        sa.Column("id", UUID, nullable=False),
        sa.Column("evaluation_run_id", UUID, nullable=False),
        sa.Column("reviewer_membership_id", UUID, nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("is_final", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("evidence_reference", sa.String(500), nullable=False, server_default=""),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("reviewed_at", TS, nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_core_ai_evaluation_reviews"),
        sa.UniqueConstraint("fingerprint", name="uq_core_ai_evaluation_review_fingerprint"),
        sa.CheckConstraint(
            "decision IN ('pending', 'approved', 'changes_requested', 'rejected')",
            name="ck_core_ai_evaluation_review_decision",
        ),
        sa.CheckConstraint(
            "(is_final = false AND decision = 'pending') OR (is_final = true AND decision != 'pending')",
            name="ck_core_ai_evaluation_review_final_state",
        ),
        sa.CheckConstraint("length(fingerprint) = 64", name="ck_core_ai_evaluation_review_fingerprint"),
        sa.ForeignKeyConstraint(
            ["evaluation_run_id"], ["core_ai_evaluation_runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_membership_id"], ["core_memberships.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index("ix_core_ai_evaluation_reviews_run", "core_ai_evaluation_reviews", ["evaluation_run_id"])
    op.create_index(
        "ix_core_ai_evaluation_reviews_reviewer", "core_ai_evaluation_reviews", ["reviewer_membership_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_core_ai_evaluation_reviews_reviewer", table_name="core_ai_evaluation_reviews")
    op.drop_index("ix_core_ai_evaluation_reviews_run", table_name="core_ai_evaluation_reviews")
    op.drop_table("core_ai_evaluation_reviews")
    op.drop_index("ix_core_ai_evaluation_results_run", table_name="core_ai_evaluation_results")
    op.drop_table("core_ai_evaluation_results")
    op.drop_index("ix_core_ai_evaluation_runs_model", table_name="core_ai_evaluation_runs")
    op.drop_index("ix_core_ai_evaluation_runs_dataset", table_name="core_ai_evaluation_runs")
    op.drop_index("ix_core_ai_evaluation_runs_scope", table_name="core_ai_evaluation_runs")
    op.drop_table("core_ai_evaluation_runs")
    op.drop_index("ix_core_ai_evaluation_datasets_product", table_name="core_ai_evaluation_datasets")
    op.drop_index("ix_core_ai_evaluation_datasets_key", table_name="core_ai_evaluation_datasets")
    op.drop_table("core_ai_evaluation_datasets")
    op.drop_index("ix_core_ai_prompt_rollback_target", table_name="core_ai_prompt_rollback_targets")
    op.drop_index("ix_core_ai_prompt_rollback_source", table_name="core_ai_prompt_rollback_targets")
    op.drop_table("core_ai_prompt_rollback_targets")
    op.drop_index("ix_core_ai_model_fallbacks_target", table_name="core_ai_model_fallbacks")
    op.drop_index("ix_core_ai_model_fallbacks_source", table_name="core_ai_model_fallbacks")
    op.drop_table("core_ai_model_fallbacks")
    op.drop_index("ix_core_ai_model_registrations_runtime", table_name="core_ai_model_registrations")
    op.drop_index("ix_core_ai_model_registrations_capability", table_name="core_ai_model_registrations")
    op.drop_table("core_ai_model_registrations")
