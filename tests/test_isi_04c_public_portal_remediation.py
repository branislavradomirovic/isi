import json
from pathlib import Path

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.api.dependencies import get_db
from src.core.config import Settings, get_settings
from src.core.database import Base
from src.public.catalog_service import document_catalog_from_html
from src.public_content.models import PublicPage, PublicPageTranslation


ROOT = Path(__file__).resolve().parents[1]


def test_preserved_legacy_document_snapshot_keeps_all_icon_link_titles_and_urls():
    snapshot = json.loads(
        (ROOT / "data/migration/legacy_isi/snapshots/f9b1f91356a536111f721822.json").read_text(encoding="utf-8")
    )
    groups = document_catalog_from_html(snapshot["body_html"])
    items = [item for group in groups for item in group.items]

    assert len(items) == 26
    by_href = {item.href: item for item in items}
    assert by_href["https://sdgs.un.org/2030agenda"].title == "Agenda 2030 za održivi razvoj (SDGs)"
    assert all(item.title and item.href.startswith("https://") for item in items)


def test_icon_link_uses_nearby_document_heading_without_inventing_unpaired_titles():
    paired = '<div><div><h3>Dokument iz izvora</h3><div></div></div><div><a href="https://example.org/doc"><i></i></a></div></div>'
    unpaired = '<div><h3>Institucionalna grupa</h3><div><a href="https://example.org/unpaired"><i></i></a></div></div>'

    groups = document_catalog_from_html(paired + unpaired)
    items = [item for group in groups for item in group.items]

    assert [(item.title, item.href) for item in items] == [
        ("Dokument iz izvora", "https://example.org/doc")
    ]


def _factory():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _translation(page_id, locale, route, title):
    return PublicPageTranslation(
        page_id=page_id,
        locale=locale,
        route_path=route,
        title=title,
        summary=title,
        body_html="<p>Public page</p>",
        body_text="Public page",
        seo_title=title,
        meta_description=title,
    )


def test_english_home_and_footer_mark_serbian_fallback_routes_explicitly():
    factory = _factory()
    with factory() as session:
        home = PublicPage(page_key="home", page_type="home", status="published", is_navigation=True, navigation_order=1)
        session.add(home)
        session.flush()
        session.add_all([
            _translation(home.id, "sr-Latn", "/", "Institut za socijalnu inkluziju"),
            _translation(home.id, "en", "/en/", "Institute for Social Inclusion"),
        ])
        pages = (
            ("legacy.dokumenti", "document_index", "/dokumenti/", "Dokumenti"),
            ("legacy.biblioteka", "library_index", "/biblioteka/", "Biblioteka"),
            ("legacy.inkluzivni-razvoj", "program", "/inkluzivni-razvoj/", "Inkluzivni razvoj"),
        )
        for key, page_type, route, title in pages:
            page = PublicPage(page_key=key, page_type=page_type, status="published", is_navigation=False, navigation_order=10)
            session.add(page)
            session.flush()
            session.add(_translation(page.id, "sr-Latn", route, title))
        session.commit()

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: Settings(
        isi_env="production",
        public_preview_drafts=False,
        public_base_url="https://isi.example",
    )
    client = TestClient(app)
    try:
        response = client.get("/en/")
        assert response.status_code == 200
        soup = BeautifulSoup(response.text, "html.parser")
        expected = {
            "/dokumenti/": "Serbian",
            "/biblioteka/": "Serbian",
            "/inkluzivni-razvoj/": "Serbian",
        }
        for href, language in expected.items():
            anchors = soup.find_all("a", href=href)
            assert anchors
            assert all(language in anchor.get_text(" ", strip=True) for anchor in anchors)
        assert not any(
            anchor.get("href", "").startswith("/en/")
            and anchor.get("href", "").split("/")[-2] in {"dokumenti", "biblioteka", "inkluzivni-razvoj"}
            for anchor in soup.find_all("a", href=True)
        )
    finally:
        app.dependency_overrides.clear()


def test_documents_mobile_layout_has_narrow_viewport_rules():
    css = (ROOT / "src/public/static/css/semantic-polish.css").read_text(encoding="utf-8")
    assert ".semantic-documents-hero h1" in css
    assert "white-space:nowrap" in css
    assert ".semantic-documents-art{display:none}" in css
