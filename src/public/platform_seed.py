from __future__ import annotations

from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.public_content.models import PublicPage, PublicPageTranslation


def seed_platform_pages(session: Session, payload: dict) -> dict[str, int]:
    """Idempotently seed SIMPA/ORDO public platform pages as draft-only content."""
    counts = {
        "pages_created": 0,
        "pages_updated": 0,
        "translations_created": 0,
        "translations_updated": 0,
    }
    for item in payload["pages"]:
        page = session.scalar(select(PublicPage).where(PublicPage.page_key == item["page_key"]))
        if page is None:
            page = PublicPage(
                page_key=item["page_key"],
                page_type=item["page_type"],
                status="draft",
                navigation_order=item["navigation_order"],
                is_navigation=True,
            )
            session.add(page)
            session.flush()
            counts["pages_created"] += 1
        else:
            page.page_type = item["page_type"]
            page.navigation_order = item["navigation_order"]
            page.is_navigation = True
            if page.status == "archived":
                page.status = "draft"
            counts["pages_updated"] += 1

        for locale, values in item["translations"].items():
            translation = session.scalar(
                select(PublicPageTranslation).where(
                    PublicPageTranslation.page_id == page.id,
                    PublicPageTranslation.locale == locale,
                )
            )
            if translation is None:
                translation = PublicPageTranslation(page_id=page.id, locale=locale)
                session.add(translation)
                counts["translations_created"] += 1
            else:
                counts["translations_updated"] += 1

            translation.route_path = values["route_path"]
            translation.title = values["title"]
            translation.summary = values["summary"]
            translation.body_html = values["body_html"]
            translation.body_text = BeautifulSoup(values["body_html"], "html.parser").get_text(" ", strip=True)
            translation.seo_title = values["title"]
            translation.meta_description = values["meta_description"]
            translation.source_url = ""
            translation.source_content_sha256 = ""

    session.commit()
    return counts


# Backward-compatible service alias for callers that used the old tool-level name.
seed = seed_platform_pages
