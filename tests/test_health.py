from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.api.dependencies import get_db
from src.core.config import Settings, get_settings
from src.core.database import Base
from src.public_content.models import PublicPage, PublicPageTranslation

client = TestClient(app)


def test_health_endpoint_contract():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "isi-api",
        "phase": "foundation",
    }


def test_public_home_hides_draft_content_by_default():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with factory() as session:
        page = PublicPage(page_key="home", page_type="home", status="draft")
        session.add(page)
        session.flush()
        session.add(
            PublicPageTranslation(
                page_id=page.id,
                locale="sr-Latn",
                route_path="/",
                title="Institut za socijalnu inkluziju",
                summary="Draft home",
                body_html="<p>Draft home</p>",
                body_text="Draft home",
                seo_title="ISI",
                meta_description="ISI",
            )
        )
        session.commit()

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: Settings(
        isi_env="development",
        public_preview_drafts=False,
    )
    try:
        response = TestClient(app).get("/")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
