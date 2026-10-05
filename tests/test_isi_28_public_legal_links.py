"""Published legal content follows the existing CMS public-read boundary."""

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.api.dependencies import get_db
from src.core.config import Settings, get_settings
from src.core.database import Base
from src.public_content.models import PublicPage, PublicPageTranslation


@pytest.fixture
def portal():
    engine = create_engine(
        "sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    def add(key, status, translations, *, page_type="legal", navigation=False):
        with factory() as db:
            page = PublicPage(page_key=key, page_type=page_type, status=status, is_navigation=navigation)
            db.add(page)
            db.flush()
            for locale, route, title in translations:
                db.add(PublicPageTranslation(
                    page_id=page.id, locale=locale, route_path=route, title=title,
                    body_html="<p>Synthetic acceptance content.</p>", body_text="Synthetic acceptance content.",
                    seo_title=title, meta_description=title,
                ))
            db.commit()

    add("home", "published", [("sr-Latn", "/", "ISI"), ("en", "/en/", "ISI")], page_type="home")

    def db_override():
        with factory() as db:
            yield db

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = db_override
    # Production must still reject drafts even if the preview setting is accidentally enabled.
    app.dependency_overrides[get_settings] = lambda: Settings(
        isi_env="production", public_preview_drafts=True, public_base_url="https://isi.example",
        app_base_url="https://isi.example/app/",
    )
    client = TestClient(app)
    try:
        yield client, add
    finally:
        client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        engine.dispose()


def test_published_legal_routes_are_localized_and_in_sitemap_without_primary_navigation(portal):
    client, add = portal
    add("legal.terms", "published", [
        ("sr-Latn", "/uslovi-koriscenja/", "Uslovi korišćenja"),
        ("en", "/en/terms/", "Terms of Use"),
    ])
    add("legal.privacy", "published", [("sr-Latn", "/privatnost/", "Obaveštenje o privatnosti")])
    for home, expected, absent in [
        ("/", {"/uslovi-koriscenja/", "/privatnost/"}, {"/en/terms/"}),
        ("/en/", {"/en/terms/"}, {"/uslovi-koriscenja/", "/privatnost/"}),
    ]:
        response = client.get(home)
        assert response.status_code == 200
        footer = BeautifulSoup(response.text, "html.parser").find("footer")
        links = {a["href"] for a in footer.find_all("a", href=True)}
        assert expected <= links and not absent & links
        assert "https://isi.example/app/?help=public" in links
        for route in expected:
            assert client.get(route).status_code == 200
    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    for route in ["/uslovi-koriscenja/", "/privatnost/", "/en/terms/"]:
        assert f"<loc>https://isi.example{route}</loc>" in sitemap.text
    assert "Pravne informacije" in client.get("/uslovi-koriscenja/").text
    terms = BeautifulSoup(client.get("/en/terms/").text, "html.parser")
    assert "Legal information" in terms.get_text()
    assert terms.find("link", rel="canonical")["href"] == "https://isi.example/en/terms/"
    assert terms.find("link", hreflang="sr-Latn")["href"] == "https://isi.example/uslovi-koriscenja/"
    assert "Disallow: /api/" in client.get("/robots.txt").text
    assert client.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("state", ["draft", "archived"])
def test_unpublished_legal_content_never_leaks_through_footer_sitemap_or_route(portal, state):
    client, add = portal
    add("legal.privacy", state, [
        ("sr-Latn", "/privatnost/", "UNPUBLISHED_LEGAL_CANARY"),
        ("en", "/en/privacy/", "UNPUBLISHED_LEGAL_CANARY"),
    ], navigation=True)
    for route in ["/", "/en/", "/sitemap.xml"]:
        response = client.get(route)
        assert response.status_code == 200
        assert "UNPUBLISHED_LEGAL_CANARY" not in response.text
        assert "/privatnost/" not in response.text and "/en/privacy/" not in response.text
    for route in ["/privatnost/", "/en/privacy/"]:
        assert client.get(route).status_code == 404


def test_missing_legal_pages_and_unrelated_published_content_add_no_footer_links(portal):
    client, add = portal
    add("article", "published", [("sr-Latn", "/clanak/", "Article")], page_type="standard")
    response = client.get("/")
    assert response.status_code == 200
    footer = BeautifulSoup(response.text, "html.parser").find("footer")
    assert footer.find("a", href="/clanak/") is None
    assert client.get("/privatnost/").status_code == 404


def test_legal_page_in_primary_navigation_is_not_duplicated_in_sitemap(portal):
    client, add = portal
    add("legal.terms", "published", [("sr-Latn", "/uslovi/", "Uslovi")], navigation=True)
    assert client.get("/sitemap.xml").text.count("<loc>https://isi.example/uslovi/</loc>") == 1
