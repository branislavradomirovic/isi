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
