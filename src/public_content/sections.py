from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class SectionTimestampMixin:
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PublicPageSection(SectionTimestampMixin, Base):
    __tablename__ = "public_page_sections"
    __table_args__ = (
        UniqueConstraint("page_id", "section_key", name="uq_public_page_section_key"),
        CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_page_sections_status"),
        CheckConstraint("product_scope IN ('ISI', 'SIMPA', 'ORDO', 'SHARED')", name="ck_public_page_sections_product_scope"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    page_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("public_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    section_key: Mapped[str] = mapped_column(String(180), nullable=False)
    product_scope: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    domain_code: Mapped[str] = mapped_column(String(160), nullable=False, default="", server_default="", index=True)
    visual_kind: Mapped[str] = mapped_column(String(64), nullable=False, default="editorial", server_default="editorial")
    theme: Mapped[str] = mapped_column(String(32), nullable=False, default="neutral", server_default="neutral")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1000, server_default="1000")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft", index=True)


class PublicPageSectionTranslation(Base):
    __tablename__ = "public_page_section_translations"
    __table_args__ = (
        UniqueConstraint("section_id", "locale", name="uq_public_page_section_translation_locale"),
        CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_page_section_translations_locale"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("public_page_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    eyebrow: Mapped[str] = mapped_column(String(180), nullable=False, default="", server_default="")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    lead: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    body_html: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")


class PublicPageSectionItem(Base):
    __tablename__ = "public_page_section_items"
    __table_args__ = (
        UniqueConstraint("section_id", "item_key", name="uq_public_page_section_item_key"),
        CheckConstraint("item_kind IN ('principle', 'domain', 'indicator', 'step', 'stakeholder', 'outcome', 'source', 'question', 'fact')", name="ck_public_page_section_items_kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("public_page_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    item_key: Mapped[str] = mapped_column(String(180), nullable=False)
    item_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="fact", server_default="fact")
    domain_code: Mapped[str] = mapped_column(String(160), nullable=False, default="", server_default="", index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1000, server_default="1000")
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")


class PublicPageSectionItemTranslation(Base):
    __tablename__ = "public_page_section_item_translations"
    __table_args__ = (
        UniqueConstraint("item_id", "locale", name="uq_public_page_section_item_translation_locale"),
        CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_page_section_item_translations_locale"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("public_page_section_items.id", ondelete="CASCADE"), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(320), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
