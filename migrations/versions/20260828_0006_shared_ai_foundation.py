"""shared ai foundation

Revision ID: 20260828_0006
Revises: 20260828_0005
Create Date: 2026-08-28
"""

from alembic import op
import sqlalchemy as sa

revision = "20260828_0006"
down_revision = "20260828_0005"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "core_ai_models",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("model_key", sa.String(160), nullable=False),
        sa.Column("provider_type", sa.String(24), nullable=False),
        sa.Column("provider_name", sa.String(120), nullable=False),
        sa.Column("model_name", sa.String(300), nullable=False),
        sa.Column("purpose", sa.String(24), nullable=False),
        sa.Column("product_scope", sa.String(16), nullable=False, server_default="SHARED"),
        sa.Column("local_provider", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("context_window", sa.Integer(), nullable=True),
        sa.Column("max_output_tokens", sa.Integer(), nullable=True),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=True),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("model_key", name="uq_core_ai_models_key"),
        sa.CheckConstraint("provider_type IN ('ollama', 'stub', 'external')", name="ck_core_ai_models_provider_type"),
        sa.CheckConstraint("purpose IN ('chat', 'embedding')", name="ck_core_ai_models_purpose"),
        sa.CheckConstraint("product_scope IN ('SHARED', 'SIMPA', 'ORDO')", name="ck_core_ai_models_product_scope"),
    )

    op.create_table(
        "core_ai_prompts",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("prompt_key", sa.String(180), nullable=False),
        sa.Column("product_scope", sa.String(16), nullable=False, server_default="SHARED"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("purpose", sa.String(180), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("prompt_key", name="uq_core_ai_prompts_key"),
        sa.CheckConstraint("product_scope IN ('SHARED', 'SIMPA', 'ORDO')", name="ck_core_ai_prompts_product_scope"),
    )

    op.create_table(
        "core_ai_policy_profiles",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("policy_key", sa.String(160), nullable=False),
        sa.Column("product_scope", sa.String(16), nullable=False, server_default="SHARED"),
        sa.Column("sensitivity", sa.String(24), nullable=False, server_default="internal"),
        sa.Column("provider_policy", sa.String(32), nullable=False, server_default="local_only"),
        sa.Column("allow_external", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("require_human_review", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("policy_key", name="uq_core_ai_policy_profiles_key"),
        sa.CheckConstraint("product_scope IN ('SHARED', 'SIMPA', 'ORDO')", name="ck_core_ai_policy_profiles_product_scope"),
        sa.CheckConstraint("sensitivity IN ('public', 'internal', 'sensitive')", name="ck_core_ai_policy_profiles_sensitivity"),
        sa.CheckConstraint("provider_policy IN ('local_only', 'local_preferred', 'any')", name="ck_core_ai_policy_profiles_provider_policy"),
        sa.CheckConstraint("max_attempts >= 1 AND max_attempts <= 5", name="ck_core_ai_policy_profiles_attempts"),
    )

    op.create_table(
        "core_ai_prompt_versions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("prompt_id", UUID, sa.ForeignKey("core_ai_prompts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("system_template", sa.Text(), nullable=False, server_default=""),
        sa.Column("user_template", sa.Text(), nullable=False),
        sa.Column("output_schema", sa.JSON(), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("prompt_id", "version_no", name="uq_core_ai_prompt_versions_prompt_version"),
        sa.CheckConstraint("status IN ('draft', 'active', 'retired')", name="ck_core_ai_prompt_versions_status"),
    )
    op.create_index("ix_core_ai_prompt_versions_prompt_id", "core_ai_prompt_versions", ["prompt_id"])

    op.create_table(
        "core_ai_jobs",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("model_id", UUID, sa.ForeignKey("core_ai_models.id"), nullable=False),
        sa.Column("prompt_version_id", UUID, sa.ForeignKey("core_ai_prompt_versions.id"), nullable=False),
        sa.Column("policy_profile_id", UUID, sa.ForeignKey("core_ai_policy_profiles.id"), nullable=False),
        sa.Column("job_type", sa.String(24), nullable=False, server_default="chat"),
        sa.Column("status", sa.String(24), nullable=False, server_default="queued"),
        sa.Column("sensitivity", sa.String(24), nullable=False, server_default="internal"),
        sa.Column("effective_provider_policy", sa.String(32), nullable=False),
        sa.Column("request_sha256", sa.String(64), nullable=False),
        sa.Column("request_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("output_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("structured_output", sa.JSON(), nullable=True),
        sa.Column("provider_name", sa.String(120), nullable=False, server_default=""),
        sa.Column("model_name", sa.String(300), nullable=False, server_default=""),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(120), nullable=False, server_default=""),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("human_review_status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rq_job_id", sa.String(160), nullable=False, server_default=""),
        sa.Column("queued_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("started_at", TS, nullable=True),
        sa.Column("finished_at", TS, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ai_jobs_product"),
        sa.CheckConstraint("job_type IN ('chat', 'structured')", name="ck_core_ai_jobs_type"),
        sa.CheckConstraint("status IN ('queued', 'running', 'succeeded', 'failed', 'review_required')", name="ck_core_ai_jobs_status"),
        sa.CheckConstraint("sensitivity IN ('public', 'internal', 'sensitive')", name="ck_core_ai_jobs_sensitivity"),
        sa.CheckConstraint("effective_provider_policy IN ('local_only', 'local_preferred', 'any')", name="ck_core_ai_jobs_provider_policy"),
        sa.CheckConstraint("human_review_status IN ('not_required', 'pending', 'accepted', 'rejected')", name="ck_core_ai_jobs_review_status"),
    )
    op.create_index("ix_core_ai_jobs_organization_id", "core_ai_jobs", ["organization_id"])
    op.create_index("ix_core_ai_jobs_workspace_id", "core_ai_jobs", ["workspace_id"])
    op.create_index("ix_core_ai_jobs_product_code", "core_ai_jobs", ["product_code"])
    op.create_index("ix_core_ai_jobs_request_sha256", "core_ai_jobs", ["request_sha256"])

    op.create_table(
        "core_ai_job_attempts",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("job_id", UUID, sa.ForeignKey("core_ai_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("provider_name", sa.String(120), nullable=False),
        sa.Column("model_name", sa.String(300), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="running"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(120), nullable=False, server_default=""),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("job_id", "attempt_no", name="uq_core_ai_job_attempts_job_attempt"),
        sa.CheckConstraint("status IN ('running', 'succeeded', 'failed')", name="ck_core_ai_job_attempts_status"),
    )
    op.create_index("ix_core_ai_job_attempts_job_id", "core_ai_job_attempts", ["job_id"])

    op.create_table(
        "core_ai_audit_events",
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
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ai_audit_events_product"),
    )
    op.create_index("ix_core_ai_audit_events_organization_id", "core_ai_audit_events", ["organization_id"])
    op.create_index("ix_core_ai_audit_events_workspace_id", "core_ai_audit_events", ["workspace_id"])
    op.create_index("ix_core_ai_audit_events_product_code", "core_ai_audit_events", ["product_code"])
    op.create_index("ix_core_ai_audit_events_event_type", "core_ai_audit_events", ["event_type"])

    op.create_table(
        "core_ai_embeddings",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID, sa.ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_code", sa.String(16), sa.ForeignKey("core_products.code"), nullable=False),
        sa.Column("namespace", sa.String(220), nullable=False),
        sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("source_id", sa.String(220), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("model_id", UUID, sa.ForeignKey("core_ai_models.id"), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("vector_data", sa.JSON(), nullable=False),
        sa.Column("created_by_membership_id", UUID, sa.ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint(
            "namespace",
            "source_type",
            "source_id",
            "chunk_index",
            "content_sha256",
            "model_id",
            name="uq_core_ai_embeddings_identity",
        ),
        sa.CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ai_embeddings_product"),
    )
    op.create_index("ix_core_ai_embeddings_organization_id", "core_ai_embeddings", ["organization_id"])
    op.create_index("ix_core_ai_embeddings_workspace_id", "core_ai_embeddings", ["workspace_id"])
    op.create_index("ix_core_ai_embeddings_product_code", "core_ai_embeddings", ["product_code"])
    op.create_index("ix_core_ai_embeddings_namespace", "core_ai_embeddings", ["namespace"])
    op.create_index("ix_core_ai_embeddings_content_sha256", "core_ai_embeddings", ["content_sha256"])

    op.execute(
        """
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        EXECUTE 'CREATE TABLE IF NOT EXISTS core_ai_embedding_vectors (
            embedding_id uuid PRIMARY KEY REFERENCES core_ai_embeddings(id) ON DELETE CASCADE,
            embedding vector NOT NULL
        )';
    END IF;
END $$;
"""
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS core_ai_embedding_vectors")
    op.drop_index("ix_core_ai_embeddings_content_sha256", table_name="core_ai_embeddings")
    op.drop_index("ix_core_ai_embeddings_namespace", table_name="core_ai_embeddings")
    op.drop_index("ix_core_ai_embeddings_product_code", table_name="core_ai_embeddings")
    op.drop_index("ix_core_ai_embeddings_workspace_id", table_name="core_ai_embeddings")
    op.drop_index("ix_core_ai_embeddings_organization_id", table_name="core_ai_embeddings")
    op.drop_table("core_ai_embeddings")
    op.drop_index("ix_core_ai_audit_events_event_type", table_name="core_ai_audit_events")
    op.drop_index("ix_core_ai_audit_events_product_code", table_name="core_ai_audit_events")
    op.drop_index("ix_core_ai_audit_events_workspace_id", table_name="core_ai_audit_events")
    op.drop_index("ix_core_ai_audit_events_organization_id", table_name="core_ai_audit_events")
    op.drop_table("core_ai_audit_events")
    op.drop_index("ix_core_ai_job_attempts_job_id", table_name="core_ai_job_attempts")
    op.drop_table("core_ai_job_attempts")
    op.drop_index("ix_core_ai_jobs_request_sha256", table_name="core_ai_jobs")
    op.drop_index("ix_core_ai_jobs_product_code", table_name="core_ai_jobs")
    op.drop_index("ix_core_ai_jobs_workspace_id", table_name="core_ai_jobs")
    op.drop_index("ix_core_ai_jobs_organization_id", table_name="core_ai_jobs")
    op.drop_table("core_ai_jobs")
    op.drop_index("ix_core_ai_prompt_versions_prompt_id", table_name="core_ai_prompt_versions")
    op.drop_table("core_ai_prompt_versions")
    op.drop_table("core_ai_policy_profiles")
    op.drop_table("core_ai_prompts")
    op.drop_table("core_ai_models")
