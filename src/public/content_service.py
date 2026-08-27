from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.public_content.models import PublicPage, PublicPageTranslation


@dataclass(frozen=True)
class PublicPageView:
    page_id: object
    page_key: str
    page_type: str
    status: str
    locale: str
    route_path: str
    title: str
    summary: str
    body_html: str
    body_text: str
    seo_title: str
    meta_description: str

    @property
    def excerpt(self) -> str:
        text = " ".join((self.summary or self.body_text or "").split())
        return text if len(text) <= 220 else text[:217].rstrip() + "…"


def _base_page_query(*, locale: str, include_drafts: bool):
    stmt = (
        select(PublicPage, PublicPageTranslation)
        .join(PublicPageTranslation, PublicPageTranslation.page_id == PublicPage.id)
        .where(PublicPageTranslation.locale == locale)
        .where(PublicPage.status != "archived")
    )
    if not include_drafts:
        stmt = stmt.where(PublicPage.status == "published")
    return stmt


def _view(row) -> PublicPageView | None:
    if row is None:
        return None
    page, translation = row
    return PublicPageView(
        page_id=page.id,
        page_key=page.page_key,
        page_type=page.page_type,
        status=page.status,
        locale=translation.locale,
        route_path=translation.route_path,
        title=translation.title,
        summary=translation.summary,
        body_html=translation.body_html,
        body_text=translation.body_text,
        seo_title=translation.seo_title,
        meta_description=translation.meta_description,
    )


def get_page_by_key(
    session: Session,
    *,
    page_key: str,
    locale: str,
    include_drafts: bool = False,
) -> PublicPageView | None:
    row = session.execute(
        _base_page_query(locale=locale, include_drafts=include_drafts).where(PublicPage.page_key == page_key)
    ).first()
    return _view(row)


def get_page_by_route(
    session: Session,
    *,
    route_path: str,
    locale: str,
    include_drafts: bool = False,
) -> PublicPageView | None:
    candidates = [route_path]
    if route_path != "/":
        alternate = route_path.rstrip("/") if route_path.endswith("/") else route_path + "/"
        if alternate and alternate not in candidates:
            candidates.append(alternate)
    for candidate in candidates:
        row = session.execute(
            _base_page_query(locale=locale, include_drafts=include_drafts).where(
                PublicPageTranslation.route_path == candidate
            )
        ).first()
        view = _view(row)
        if view is not None:
            return view
    return None


def list_navigation(
    session: Session,
    *,
    locale: str,
    include_drafts: bool = False,
) -> list[PublicPageView]:
    rows = session.execute(
        _base_page_query(locale=locale, include_drafts=include_drafts)
        .where(PublicPage.is_navigation.is_(True))
        .order_by(PublicPage.navigation_order.asc(), PublicPageTranslation.title.asc())
    ).all()
    return [_view(row) for row in rows if row is not None]


def list_platforms(
    session: Session,
    *,
    locale: str,
    include_drafts: bool = False,
) -> list[PublicPageView]:
    rows = session.execute(
        _base_page_query(locale=locale, include_drafts=include_drafts)
        .where(PublicPage.page_type == "platform")
        .order_by(PublicPage.navigation_order.asc(), PublicPageTranslation.title.asc())
    ).all()
    return [_view(row) for row in rows if row is not None]


def alternate_locale_page(
    session: Session,
    *,
    page_key: str,
    locale: str,
    include_drafts: bool = False,
) -> PublicPageView | None:
    return get_page_by_key(
        session,
        page_key=page_key,
        locale=locale,
        include_drafts=include_drafts,
    )
