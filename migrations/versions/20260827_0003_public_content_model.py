"""public content model and legacy migration staging

Revision ID: 20260827_0003
Revises: 20260827_0002
Create Date: 2026-08-27
"""

from alembic import op
import sqlalchemy as sa

revision = "20260827_0003"
down_revision = "20260827_0002"
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def _timestamps():
    return (
        sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def upgrade() -> None:
    op.create_table(
        "public_media_assets",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("source_url", sa.String(1200), nullable=False),
        sa.Column("legacy_path", sa.String(700), nullable=False, server_default=""),
        sa.Column("asset_type", sa.String(32), nullable=False, server_default="asset"),
        sa.Column("extension", sa.String(16), nullable=False, server_default=""),
        sa.Column("locale", sa.String(16), nullable=False, server_default="sr-Latn"),
        sa.Column("discovered_from", sa.String(1200), nullable=False, server_default=""),
        sa.Column("migration_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("storage_path", sa.String(1200), nullable=False, server_default=""),
        sa.Column("content_sha256", sa.String(64), nullable=False, server_default=""),
        sa.Column("mime_type", sa.String(160), nullable=False, server_default=""),
        *_timestamps(),
        sa.UniqueConstraint("source_url", name="uq_public_media_assets_source_url"),
        sa.CheckConstraint(
            "migration_status IN ('pending', 'downloaded', 'verified', 'failed', 'archived')",
            name="ck_public_media_assets_migration_status",
        ),
    )
    op.create_index("ix_public_media_assets_source_url", "public_media_assets", ["source_url"])

    op.create_table(
        "public_pages",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("page_key", sa.String(180), nullable=False),
        sa.Column("page_type", sa.String(40), nullable=False, server_default="standard"),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("navigation_order", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("is_navigation", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("published_at", TS, nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("page_key", name="uq_public_pages_page_key"),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_pages_status"),
        sa.CheckConstraint(
            "page_type IN ('home', 'standard', 'team_index', 'activity_index', 'document_index', 'library_index', 'program', 'heritage', 'platform', 'legal')",
            name="ck_public_pages_page_type",
        ),
    )
    op.create_index("ix_public_pages_page_key", "public_pages", ["page_key"])
    op.create_index("ix_public_pages_status", "public_pages", ["status"])

    op.create_table(
        "public_page_translations",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("page_id", UUID, sa.ForeignKey("public_pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("route_path", sa.String(500), nullable=False),
        sa.Column("title", sa.String(320), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("body_html", sa.Text(), nullable=False, server_default=""),
        sa.Column("body_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("seo_title", sa.String(320), nullable=False, server_default=""),
        sa.Column("meta_description", sa.String(700), nullable=False, server_default=""),
        sa.Column("source_url", sa.String(1200), nullable=False, server_default=""),
        sa.Column("source_content_sha256", sa.String(64), nullable=False, server_default=""),
        sa.Column("source_fetched_at", TS, nullable=True),
        sa.Column("imported_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        *_timestamps(),
        sa.UniqueConstraint("page_id", "locale", name="uq_public_page_translation_locale"),
        sa.UniqueConstraint("route_path", name="uq_public_page_translation_route_path"),
        sa.CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_page_translations_locale"),
    )
    op.create_index("ix_public_page_translations_page_id", "public_page_translations", ["page_id"])
    op.create_index("ix_public_page_translations_locale", "public_page_translations", ["locale"])
    op.create_index("ix_public_page_translations_route_path", "public_page_translations", ["route_path"])

    op.create_table(
        "public_legacy_sources",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("source_url", sa.String(1200), nullable=False),
        sa.Column("legacy_path", sa.String(700), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("title", sa.String(320), nullable=False, server_default=""),
        sa.Column("canonical_url", sa.String(1200), nullable=False, server_default=""),
        sa.Column("http_status", sa.Integer(), nullable=False),
        sa.Column("inventory_content_sha256", sa.String(64), nullable=False, server_default=""),
        sa.Column("snapshot_content_sha256", sa.String(64), nullable=False, server_default=""),
        sa.Column("source_html_sha256", sa.String(64), nullable=False, server_default=""),
        sa.Column("snapshot_file", sa.String(1000), nullable=False, server_default=""),
        sa.Column("extraction_method", sa.String(120), nullable=False, server_default=""),
        sa.Column("mapping_status", sa.String(32), nullable=False, server_default="unmapped"),
        sa.Column("mapped_page_id", UUID, sa.ForeignKey("public_pages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_fetched_at", TS, nullable=True),
        sa.Column("imported_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        *_timestamps(),
        sa.UniqueConstraint("source_url", name="uq_public_legacy_sources_source_url"),
        sa.CheckConstraint(
            "mapping_status IN ('unmapped', 'mapped_page', 'mapped_entity', 'ignored')",
            name="ck_public_legacy_sources_mapping_status",
        ),
    )
    op.create_index("ix_public_legacy_sources_source_url", "public_legacy_sources", ["source_url"])
    op.create_index("ix_public_legacy_sources_legacy_path", "public_legacy_sources", ["legacy_path"])
    op.create_index("ix_public_legacy_sources_mapped_page_id", "public_legacy_sources", ["mapped_page_id"])

    op.create_table(
        "public_redirects",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("legacy_path", sa.String(700), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("target_path", sa.String(700), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("http_status_code", sa.Integer(), nullable=False, server_default="301"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        *_timestamps(),
        sa.UniqueConstraint("legacy_path", "locale", name="uq_public_redirect_legacy_locale"),
        sa.CheckConstraint("status IN ('pending', 'approved', 'disabled')", name="ck_public_redirects_status"),
        sa.CheckConstraint("http_status_code IN (301, 302, 307, 308)", name="ck_public_redirects_http_status_code"),
    )
    op.create_index("ix_public_redirects_legacy_path", "public_redirects", ["legacy_path"])

    op.create_table(
        "public_people",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("image_asset_id", UUID, sa.ForeignKey("public_media_assets.id", ondelete="SET NULL"), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_people_status"),
    )
    op.create_table(
        "public_person_translations",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("person_id", UUID, sa.ForeignKey("public_people.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("role_title", sa.String(320), nullable=False, server_default=""),
        sa.Column("bio_html", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("person_id", "locale", name="uq_public_person_translation_locale"),
        sa.CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_person_translations_locale"),
    )
    op.create_index("ix_public_person_translations_person_id", "public_person_translations", ["person_id"])

    op.create_table(
        "public_activities",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("occurred_on", sa.Date(), nullable=True),
        sa.Column("cover_asset_id", UUID, sa.ForeignKey("public_media_assets.id", ondelete="SET NULL"), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_activities_status"),
    )
    op.create_table(
        "public_activity_translations",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("activity_id", UUID, sa.ForeignKey("public_activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("slug", sa.String(240), nullable=False),
        sa.Column("title", sa.String(320), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("body_html", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("activity_id", "locale", name="uq_public_activity_translation_locale"),
        sa.CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_activity_translations_locale"),
    )
    op.create_index("ix_public_activity_translations_activity_id", "public_activity_translations", ["activity_id"])

    op.create_table(
        "public_publications",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("published_on", sa.Date(), nullable=True),
        sa.Column("document_asset_id", UUID, sa.ForeignKey("public_media_assets.id", ondelete="SET NULL"), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_publications_status"),
    )
    op.create_table(
        "public_publication_translations",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("publication_id", UUID, sa.ForeignKey("public_publications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("slug", sa.String(240), nullable=False),
        sa.Column("title", sa.String(320), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("citation", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("publication_id", "locale", name="uq_public_publication_translation_locale"),
        sa.CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_publication_translations_locale"),
    )
    op.create_index("ix_public_publication_translations_publication_id", "public_publication_translations", ["publication_id"])

    op.create_table(
        "public_documents",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("document_asset_id", UUID, sa.ForeignKey("public_media_assets.id", ondelete="SET NULL"), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_documents_status"),
    )
    op.create_table(
        "public_document_translations",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("document_id", UUID, sa.ForeignKey("public_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("slug", sa.String(240), nullable=False),
        sa.Column("title", sa.String(320), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("document_id", "locale", name="uq_public_document_translation_locale"),
        sa.CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_document_translations_locale"),
    )
    op.create_index("ix_public_document_translations_document_id", "public_document_translations", ["document_id"])

    op.create_table(
        "public_programs",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("external_url", sa.String(1200), nullable=False, server_default=""),
        *_timestamps(),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_programs_status"),
    )
    op.create_table(
        "public_program_translations",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("program_id", UUID, sa.ForeignKey("public_programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("slug", sa.String(240), nullable=False),
        sa.Column("title", sa.String(320), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("body_html", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("program_id", "locale", name="uq_public_program_translation_locale"),
        sa.CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_program_translations_locale"),
    )
    op.create_index("ix_public_program_translations_program_id", "public_program_translations", ["program_id"])

    op.create_table(
        "public_partners",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("website_url", sa.String(1200), nullable=False, server_default=""),
        sa.Column("logo_asset_id", UUID, sa.ForeignKey("public_media_assets.id", ondelete="SET NULL"), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_partners_status"),
    )
    op.create_table(
        "public_partner_translations",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("partner_id", UUID, sa.ForeignKey("public_partners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("name", sa.String(320), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("partner_id", "locale", name="uq_public_partner_translation_locale"),
        sa.CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_partner_translations_locale"),
    )
    op.create_index("ix_public_partner_translations_partner_id", "public_partner_translations", ["partner_id"])


def downgrade() -> None:
    for table in (
        "public_partner_translations", "public_partners",
        "public_program_translations", "public_programs",
        "public_document_translations", "public_documents",
        "public_publication_translations", "public_publications",
        "public_activity_translations", "public_activities",
        "public_person_translations", "public_people",
        "public_redirects", "public_legacy_sources", "public_page_translations", "public_pages",
        "public_media_assets",
    ):
        op.drop_table(table)
