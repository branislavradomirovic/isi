"""Add capability-bound AI evaluation and promotion runtime.

Revision ID: 20260918_0034
Revises: 20260917_0033
Create Date: 2026-09-18
"""

from alembic import op
import sqlalchemy as sa


revision = "20260918_0034"
down_revision = "20260917_0033"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_index(
        "uq_core_ai_model_registration_enabled_champion",
        "core_ai_model_registrations",
        ["product_scope", "capability_key"],
        unique=True,
        postgresql_where=sa.text("lifecycle_state = 'champion' AND enabled = true"),
    )
    op.add_column("core_ai_jobs", sa.Column("model_registration_id", UUID, nullable=True))
    op.create_foreign_key(
        "fk_core_ai_jobs_model_registration", "core_ai_jobs", "core_ai_model_registrations",
        ["model_registration_id"], ["id"], ondelete="RESTRICT",
    )
    op.create_index("ix_core_ai_jobs_model_registration", "core_ai_jobs", ["model_registration_id"])

    op.add_column("core_ai_job_attempts", sa.Column("model_registration_id", UUID, nullable=True))
    op.add_column("core_ai_job_attempts", sa.Column("fallback_edge_id", UUID, nullable=True))
    op.add_column(
        "core_ai_job_attempts", sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column(
        "core_ai_job_attempts",
        sa.Column("requires_human_review", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_foreign_key(
        "fk_core_ai_job_attempts_model_registration", "core_ai_job_attempts", "core_ai_model_registrations",
        ["model_registration_id"], ["id"], ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_core_ai_job_attempts_fallback_edge", "core_ai_job_attempts", "core_ai_model_fallbacks",
        ["fallback_edge_id"], ["id"], ondelete="RESTRICT",
    )
    op.create_index(
        "ix_core_ai_job_attempts_model_registration", "core_ai_job_attempts", ["model_registration_id"]
    )
    op.create_index("ix_core_ai_job_attempts_fallback_edge", "core_ai_job_attempts", ["fallback_edge_id"])

    op.create_table(
        "core_ai_evaluation_benchmarks",
        sa.Column("id", UUID, nullable=False),
        sa.Column("dataset_key", sa.String(180), nullable=False),
        sa.Column("version", sa.String(80), nullable=False),
        sa.Column("product_code", sa.String(16), nullable=False),
        sa.Column("capability_key", sa.String(180), nullable=False),
        sa.Column("model_family", sa.String(32), nullable=False),
        sa.Column("schema_version", sa.String(80), nullable=False),
        sa.Column("case_count", sa.Integer(), nullable=False),
        sa.Column("cases_sha256", sa.String(64), nullable=False),
        sa.Column("manifest_fingerprint", sa.String(64), nullable=False),
        sa.Column("source_provenance", sa.Text(), nullable=False),
        sa.Column("sensitivity_class", sa.String(32), nullable=False),
        sa.Column("methodology_version", sa.String(180), nullable=True),
        sa.Column("frozen", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("approval_state", sa.String(24), nullable=False),
        sa.Column("owner", sa.String(180), nullable=False),
        sa.Column("manifest_json", sa.JSON(), nullable=False),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_core_ai_evaluation_benchmarks"),
        sa.UniqueConstraint("dataset_key", "version", name="uq_core_ai_evaluation_benchmark_version"),
        sa.UniqueConstraint("manifest_fingerprint", name="uq_core_ai_evaluation_benchmark_fingerprint"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ai_evaluation_benchmark_product"),
        sa.CheckConstraint(
            "model_family IN ('statistical_ml', 'embedding', 'llm', 'vlm')",
            name="ck_core_ai_evaluation_benchmark_family",
        ),
        sa.CheckConstraint("approval_state IN ('draft', 'approved')", name="ck_core_ai_evaluation_benchmark_approval"),
        sa.CheckConstraint("case_count >= 1", name="ck_core_ai_evaluation_benchmark_case_count"),
        sa.CheckConstraint(
            "length(cases_sha256) = 64 AND length(manifest_fingerprint) = 64",
            name="ck_core_ai_evaluation_benchmark_fingerprints",
        ),
        sa.ForeignKeyConstraint(["product_code"], ["core_products.code"]),
        sa.ForeignKeyConstraint(["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_core_ai_evaluation_benchmarks_product", "core_ai_evaluation_benchmarks", ["product_code"])
    op.create_index(
        "ix_core_ai_evaluation_benchmarks_capability", "core_ai_evaluation_benchmarks", ["capability_key"]
    )

    op.add_column("core_ai_evaluation_runs", sa.Column("benchmark_id", UUID, nullable=True))
    op.create_foreign_key(
        "fk_core_ai_evaluation_runs_benchmark", "core_ai_evaluation_runs", "core_ai_evaluation_benchmarks",
        ["benchmark_id"], ["id"], ondelete="RESTRICT",
    )
    op.create_index("ix_core_ai_evaluation_runs_benchmark", "core_ai_evaluation_runs", ["benchmark_id"])

    op.create_table(
        "core_ai_capability_thresholds",
        sa.Column("id", UUID, nullable=False),
        sa.Column("product_scope", sa.String(16), nullable=False),
        sa.Column("capability_key", sa.String(180), nullable=False),
        sa.Column("model_family", sa.String(32), nullable=False),
        sa.Column("version", sa.String(80), nullable=False),
        sa.Column("metric_definitions", sa.JSON(), nullable=False),
        sa.Column("minimum_thresholds", sa.JSON(), nullable=False),
        sa.Column("minimum_deltas", sa.JSON(), nullable=False),
        sa.Column("hard_gates", sa.JSON(), nullable=False),
        sa.Column("resource_limits", sa.JSON(), nullable=False),
        sa.Column("failure_threshold", sa.Integer(), nullable=False),
        sa.Column("cooldown_seconds", sa.Integer(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("provenance", sa.Text(), nullable=False),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_core_ai_capability_thresholds"),
        sa.UniqueConstraint(
            "product_scope", "capability_key", "model_family", "version",
            name="uq_core_ai_capability_threshold_version",
        ),
        sa.UniqueConstraint("fingerprint", name="uq_core_ai_capability_threshold_fingerprint"),
        sa.CheckConstraint("product_scope IN ('SHARED', 'SIMPA', 'ORDO')", name="ck_core_ai_capability_threshold_scope"),
        sa.CheckConstraint(
            "model_family IN ('statistical_ml', 'embedding', 'llm', 'vlm')",
            name="ck_core_ai_capability_threshold_family",
        ),
        sa.CheckConstraint("failure_threshold >= 1", name="ck_core_ai_capability_threshold_failures"),
        sa.CheckConstraint("cooldown_seconds >= 0", name="ck_core_ai_capability_threshold_cooldown"),
        sa.CheckConstraint("length(fingerprint) = 64", name="ck_core_ai_capability_threshold_fingerprint"),
        sa.ForeignKeyConstraint(["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_core_ai_capability_thresholds_capability", "core_ai_capability_thresholds", ["capability_key"])

    op.create_table(
        "core_ai_promotion_decisions",
        sa.Column("id", UUID, nullable=False),
        sa.Column("product_code", sa.String(16), nullable=False),
        sa.Column("capability_key", sa.String(180), nullable=False),
        sa.Column("model_family", sa.String(32), nullable=False),
        sa.Column("candidate_registration_id", UUID, nullable=False),
        sa.Column("baseline_registration_id", UUID, nullable=False),
        sa.Column("candidate_run_id", UUID, nullable=False),
        sa.Column("baseline_run_id", UUID, nullable=False),
        sa.Column("benchmark_id", UUID, nullable=False),
        sa.Column("threshold_profile_id", UUID, nullable=False),
        sa.Column("rollback_registration_id", UUID, nullable=False),
        sa.Column("comparison_evidence", sa.JSON(), nullable=False),
        sa.Column("evidence_fingerprint", sa.String(64), nullable=False),
        sa.Column("decision_status", sa.String(24), nullable=False),
        sa.Column("blocker_reasons", sa.JSON(), nullable=False),
        sa.Column("final_review_id", UUID, nullable=True),
        sa.Column("owner_approval_reference", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("executed_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.Column("executed_at", TS, nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_core_ai_promotion_decisions"),
        sa.UniqueConstraint("evidence_fingerprint", name="uq_core_ai_promotion_decision_fingerprint"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ai_promotion_decision_product"),
        sa.CheckConstraint(
            "decision_status IN ('eligible', 'blocked', 'promoted', 'rolled_back')",
            name="ck_core_ai_promotion_decision_status",
        ),
        sa.CheckConstraint("length(evidence_fingerprint) = 64", name="ck_core_ai_promotion_decision_fingerprint"),
        sa.ForeignKeyConstraint(["product_code"], ["core_products.code"]),
        sa.ForeignKeyConstraint(["candidate_registration_id"], ["core_ai_model_registrations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["baseline_registration_id"], ["core_ai_model_registrations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["candidate_run_id"], ["core_ai_evaluation_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["baseline_run_id"], ["core_ai_evaluation_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["benchmark_id"], ["core_ai_evaluation_benchmarks.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["threshold_profile_id"], ["core_ai_capability_thresholds.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["rollback_registration_id"], ["core_ai_model_registrations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["final_review_id"], ["core_ai_evaluation_reviews.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["executed_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_core_ai_promotion_decisions_capability", "core_ai_promotion_decisions", ["capability_key"])

    op.create_table(
        "core_ai_capability_runtime_states",
        sa.Column("id", UUID, nullable=False),
        sa.Column("product_scope", sa.String(16), nullable=False),
        sa.Column("capability_key", sa.String(180), nullable=False),
        sa.Column("model_family", sa.String(32), nullable=False),
        sa.Column("champion_registration_id", UUID, nullable=True),
        sa.Column("rollback_registration_id", UUID, nullable=True),
        sa.Column("threshold_profile_id", UUID, nullable=False),
        sa.Column("circuit_state", sa.String(16), nullable=False, server_default="closed"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_threshold", sa.Integer(), nullable=False),
        sa.Column("cooldown_seconds", sa.Integer(), nullable=False),
        sa.Column("opened_at", TS, nullable=True),
        sa.Column("last_failure_at", TS, nullable=True),
        sa.Column("last_success_at", TS, nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_core_ai_capability_runtime_states"),
        sa.UniqueConstraint("product_scope", "capability_key", name="uq_core_ai_capability_runtime_scope"),
        sa.CheckConstraint("product_scope IN ('SHARED', 'SIMPA', 'ORDO')", name="ck_core_ai_capability_runtime_scope"),
        sa.CheckConstraint("circuit_state IN ('closed', 'open', 'half_open')", name="ck_core_ai_capability_runtime_circuit"),
        sa.CheckConstraint("failure_threshold >= 1", name="ck_core_ai_capability_runtime_failures"),
        sa.CheckConstraint("cooldown_seconds >= 0", name="ck_core_ai_capability_runtime_cooldown"),
        sa.CheckConstraint("consecutive_failures >= 0", name="ck_core_ai_capability_runtime_count"),
        sa.ForeignKeyConstraint(["champion_registration_id"], ["core_ai_model_registrations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["rollback_registration_id"], ["core_ai_model_registrations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["threshold_profile_id"], ["core_ai_capability_thresholds.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_core_ai_capability_runtime_capability", "core_ai_capability_runtime_states", ["capability_key"])

    op.create_table(
        "core_ai_drift_snapshots",
        sa.Column("id", UUID, nullable=False),
        sa.Column("organization_id", UUID, nullable=False),
        sa.Column("workspace_id", UUID, nullable=False),
        sa.Column("product_code", sa.String(16), nullable=False),
        sa.Column("capability_key", sa.String(180), nullable=False),
        sa.Column("model_registration_id", UUID, nullable=False),
        sa.Column("threshold_profile_id", UUID, nullable=False),
        sa.Column("window_start", TS, nullable=False),
        sa.Column("window_end", TS, nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_by_membership_id", UUID, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_core_ai_drift_snapshots"),
        sa.UniqueConstraint("fingerprint", name="uq_core_ai_drift_snapshot_fingerprint"),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ai_drift_snapshot_product"),
        sa.CheckConstraint(
            "status IN ('ok', 'warning', 'blocker', 'insufficient_evidence')",
            name="ck_core_ai_drift_snapshot_status",
        ),
        sa.CheckConstraint("length(fingerprint) = 64", name="ck_core_ai_drift_snapshot_fingerprint"),
        sa.ForeignKeyConstraint(["organization_id"], ["core_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["core_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_code"], ["core_products.code"]),
        sa.ForeignKeyConstraint(["model_registration_id"], ["core_ai_model_registrations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["threshold_profile_id"], ["core_ai_capability_thresholds.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_membership_id"], ["core_memberships.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_core_ai_drift_snapshots_scope", "core_ai_drift_snapshots", ["organization_id", "workspace_id", "product_code"])
    op.create_index("ix_core_ai_drift_snapshots_capability", "core_ai_drift_snapshots", ["capability_key"])


def downgrade() -> None:
    op.drop_index("ix_core_ai_drift_snapshots_capability", table_name="core_ai_drift_snapshots")
    op.drop_index("ix_core_ai_drift_snapshots_scope", table_name="core_ai_drift_snapshots")
    op.drop_table("core_ai_drift_snapshots")
    op.drop_index("ix_core_ai_capability_runtime_capability", table_name="core_ai_capability_runtime_states")
    op.drop_table("core_ai_capability_runtime_states")
    op.drop_index("ix_core_ai_promotion_decisions_capability", table_name="core_ai_promotion_decisions")
    op.drop_table("core_ai_promotion_decisions")
    op.drop_index("ix_core_ai_capability_thresholds_capability", table_name="core_ai_capability_thresholds")
    op.drop_table("core_ai_capability_thresholds")
    op.drop_index("ix_core_ai_evaluation_runs_benchmark", table_name="core_ai_evaluation_runs")
    op.drop_constraint("fk_core_ai_evaluation_runs_benchmark", "core_ai_evaluation_runs", type_="foreignkey")
    op.drop_column("core_ai_evaluation_runs", "benchmark_id")
    op.drop_index("ix_core_ai_evaluation_benchmarks_capability", table_name="core_ai_evaluation_benchmarks")
    op.drop_index("ix_core_ai_evaluation_benchmarks_product", table_name="core_ai_evaluation_benchmarks")
    op.drop_table("core_ai_evaluation_benchmarks")
    op.drop_index("ix_core_ai_job_attempts_fallback_edge", table_name="core_ai_job_attempts")
    op.drop_index("ix_core_ai_job_attempts_model_registration", table_name="core_ai_job_attempts")
    op.drop_constraint("fk_core_ai_job_attempts_fallback_edge", "core_ai_job_attempts", type_="foreignkey")
    op.drop_constraint("fk_core_ai_job_attempts_model_registration", "core_ai_job_attempts", type_="foreignkey")
    op.drop_column("core_ai_job_attempts", "requires_human_review")
    op.drop_column("core_ai_job_attempts", "is_fallback")
    op.drop_column("core_ai_job_attempts", "fallback_edge_id")
    op.drop_column("core_ai_job_attempts", "model_registration_id")
    op.drop_index("ix_core_ai_jobs_model_registration", table_name="core_ai_jobs")
    op.drop_constraint("fk_core_ai_jobs_model_registration", "core_ai_jobs", type_="foreignkey")
    op.drop_column("core_ai_jobs", "model_registration_id")
    op.drop_index(
        "uq_core_ai_model_registration_enabled_champion",
        table_name="core_ai_model_registrations",
    )
