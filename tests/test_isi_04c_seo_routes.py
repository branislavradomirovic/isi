from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.api.dependencies import get_db
from src.core.config import Settings, get_settings
from src.core.database import Base
from src.public_content.models import PublicPage, PublicPageTranslation


def _factory():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _seed(factory, *, status: str):
    with factory() as session:
        home = PublicPage(page_key="home", page_type="home", status=status, is_navigation=True, navigation_order=1)
        simpa = PublicPage(page_key="platform.simpa", page_type="platform", status=status, is_navigation=True, navigation_order=5)
        session.add_all([home, simpa]); session.flush()
        session.add_all([
            PublicPageTranslation(page_id=home.id, locale="sr-Latn", route_path="/", title="Institut za socijalnu inkluziju", summary="Institucionalni sažetak", body_html="<p>Home</p>", body_text="Home", seo_title="ISI", meta_description="ISI opis"),
            PublicPageTranslation(page_id=home.id, locale="en", route_path="/en/", title="Institute for Social Inclusion", summary="Institutional summary", body_html="<p>Home</p>", body_text="Home", seo_title="ISI", meta_description="ISI description"),
            PublicPageTranslation(page_id=simpa.id, locale="sr-Latn", route_path="/simpa/", title="SIMPA", summary="SIMPA", body_html="<p>SIMPA</p>", body_text="SIMPA", seo_title="SIMPA", meta_description="SIMPA opis"),
            PublicPageTranslation(page_id=simpa.id, locale="en", route_path="/en/simpa/", title="SIMPA", summary="SIMPA", body_html="<p>SIMPA</p>", body_text="SIMPA", seo_title="SIMPA", meta_description="SIMPA description"),
        ])
        session.commit()


def _client(factory, settings):
    def override_db():
        with factory() as session:
            yield session
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def test_readiness_endpoints_and_preview_seo_contract():
    factory = _factory(); _seed(factory, status="draft")
    client = _client(factory, Settings(isi_env="development", public_preview_drafts=True, public_base_url="https://isi.rs"))
    try:
        robots = client.get("/robots.txt")
        assert robots.status_code == 200
        assert "Disallow: /" in robots.text
        sitemap = client.get("/sitemap.xml")
        assert sitemap.status_code == 200
        assert "<urlset" in sitemap.text
        assert "https://isi.rs/simpa/" not in sitemap.text  # draft content must not leak
        manifest = client.get("/site.webmanifest")
        assert manifest.status_code == 200
        assert manifest.headers["content-type"].startswith("application/manifest+json")
        assert '"start_url":"/"' in manifest.text
        favicon = client.get("/favicon.ico")
        assert favicon.status_code == 200
        assert favicon.headers["content-type"].startswith("image/svg+xml")
        assert b"<svg" in favicon.content
        home = client.get("/")
        assert home.status_code == 200
        assert '<meta name="robots" content="noindex,nofollow">' in home.text
        assert 'property="og:title"' in home.text
        assert 'name="twitter:card"' in home.text
        assert 'hreflang="x-default"' in home.text
        assert '<link rel="icon" href="/static/img/brand/isi-logo-transparent.svg" type="image/svg+xml">' in home.text
        assert '<link rel="manifest" href="/site.webmanifest">' in home.text
        assert 'aria-current="page"' in home.text
    finally:
        app.dependency_overrides.clear()


def test_production_sitemap_contains_published_routes_only():
    factory = _factory(); _seed(factory, status="published")
    client = _client(factory, Settings(isi_env="production", public_preview_drafts=False, public_base_url="https://isi.rs"))
    try:
        robots = client.get("/robots.txt")
        assert "Allow: /" in robots.text
        assert "https://isi.rs/sitemap.xml" in robots.text
        sitemap = client.get("/sitemap.xml")
        assert "https://isi.rs/" in sitemap.text
        assert "https://isi.rs/simpa/" in sitemap.text
        assert "https://isi.rs/en/" in sitemap.text
        home = client.get("/")
        assert 'content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"' in home.text
    finally:
        app.dependency_overrides.clear()


def test_public_404_is_html_but_api_404_remains_json():
    factory = _factory()
    client = _client(factory, Settings(isi_env="development", public_preview_drafts=True))
    try:
        public_missing = client.get("/definitely-missing/")
        assert public_missing.status_code == 404
        assert "text/html" in public_missing.headers.get("content-type", "")
        assert "404" in public_missing.text
        api_missing = client.get("/api/v1/definitely-missing")
        assert api_missing.status_code == 404
        assert "application/json" in api_missing.headers.get("content-type", "")
    finally:
        app.dependency_overrides.clear()
