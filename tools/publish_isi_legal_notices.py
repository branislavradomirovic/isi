"""Publish the owner-reviewed, digest-bound ISI legal notices without overwrites."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import build_engine, build_session_factory
from src.public_content.models import PublicPage, PublicPageTranslation

SOURCE = Path("data/public/legal_notices.json")


def publish(session: Session, raw: bytes, approved_digest: str) -> dict[str, int]:
    digest = hashlib.sha256(raw).hexdigest()
    if digest != approved_digest:
        raise ValueError("legal publication approval digest mismatch")
    payload = json.loads(raw)
    if payload.get("publication_status") != "OWNER_AUTHORIZED_PLACEHOLDERS":
        raise ValueError("unsupported publication authority")
    pages = payload.get("pages", [])
    if len(pages) != 2 or {p["page_key"] for p in pages} != {"legal.terms", "legal.privacy"}:
        raise ValueError("unexpected legal page scope")
    checked = []
    seen_routes: set[str] = set()
    # Complete validation precedes any writes, including autoflush.
    with session.no_autoflush:
        for item in pages:
            if item["page_type"] != "legal" or set(item["translations"]) != {"sr-Latn", "en"}:
                raise ValueError("legal publication requires both locales")
            page = session.scalar(select(PublicPage).where(PublicPage.page_key == item["page_key"]))
            if page is not None and (page.page_type != "legal" or page.status != "published"):
                raise ValueError("existing page requires a separately reviewed update")
            for locale, values in item["translations"].items():
                route = values["route_path"]
                if not route.startswith("/") or route.startswith("//") or route in seen_routes:
                    raise ValueError("invalid or duplicate legal route")
                if (locale == "en") != route.startswith("/en/"):
                    raise ValueError("legal route locale mismatch")
                seen_routes.add(route)
                for key in ("title", "summary", "body_html", "meta_description"):
                    if not values.get(key):
                        raise ValueError("incomplete legal translation")
                existing = session.scalar(select(PublicPageTranslation).where(
                    PublicPageTranslation.route_path == route))
                if existing is not None:
                    if page is None or existing.page_id != page.id or existing.locale != locale:
                        raise ValueError("legal route belongs to different content")
                    if any(getattr(existing, key) != values[key] for key in
                           ("title", "summary", "body_html", "meta_description")):
                        raise ValueError("existing legal content differs; refusing overwrite")
                    if existing.source_content_sha256 != digest:
                        raise ValueError("existing legal content has different provenance")
                elif page is not None:
                    raise ValueError("existing publication is incomplete; refusing implicit repair")
            checked.append((item, page))
    created = 0
    for item, page in checked:
        if page is not None:
            continue
        page = PublicPage(page_key=item["page_key"], page_type="legal", status="published",
                          is_navigation=False, published_at=datetime.now(timezone.utc))
        session.add(page)
        session.flush()
        for locale, values in item["translations"].items():
            session.add(PublicPageTranslation(
                page_id=page.id, locale=locale, **values, seo_title=values["title"],
                body_text=BeautifulSoup(values["body_html"], "html.parser").get_text(" ", strip=True),
                source_content_sha256=digest,
            ))
        created += 1
    session.flush()
    return {"pages_created": created, "pages_unchanged": 2 - created}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved-sha256", required=True)
    args = parser.parse_args()
    factory = build_session_factory(build_engine())
    with factory() as session, session.begin():
        report = publish(session, SOURCE.read_bytes(), args.approved_sha256)
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
