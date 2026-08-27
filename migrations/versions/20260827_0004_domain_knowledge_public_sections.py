"""domain knowledge registry and structured public sections

Revision ID: 20260827_0004
Revises: 20260827_0003
Create Date: 2026-08-27
"""

from alembic import op
import sqlalchemy as sa

revision = "20260827_0004"
down_revision = "20260827_0003"
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
        "knowledge_domains",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("code", sa.String(160), nullable=False),
        sa.Column("product_scope", sa.String(16), nullable=False),
        sa.Column("parent_id", UUID, sa.ForeignKey("knowledge_domains.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title_sr", sa.String(320), nullable=False),
        sa.Column("title_en", sa.String(320), nullable=False),
        sa.Column("description_sr", sa.Text(), nullable=False, server_default=""),
        sa.Column("description_en", sa.Text(), nullable=False, server_default=""),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_timestamps(),
        sa.UniqueConstraint("code", name="uq_knowledge_domains_code"),
        sa.CheckConstraint("product_scope IN ('ISI', 'SIMPA', 'ORDO', 'SHARED')", name="ck_knowledge_domains_product_scope"),
    )
    op.create_index("ix_knowledge_domains_code", "knowledge_domains", ["code"])
    op.create_index("ix_knowledge_domains_product_scope", "knowledge_domains", ["product_scope"])

    op.create_table(
        "knowledge_sources",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("source_key", sa.String(220), nullable=False),
        sa.Column("knowledge_scope", sa.String(24), nullable=False, server_default="PUBLIC"),
        sa.Column("organization_id", UUID, sa.ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("product_scope", sa.String(16), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False, server_default="sr-Latn"),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("source_uri", sa.String(1500), nullable=False, server_default=""),
        sa.Column("origin_name", sa.String(500), nullable=False, server_default=""),
        sa.Column("authority_level", sa.String(24), nullable=False, server_default="institutional"),
        sa.Column("review_status", sa.String(24), nullable=False, server_default="reviewed"),
        sa.Column("sensitivity", sa.String(24), nullable=False, server_default="public"),
        sa.Column("rag_eligible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("content_sha256", sa.String(64), nullable=False, server_default=""),
        sa.Column("provenance", sa.Text(), nullable=False, server_default=""),
        *_timestamps(),
        sa.UniqueConstraint("source_key", name="uq_knowledge_sources_source_key"),
        sa.CheckConstraint("knowledge_scope IN ('PUBLIC', 'ORGANIZATION')", name="ck_knowledge_sources_scope"),
        sa.CheckConstraint("product_scope IN ('ISI', 'SIMPA', 'ORDO', 'SHARED')", name="ck_knowledge_sources_product_scope"),
        sa.CheckConstraint("locale IN ('sr-Latn', 'en', 'multi')", name="ck_knowledge_sources_locale"),
        sa.CheckConstraint("authority_level IN ('primary', 'institutional', 'reference', 'working')", name="ck_knowledge_sources_authority"),
        sa.CheckConstraint("review_status IN ('draft', 'reviewed', 'approved', 'retired')", name="ck_knowledge_sources_review_status"),
        sa.CheckConstraint("sensitivity IN ('public', 'internal', 'restricted')", name="ck_knowledge_sources_sensitivity"),
        sa.CheckConstraint("(knowledge_scope = 'ORGANIZATION' AND organization_id IS NOT NULL) OR (knowledge_scope = 'PUBLIC' AND organization_id IS NULL)", name="ck_knowledge_sources_org_scope"),
    )
    op.create_index("ix_knowledge_sources_source_key", "knowledge_sources", ["source_key"])
    op.create_index("ix_knowledge_sources_product_scope", "knowledge_sources", ["product_scope"])
    op.create_index("ix_knowledge_sources_organization_id", "knowledge_sources", ["organization_id"])

    op.create_table(
        "knowledge_source_domains",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("knowledge_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain_id", UUID, sa.ForeignKey("knowledge_domains.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("source_id", "domain_id", name="uq_knowledge_source_domain"),
    )
    op.create_index("ix_knowledge_source_domains_source_id", "knowledge_source_domains", ["source_id"])
    op.create_index("ix_knowledge_source_domains_domain_id", "knowledge_source_domains", ["domain_id"])

    op.create_table(
        "public_page_sections",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("page_id", UUID, sa.ForeignKey("public_pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_key", sa.String(180), nullable=False),
        sa.Column("product_scope", sa.String(16), nullable=False),
        sa.Column("domain_code", sa.String(160), nullable=False, server_default=""),
        sa.Column("visual_kind", sa.String(64), nullable=False, server_default="editorial"),
        sa.Column("theme", sa.String(32), nullable=False, server_default="neutral"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        *_timestamps(),
        sa.UniqueConstraint("page_id", "section_key", name="uq_public_page_section_key"),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_public_page_sections_status"),
        sa.CheckConstraint("product_scope IN ('ISI', 'SIMPA', 'ORDO', 'SHARED')", name="ck_public_page_sections_product_scope"),
    )
    op.create_index("ix_public_page_sections_page_id", "public_page_sections", ["page_id"])
    op.create_index("ix_public_page_sections_domain_code", "public_page_sections", ["domain_code"])
    op.create_index("ix_public_page_sections_status", "public_page_sections", ["status"])

    op.create_table(
        "public_page_section_translations",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("section_id", UUID, sa.ForeignKey("public_page_sections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("eyebrow", sa.String(180), nullable=False, server_default=""),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("lead", sa.Text(), nullable=False, server_default=""),
        sa.Column("body_html", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("section_id", "locale", name="uq_public_page_section_translation_locale"),
        sa.CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_page_section_translations_locale"),
    )
    op.create_index("ix_public_page_section_translations_section_id", "public_page_section_translations", ["section_id"])
    op.create_index("ix_public_page_section_translations_locale", "public_page_section_translations", ["locale"])

    op.create_table(
        "public_page_section_items",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("section_id", UUID, sa.ForeignKey("public_page_sections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_key", sa.String(180), nullable=False),
        sa.Column("item_kind", sa.String(32), nullable=False, server_default="fact"),
        sa.Column("domain_code", sa.String(160), nullable=False, server_default=""),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("section_id", "item_key", name="uq_public_page_section_item_key"),
        sa.CheckConstraint("item_kind IN ('principle', 'domain', 'indicator', 'step', 'stakeholder', 'outcome', 'source', 'question', 'fact')", name="ck_public_page_section_items_kind"),
    )
    op.create_index("ix_public_page_section_items_section_id", "public_page_section_items", ["section_id"])
    op.create_index("ix_public_page_section_items_domain_code", "public_page_section_items", ["domain_code"])

    op.create_table(
        "public_page_section_item_translations",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("item_id", UUID, sa.ForeignKey("public_page_section_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("label", sa.String(320), nullable=False),
        sa.Column("value", sa.String(500), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("item_id", "locale", name="uq_public_page_section_item_translation_locale"),
        sa.CheckConstraint("locale IN ('sr-Latn', 'en')", name="ck_public_page_section_item_translations_locale"),
    )
    op.create_index("ix_public_page_section_item_translations_item_id", "public_page_section_item_translations", ["item_id"])
    op.create_index("ix_public_page_section_item_translations_locale", "public_page_section_item_translations", ["locale"])


def downgrade() -> None:
    for table in (
        "public_page_section_item_translations",
        "public_page_section_items",
        "public_page_section_translations",
        "public_page_sections",
        "knowledge_source_domains",
        "knowledge_sources",
        "knowledge_domains",
    ):
        op.drop_table(table)
