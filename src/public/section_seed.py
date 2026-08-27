from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.public_content.models import PublicPage
from src.public_content.sections import (
    PublicPageSection,
    PublicPageSectionItem,
    PublicPageSectionItemTranslation,
    PublicPageSectionTranslation,
)


def seed_public_sections(session: Session, payload: dict) -> dict[str, int]:
    """Idempotently seed structured bilingual draft-only public sections."""
    counts = {"sections": 0, "section_translations": 0, "items": 0, "item_translations": 0}
    for row in payload["sections"]:
        page = session.scalar(select(PublicPage).where(PublicPage.page_key == row["page_key"]))
        if page is None:
            raise ValueError(f"public page missing for section seed: {row['page_key']}")
        section = session.scalar(select(PublicPageSection).where(PublicPageSection.page_id == page.id, PublicPageSection.section_key == row["section_key"]))
        if section is None:
            section = PublicPageSection(page_id=page.id, section_key=row["section_key"], product_scope=row["product_scope"])
            session.add(section)
            session.flush()
        section.product_scope = row["product_scope"]
        section.domain_code = row.get("domain_code", "")
        section.visual_kind = row.get("visual_kind", "editorial")
        section.theme = row.get("theme", "neutral")
        section.sort_order = row.get("sort_order", 1000)
        section.status = "draft"
        counts["sections"] += 1

        for locale, values in row["translations"].items():
            tr = session.scalar(select(PublicPageSectionTranslation).where(PublicPageSectionTranslation.section_id == section.id, PublicPageSectionTranslation.locale == locale))
            if tr is None:
                tr = PublicPageSectionTranslation(section_id=section.id, locale=locale, title=values["title"])
                session.add(tr)
            tr.eyebrow = values.get("eyebrow", "")
            tr.title = values["title"]
            tr.lead = values.get("lead", "")
            tr.body_html = values.get("body_html", "")
            counts["section_translations"] += 1

        desired_keys = {item["item_key"] for item in row.get("items", [])}
        for existing in session.scalars(select(PublicPageSectionItem).where(PublicPageSectionItem.section_id == section.id)).all():
            if existing.item_key not in desired_keys:
                session.delete(existing)
        session.flush()
        for order, values in enumerate(row.get("items", []), start=1):
            item = session.scalar(select(PublicPageSectionItem).where(PublicPageSectionItem.section_id == section.id, PublicPageSectionItem.item_key == values["item_key"]))
            if item is None:
                item = PublicPageSectionItem(section_id=section.id, item_key=values["item_key"], item_kind=values["item_kind"])
                session.add(item)
                session.flush()
            item.item_kind = values["item_kind"]
            item.domain_code = values.get("domain_code", "")
            item.sort_order = values.get("sort_order", order * 10)
            item.is_featured = values.get("is_featured", False)
            counts["items"] += 1
            for locale, tv in values["translations"].items():
                itr = session.scalar(select(PublicPageSectionItemTranslation).where(PublicPageSectionItemTranslation.item_id == item.id, PublicPageSectionItemTranslation.locale == locale))
                if itr is None:
                    itr = PublicPageSectionItemTranslation(item_id=item.id, locale=locale, label=tv["label"])
                    session.add(itr)
                itr.label = tv["label"]
                itr.value = tv.get("value", "")
                itr.description = tv.get("description", "")
                counts["item_translations"] += 1
    session.commit()
    return counts
