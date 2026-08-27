import os

import pytest
from sqlalchemy import func, select

from src.core.database import build_engine, build_session_factory
from src.public_content.models import PublicPage, PublicPageTranslation


@pytest.mark.skipif(os.getenv("ISI_RUN_NATIVE_DB_TESTS") != "1", reason="native PostgreSQL acceptance test")
def test_native_postgres_has_flagship_platform_drafts():
    factory = build_session_factory(build_engine())
    with factory() as session:
        pages = session.scalars(select(PublicPage).where(PublicPage.page_key.in_(["platform.simpa", "platform.ordo"]))).all()
        assert {page.page_key for page in pages} == {"platform.simpa", "platform.ordo"}
        assert all(page.status == "draft" for page in pages)
        count = session.scalar(select(func.count()).select_from(PublicPageTranslation).join(PublicPage).where(PublicPage.page_type == "platform"))
        assert count >= 4
