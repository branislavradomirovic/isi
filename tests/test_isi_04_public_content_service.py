from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.database import Base
from src.public.content_service import get_page_by_key, list_navigation, list_platforms
from src.public_content.models import PublicPage, PublicPageTranslation


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _add(session, key, locale, route, *, page_type="standard", status="draft", nav=False, order=100):
    page = PublicPage(page_key=key, page_type=page_type, status=status, is_navigation=nav, navigation_order=order)
    session.add(page); session.flush()
    session.add(PublicPageTranslation(page_id=page.id, locale=locale, route_path=route, title=key, summary="summary", body_html="<p>body</p>", body_text="body", seo_title=key, meta_description="meta"))
    session.commit()
    return page


def test_drafts_are_hidden_without_preview():
    with _session() as session:
        _add(session, "home", "sr-Latn", "/", status="draft")
        assert get_page_by_key(session, page_key="home", locale="sr-Latn", include_drafts=False) is None
        assert get_page_by_key(session, page_key="home", locale="sr-Latn", include_drafts=True) is not None


def test_navigation_and_platforms_are_db_backed():
    with _session() as session:
        _add(session, "platform.simpa", "sr-Latn", "/simpa/", page_type="platform", status="draft", nav=True, order=5)
        _add(session, "legacy.tim", "sr-Latn", "/tim/", status="draft", nav=True, order=10)
        nav = list_navigation(session, locale="sr-Latn", include_drafts=True)
        assert [row.page_key for row in nav] == ["platform.simpa", "legacy.tim"]
        platforms = list_platforms(session, locale="sr-Latn", include_drafts=True)
        assert [row.page_key for row in platforms] == ["platform.simpa"]
