from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
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


def _seed(factory):
    with factory() as session:
        home = PublicPage(page_key="home", page_type="home", status="draft")
        simpa = PublicPage(page_key="platform.simpa", page_type="platform", status="draft", is_navigation=True, navigation_order=5)
        ordo = PublicPage(page_key="platform.ordo", page_type="platform", status="draft", is_navigation=True, navigation_order=6)
        session.add_all([home, simpa, ordo]); session.flush()
        session.add_all([
            PublicPageTranslation(page_id=home.id, locale="sr-Latn", route_path="/", title="Institut za socijalnu inkluziju", summary="Institucionalni sažetak", body_html="<p>Nasleđeni sadržaj.</p>", body_text="Nasleđeni sadržaj", seo_title="ISI", meta_description="ISI"),
            PublicPageTranslation(page_id=home.id, locale="en", route_path="/en/homepage-english/", title="Institute for Social Inclusion", summary="Institutional summary", body_html="<p>Legacy content.</p>", body_text="Legacy content", seo_title="ISI", meta_description="ISI"),
            PublicPageTranslation(page_id=simpa.id, locale="sr-Latn", route_path="/simpa/", title="SIMPA", summary="Podaci. Znanje. Odluke. Rezultati.", body_html="<p>SIMPA content.</p>", body_text="SIMPA content", seo_title="SIMPA", meta_description="SIMPA"),
            PublicPageTranslation(page_id=simpa.id, locale="en", route_path="/en/simpa/", title="SIMPA", summary="Data. Knowledge. Decisions. Results.", body_html="<p>SIMPA content.</p>", body_text="SIMPA content", seo_title="SIMPA", meta_description="SIMPA"),
            PublicPageTranslation(page_id=ordo.id, locale="sr-Latn", route_path="/ordo/", title="ORDO", summary="Podaci. Znanje. Razvoj. Destinacija.", body_html="<p>ORDO content.</p>", body_text="ORDO content", seo_title="ORDO", meta_description="ORDO"),
            PublicPageTranslation(page_id=ordo.id, locale="en", route_path="/en/ordo/", title="ORDO", summary="Data. Knowledge. Development. Destination.", body_html="<p>ORDO content.</p>", body_text="ORDO content", seo_title="ORDO", meta_description="ORDO"),
        ])
        session.commit()


def test_public_routes_render_db_content_in_local_preview():
    factory = _factory(); _seed(factory)
    def override_db():
        with factory() as session:
            yield session
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: Settings(isi_env="development", public_preview_drafts=True)
    try:
        client = TestClient(app)
        home = client.get("/")
        assert home.status_code == 200
        assert "Institut za socijalnu inkluziju" in home.text
        assert "SIMPA" in home.text and "ORDO" in home.text
        assert "LOCAL PREVIEW" in home.text
        assert client.get("/simpa/").status_code == 200
        assert client.get("/ordo/").status_code == 200
        assert client.get("/en/").status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_production_never_exposes_drafts_even_if_preview_flag_true():
    factory = _factory(); _seed(factory)
    def override_db():
        with factory() as session:
            yield session
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: Settings(isi_env="production", public_preview_drafts=True)
    try:
        assert TestClient(app).get("/").status_code == 404
    finally:
        app.dependency_overrides.clear()
