from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class PublicTimestampMixin:
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PublicMediaAsset(PublicTimestampMixin, Base):
    __tablename__ = "public_media_assets"
    __table_args__ = (
        CheckConstraint(
            "migration_status IN ('pending', 'downloaded', 'verified', 'failed', 'archived')",
            name="ck_public_media_assets_migration_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_url: Mapped[str] = mapped_column(String(1200), nullable=False, unique=True, index=True)
    legacy_path: Mapped[str] = mapped_column(String(700), nullable=False, default="", server_default="")
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False, default="asset", server_default="asset")
    extension: Mapped[str] = mapped_column(String(16), nullable=False, default="", server_default="")
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="sr-Latn", server_default="sr-Latn")
    discovered_from: Mapped[str] = mapped_column(String(1200), nullable=False, default="", server_default="")
    migration_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending")
    storage_path: Mapped[str] = mapped_column(String(1200), nullable=False, default="", server_default="")
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    mime_type: Mapped[str] = mapped_column(String(160), nullable=False, default="", server_default="")


class PublicPage(PublicTimestampMixin, Base):
    __tablename__ = "public_pages"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_pages_status"),
        CheckConstraint(
            "page_type IN ('home', 'standard', 'team_index', 'activity_index', 'document_index', 'library_index', 'program', 'heritage', 'platform', 'legal')",
            name="ck_public_pages_page_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    page_key: Mapped[str] = mapped_column(String(180), nullable=False, unique=True, index=True)
    page_type: Mapped[str] = mapped_column(String(40), nullable=False, default="standard", server_default="standard")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft", index=True)
    navigation_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1000, server_default="1000")
    is_navigation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    published_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PublicPageTranslation(PublicTimestampMixin, Base):
    __tablename__ = "public_page_translations"
    __table_args__ = (
        UniqueConstraint("page_id", "locale", name="uq_public_page_translation_locale"),
        UniqueConstraint("route_path", name="uq_public_page_translation_route_path"),
        CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_page_translations_locale"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    page_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("public_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    route_path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(320), nullable=False, default="", server_default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    body_html: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    body_text: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    seo_title: Mapped[str] = mapped_column(String(320), nullable=False, default="", server_default="")
    meta_description: Mapped[str] = mapped_column(String(700), nullable=False, default="", server_default="")
    source_url: Mapped[str] = mapped_column(String(1200), nullable=False, default="", server_default="")
    source_content_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    source_fetched_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    imported_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PublicLegacySource(PublicTimestampMixin, Base):
    __tablename__ = "public_legacy_sources"
    __table_args__ = (
        UniqueConstraint("source_url", name="uq_public_legacy_sources_source_url"),
        CheckConstraint(
            "mapping_status IN ('unmapped', 'mapped_page', 'mapped_entity', 'ignored')",
            name="ck_public_legacy_sources_mapping_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_url: Mapped[str] = mapped_column(String(1200), nullable=False, index=True)
    legacy_path: Mapped[str] = mapped_column(String(700), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(320), nullable=False, default="", server_default="")
    canonical_url: Mapped[str] = mapped_column(String(1200), nullable=False, default="", server_default="")
    http_status: Mapped[int] = mapped_column(Integer, nullable=False)
    inventory_content_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    snapshot_content_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    source_html_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    snapshot_file: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")
    extraction_method: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    mapping_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unmapped", server_default="unmapped")
    mapped_page_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("public_pages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_fetched_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    imported_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PublicRedirect(PublicTimestampMixin, Base):
    __tablename__ = "public_redirects"
    __table_args__ = (
        UniqueConstraint("legacy_path", "locale", name="uq_public_redirect_legacy_locale"),
        CheckConstraint("status IN ('pending', 'approved', 'disabled')", name="ck_public_redirects_status"),
        CheckConstraint("http_status_code IN (301, 302, 307, 308)", name="ck_public_redirects_http_status_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    legacy_path: Mapped[str] = mapped_column(String(700), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False)
    target_path: Mapped[str] = mapped_column(String(700), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", server_default="pending")
    http_status_code: Mapped[int] = mapped_column(Integer, nullable=False, default=301, server_default="301")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")


class PublicPerson(PublicTimestampMixin, Base):
    __tablename__ = "public_people"
    __table_args__ = (CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_people_status"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1000, server_default="1000")
    image_asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("public_media_assets.id", ondelete="SET NULL"), nullable=True)


class PublicPersonTranslation(Base):
    __tablename__ = "public_person_translations"
    __table_args__ = (
        UniqueConstraint("person_id", "locale", name="uq_public_person_translation_locale"),
        CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_person_translations_locale"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("public_people.id", ondelete="CASCADE"), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    role_title: Mapped[str] = mapped_column(String(320), nullable=False, default="", server_default="")
    bio_html: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")


class PublicActivity(PublicTimestampMixin, Base):
    __tablename__ = "public_activities"
    __table_args__ = (CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_activities_status"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    occurred_on: Mapped[object | None] = mapped_column(Date, nullable=True)
    cover_asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("public_media_assets.id", ondelete="SET NULL"), nullable=True)


class PublicActivityTranslation(Base):
    __tablename__ = "public_activity_translations"
    __table_args__ = (
        UniqueConstraint("activity_id", "locale", name="uq_public_activity_translation_locale"),
        CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_activity_translations_locale"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("public_activities.id", ondelete="CASCADE"), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False)
    slug: Mapped[str] = mapped_column(String(240), nullable=False)
    title: Mapped[str] = mapped_column(String(320), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    body_html: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")


class PublicPublication(PublicTimestampMixin, Base):
    __tablename__ = "public_publications"
    __table_args__ = (CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_publications_status"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    published_on: Mapped[object | None] = mapped_column(Date, nullable=True)
    document_asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("public_media_assets.id", ondelete="SET NULL"), nullable=True)


class PublicPublicationTranslation(Base):
    __tablename__ = "public_publication_translations"
    __table_args__ = (
        UniqueConstraint("publication_id", "locale", name="uq_public_publication_translation_locale"),
        CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_publication_translations_locale"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    publication_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("public_publications.id", ondelete="CASCADE"), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False)
    slug: Mapped[str] = mapped_column(String(240), nullable=False)
    title: Mapped[str] = mapped_column(String(320), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    citation: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")


class PublicDocument(PublicTimestampMixin, Base):
    __tablename__ = "public_documents"
    __table_args__ = (CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_documents_status"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    document_asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("public_media_assets.id", ondelete="SET NULL"), nullable=True)


class PublicDocumentTranslation(Base):
    __tablename__ = "public_document_translations"
    __table_args__ = (
        UniqueConstraint("document_id", "locale", name="uq_public_document_translation_locale"),
        CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_document_translations_locale"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("public_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False)
    slug: Mapped[str] = mapped_column(String(240), nullable=False)
    title: Mapped[str] = mapped_column(String(320), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")


class PublicProgram(PublicTimestampMixin, Base):
    __tablename__ = "public_programs"
    __table_args__ = (CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_programs_status"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1000, server_default="1000")
    external_url: Mapped[str] = mapped_column(String(1200), nullable=False, default="", server_default="")


class PublicProgramTranslation(Base):
    __tablename__ = "public_program_translations"
    __table_args__ = (
        UniqueConstraint("program_id", "locale", name="uq_public_program_translation_locale"),
        CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_program_translations_locale"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("public_programs.id", ondelete="CASCADE"), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False)
    slug: Mapped[str] = mapped_column(String(240), nullable=False)
    title: Mapped[str] = mapped_column(String(320), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    body_html: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")


class PublicPartner(PublicTimestampMixin, Base):
    __tablename__ = "public_partners"
    __table_args__ = (CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_partners_status"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", server_default="draft")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1000, server_default="1000")
    website_url: Mapped[str] = mapped_column(String(1200), nullable=False, default="", server_default="")
    logo_asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("public_media_assets.id", ondelete="SET NULL"), nullable=True)


class PublicPartnerTranslation(Base):
    __tablename__ = "public_partner_translations"
    __table_args__ = (
        UniqueConstraint("partner_id", "locale", name="uq_public_partner_translation_locale"),
        CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_partner_translations_locale"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("public_partners.id", ondelete="CASCADE"), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(320), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
