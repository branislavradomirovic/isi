from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class AIModel(Base):
    __tablename__ = "core_ai_models"
    __table_args__ = (
        UniqueConstraint("model_key", name="uq_core_ai_models_key"),
        CheckConstraint("provider_type IN ('ollama', 'stub', 'external')", name="ck_core_ai_models_provider_type"),
        CheckConstraint("purpose IN ('chat', 'embedding')", name="ck_core_ai_models_purpose"),
        CheckConstraint("product_scope IN ('SHARED', 'SIMPA', 'ORDO')", name="ck_core_ai_models_product_scope"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    model_key: Mapped[str] = mapped_column(String(160), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(24), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False)
    model_name: Mapped[str] = mapped_column(String(300), nullable=False)
    purpose: Mapped[str] = mapped_column(String(24), nullable=False)
    product_scope: Mapped[str] = mapped_column(String(16), nullable=False, default="SHARED", server_default="SHARED")
    local_provider: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    context_window: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding_dimensions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=120, server_default="120")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class AIPrompt(Base):
    __tablename__ = "core_ai_prompts"
    __table_args__ = (
        UniqueConstraint("prompt_key", name="uq_core_ai_prompts_key"),
        CheckConstraint("product_scope IN ('SHARED', 'SIMPA', 'ORDO')", name="ck_core_ai_prompts_product_scope"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    prompt_key: Mapped[str] = mapped_column(String(180), nullable=False)
    product_scope: Mapped[str] = mapped_column(String(16), nullable=False, default="SHARED", server_default="SHARED")
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    purpose: Mapped[str] = mapped_column(String(180), nullable=False, default="", server_default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class AIPromptVersion(Base):
    __tablename__ = "core_ai_prompt_versions"
    __table_args__ = (
        UniqueConstraint("prompt_id", "version_no", name="uq_core_ai_prompt_versions_prompt_version"),
        CheckConstraint("status IN ('draft', 'active', 'retired')", name="ck_core_ai_prompt_versions_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    prompt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_ai_prompts.id", ondelete="CASCADE"), nullable=False, index=True)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    system_template: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    user_template: Mapped[str] = mapped_column(Text, nullable=False)
    output_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AIPromptRollbackTarget(Base):
    __tablename__ = "core_ai_prompt_rollback_targets"
    __table_args__ = (
        UniqueConstraint("source_prompt_version_id", name="uq_core_ai_prompt_rollback_source"),
        CheckConstraint(
            "source_prompt_version_id != target_prompt_version_id",
            name="ck_core_ai_prompt_rollback_not_self",
        ),
        CheckConstraint("length(fingerprint) = 64", name="ck_core_ai_prompt_rollback_fingerprint"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_prompt_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_ai_prompt_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_prompt_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_ai_prompt_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    target_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    provenance: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AIPolicyProfile(Base):
    __tablename__ = "core_ai_policy_profiles"
    __table_args__ = (
        UniqueConstraint("policy_key", name="uq_core_ai_policy_profiles_key"),
        CheckConstraint("product_scope IN ('SHARED', 'SIMPA', 'ORDO')", name="ck_core_ai_policy_profiles_product_scope"),
        CheckConstraint("sensitivity IN ('public', 'internal', 'sensitive')", name="ck_core_ai_policy_profiles_sensitivity"),
        CheckConstraint("provider_policy IN ('local_only', 'local_preferred', 'any')", name="ck_core_ai_policy_profiles_provider_policy"),
        CheckConstraint("max_attempts >= 1 AND max_attempts <= 5", name="ck_core_ai_policy_profiles_attempts"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    policy_key: Mapped[str] = mapped_column(String(160), nullable=False)
    product_scope: Mapped[str] = mapped_column(String(16), nullable=False, default="SHARED", server_default="SHARED")
    sensitivity: Mapped[str] = mapped_column(String(24), nullable=False, default="internal", server_default="internal")
    provider_policy: Mapped[str] = mapped_column(String(32), nullable=False, default="local_only", server_default="local_only")
    allow_external: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    require_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=2, server_default="2")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class AIJob(Base):
    __tablename__ = "core_ai_jobs"
    __table_args__ = (
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ai_jobs_product"),
        CheckConstraint("job_type IN ('chat', 'structured')", name="ck_core_ai_jobs_type"),
        CheckConstraint("status IN ('queued', 'running', 'succeeded', 'failed', 'review_required')", name="ck_core_ai_jobs_status"),
        CheckConstraint("sensitivity IN ('public', 'internal', 'sensitive')", name="ck_core_ai_jobs_sensitivity"),
        CheckConstraint("effective_provider_policy IN ('local_only', 'local_preferred', 'any')", name="ck_core_ai_jobs_provider_policy"),
        CheckConstraint("human_review_status IN ('not_required', 'pending', 'accepted', 'rejected')", name="ck_core_ai_jobs_review_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_ai_models.id"), nullable=False)
    prompt_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_ai_prompt_versions.id"), nullable=False)
    policy_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_ai_policy_profiles.id"), nullable=False)
    job_type: Mapped[str] = mapped_column(String(24), nullable=False, default="chat", server_default="chat")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued", server_default="queued")
    sensitivity: Mapped[str] = mapped_column(String(24), nullable=False, default="internal", server_default="internal")
    effective_provider_policy: Mapped[str] = mapped_column(String(32), nullable=False)
    request_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    request_text: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    output_text: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    structured_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    model_name: Mapped[str] = mapped_column(String(300), nullable=False, default="", server_default="")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    human_review_status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", server_default="pending")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    rq_job_id: Mapped[str] = mapped_column(String(160), nullable=False, default="", server_default="")
    queued_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class AIJobAttempt(Base):
    __tablename__ = "core_ai_job_attempts"
    __table_args__ = (
        UniqueConstraint("job_id", "attempt_no", name="uq_core_ai_job_attempts_job_attempt"),
        CheckConstraint("status IN ('running', 'succeeded', 'failed')", name="ck_core_ai_job_attempts_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_ai_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False)
    model_name: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="running", server_default="running")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AIAuditEvent(Base):
    __tablename__ = "core_ai_audit_events"
    __table_args__ = (
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ai_audit_events_product"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    actor_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AIEmbedding(Base):
    __tablename__ = "core_ai_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "namespace",
            "source_type",
            "source_id",
            "chunk_index",
            "content_sha256",
            "model_id",
            name="uq_core_ai_embeddings_identity",
        ),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ai_embeddings_product"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    namespace: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_id: Mapped[str] = mapped_column(String(220), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("core_ai_models.id"), nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_data: Mapped[list] = mapped_column(JSON, nullable=False)
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AIModelRegistration(Base):
    """Immutable capability/model identity plus a separately controlled lifecycle state."""

    __tablename__ = "core_ai_model_registrations"
    __table_args__ = (
        UniqueConstraint("registry_fingerprint", name="uq_core_ai_model_registration_fingerprint"),
        CheckConstraint("product_scope IN ('SHARED', 'SIMPA', 'ORDO')", name="ck_core_ai_model_registration_scope"),
        CheckConstraint(
            "model_family IN ('statistical_ml', 'embedding', 'llm', 'vlm')",
            name="ck_core_ai_model_registration_family",
        ),
        CheckConstraint(
            "lifecycle_state IN ('candidate', 'challenger', 'champion', 'retired')",
            name="ck_core_ai_model_registration_lifecycle",
        ),
        CheckConstraint("length(registry_fingerprint) = 64", name="ck_core_ai_model_registration_fingerprint"),
        CheckConstraint(
            "artifact_checksum IS NULL OR length(artifact_checksum) = 64",
            name="ck_core_ai_model_registration_artifact_checksum",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    capability_key: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    product_scope: Mapped[str] = mapped_column(String(16), nullable=False)
    model_family: Mapped[str] = mapped_column(String(32), nullable=False)
    model_key: Mapped[str] = mapped_column(String(220), nullable=False)
    runtime_model_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_ai_models.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    provider_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    runtime_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    version: Mapped[str] = mapped_column(String(160), nullable=False)
    revision: Mapped[str | None] = mapped_column(String(160), nullable=True)
    artifact_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    artifact_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provenance: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    registry_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(String(24), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    retired_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    retired_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AIModelFallback(Base):
    __tablename__ = "core_ai_model_fallbacks"
    __table_args__ = (
        UniqueConstraint("source_registration_id", "target_registration_id", name="uq_core_ai_model_fallback_edge"),
        UniqueConstraint("source_registration_id", "priority", name="uq_core_ai_model_fallback_priority"),
        CheckConstraint("source_registration_id != target_registration_id", name="ck_core_ai_model_fallback_not_self"),
        CheckConstraint("priority >= 1", name="ck_core_ai_model_fallback_priority"),
        CheckConstraint("length(fingerprint) = 64", name="ck_core_ai_model_fallback_fingerprint"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_registration_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_ai_model_registrations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_registration_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_ai_model_registrations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_codes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    semantically_equivalent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    provenance: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AIEvaluationDataset(Base):
    __tablename__ = "core_ai_evaluation_datasets"
    __table_args__ = (
        UniqueConstraint("dataset_key", "version", name="uq_core_ai_evaluation_dataset_version"),
        UniqueConstraint("dataset_fingerprint", name="uq_core_ai_evaluation_dataset_fingerprint"),
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ai_evaluation_dataset_product"),
        CheckConstraint(
            "sensitivity IN ('public', 'internal', 'sensitive', 'synthetic_non_production')",
            name="ck_core_ai_evaluation_dataset_sensitivity",
        ),
        CheckConstraint("approval_state IN ('draft', 'approved')", name="ck_core_ai_evaluation_dataset_approval"),
        CheckConstraint("case_count >= 1", name="ck_core_ai_evaluation_dataset_case_count"),
        CheckConstraint(
            "length(cases_sha256) = 64 AND length(dataset_fingerprint) = 64",
            name="ck_core_ai_evaluation_dataset_fingerprints",
        ),
        CheckConstraint(
            "foundation_only_not_production_promotion_evidence = true",
            name="ck_core_ai_evaluation_dataset_foundation_only",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    dataset_key: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    schema_version: Mapped[str] = mapped_column(String(80), nullable=False)
    capability_coverage: Mapped[list] = mapped_column(JSON, nullable=False)
    cases_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    case_count: Mapped[int] = mapped_column(Integer, nullable=False)
    source_provenance: Mapped[str] = mapped_column(Text, nullable=False)
    sensitivity: Mapped[str] = mapped_column(String(32), nullable=False)
    frozen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    frozen_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    approval_state: Mapped[str] = mapped_column(String(24), nullable=False)
    owner: Mapped[str] = mapped_column(String(180), nullable=False)
    foundation_only_not_production_promotion_evidence: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    manifest_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    dataset_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AIEvaluationRun(Base):
    __tablename__ = "core_ai_evaluation_runs"
    __table_args__ = (
        CheckConstraint("product_code IN ('SIMPA', 'ORDO')", name="ck_core_ai_evaluation_run_product"),
        CheckConstraint(
            "status IN ('created', 'running', 'completed', 'failed')",
            name="ck_core_ai_evaluation_run_status",
        ),
        CheckConstraint("length(input_fingerprint) = 64", name="ck_core_ai_evaluation_run_input_fingerprint"),
        CheckConstraint("length(environment_fingerprint) = 64", name="ck_core_ai_evaluation_run_environment_fingerprint"),
        CheckConstraint(
            "result_fingerprint IS NULL OR length(result_fingerprint) = 64",
            name="ck_core_ai_evaluation_run_result_fingerprint",
        ),
        CheckConstraint(
            "(status IN ('created', 'running') AND result_fingerprint IS NULL AND completed_at IS NULL) "
            "OR (status IN ('completed', 'failed') AND result_fingerprint IS NOT NULL AND completed_at IS NOT NULL)",
            name="ck_core_ai_evaluation_run_terminal_state",
        ),
        CheckConstraint(
            "(status = 'failed' AND length(failure_reason) > 0) OR "
            "(status != 'failed' AND failure_reason = '')",
            name="ck_core_ai_evaluation_run_failure_state",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_code: Mapped[str] = mapped_column(ForeignKey("core_products.code"), nullable=False, index=True)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_ai_evaluation_datasets.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    model_registration_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_ai_model_registrations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    baseline_registration_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_ai_model_registrations.id", ondelete="RESTRICT"), nullable=True
    )
    prompt_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_ai_prompt_versions.id", ondelete="RESTRICT"), nullable=True
    )
    policy_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_ai_policy_profiles.id", ondelete="RESTRICT"), nullable=True
    )
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    environment_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    provenance: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="created", server_default="created")
    result_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_reason: Mapped[str] = mapped_column(String(180), nullable=False, default="", server_default="")
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AIEvaluationResult(Base):
    __tablename__ = "core_ai_evaluation_results"
    __table_args__ = (
        UniqueConstraint("evaluation_run_id", "sequence_no", name="uq_core_ai_evaluation_result_sequence"),
        CheckConstraint(
            "result_type IN ('metric', 'safety', 'reliability', 'provenance', 'evidence')",
            name="ck_core_ai_evaluation_result_type",
        ),
        CheckConstraint("sequence_no >= 1", name="ck_core_ai_evaluation_result_sequence"),
        CheckConstraint("length(fingerprint) = 64", name="ck_core_ai_evaluation_result_fingerprint"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_ai_evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    result_type: Mapped[str] = mapped_column(String(24), nullable=False)
    result_key: Mapped[str] = mapped_column(String(180), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AIEvaluationReview(Base):
    __tablename__ = "core_ai_evaluation_reviews"
    __table_args__ = (
        CheckConstraint(
            "decision IN ('pending', 'approved', 'changes_requested', 'rejected')",
            name="ck_core_ai_evaluation_review_decision",
        ),
        CheckConstraint(
            "(is_final = false AND decision = 'pending') OR (is_final = true AND decision != 'pending')",
            name="ck_core_ai_evaluation_review_final_state",
        ),
        CheckConstraint("length(fingerprint) = 64", name="ck_core_ai_evaluation_review_fingerprint"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_ai_evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_membership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core_memberships.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    evidence_reference: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    reviewed_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
