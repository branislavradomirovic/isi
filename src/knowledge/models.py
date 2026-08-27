from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.platform.identity.models import Organization as _Organization  # noqa: F401


class KnowledgeTimestampMixin:
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class KnowledgeDomain(KnowledgeTimestampMixin, Base):
    __tablename__ = "knowledge_domains"
    __table_args__ = (
        UniqueConstraint("code", name="uq_knowledge_domains_code"),
        CheckConstraint("product_scope IN ('ISI', 'SIMPA', 'ORDO', 'SHARED')", name="ck_knowledge_domains_product_scope"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    product_scope: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("knowledge_domains.id", ondelete="SET NULL"), nullable=True)
    title_sr: Mapped[str] = mapped_column(String(320), nullable=False)
    title_en: Mapped[str] = mapped_column(String(320), nullable=False)
    description_sr: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    description_en: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1000, server_default="1000")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class KnowledgeSource(KnowledgeTimestampMixin, Base):
    __tablename__ = "knowledge_sources"
    __table_args__ = (
        UniqueConstraint("source_key", name="uq_knowledge_sources_source_key"),
        CheckConstraint("knowledge_scope IN ('PUBLIC', 'ORGANIZATION')", name="ck_knowledge_sources_scope"),
        CheckConstraint("product_scope IN ('ISI', 'SIMPA', 'ORDO', 'SHARED')", name="ck_knowledge_sources_product_scope"),
        CheckConstraint("locale IN ('sr-Latn', 'en', 'multi')", name="ck_knowledge_sources_locale"),
        CheckConstraint("authority_level IN ('primary', 'institutional', 'reference', 'working')", name="ck_knowledge_sources_authority"),
        CheckConstraint("review_status IN ('draft', 'reviewed', 'approved', 'retired')", name="ck_knowledge_sources_review_status"),
        CheckConstraint("sensitivity IN ('public', 'internal', 'restricted')", name="ck_knowledge_sources_sensitivity"),
        CheckConstraint(
            "(knowledge_scope = 'ORGANIZATION' AND organization_id IS NOT NULL) OR "
            "(knowledge_scope = 'PUBLIC' AND organization_id IS NULL)",
            name="ck_knowledge_sources_org_scope",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_key: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    knowledge_scope: Mapped[str] = mapped_column(String(24), nullable=False, default="PUBLIC", server_default="PUBLIC")
    organization_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    product_scope: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="sr-Latn", server_default="sr-Latn")
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_uri: Mapped[str] = mapped_column(String(1500), nullable=False, default="", server_default="")
    origin_name: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    authority_level: Mapped[str] = mapped_column(String(24), nullable=False, default="institutional", server_default="institutional")
    review_status: Mapped[str] = mapped_column(String(24), nullable=False, default="reviewed", server_default="reviewed")
    sensitivity: Mapped[str] = mapped_column(String(24), nullable=False, default="public", server_default="public")
    rag_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    effective_from: Mapped[object | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[object | None] = mapped_column(Date, nullable=True)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    provenance: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")


class KnowledgeSourceDomain(Base):
    __tablename__ = "knowledge_source_domains"
    __table_args__ = (UniqueConstraint("source_id", "domain_id", name="uq_knowledge_source_domain"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("knowledge_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    domain_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("knowledge_domains.id", ondelete="CASCADE"), nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
