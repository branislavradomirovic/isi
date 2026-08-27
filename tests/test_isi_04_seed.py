import json
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from src.core.database import Base
from src.public.platform_seed import seed_platform_pages
from src.public_content.models import PublicPage, PublicPageTranslation


def test_platform_seed_is_idempotent_and_draft_only():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    payload = json.loads(Path("data/public/flagship_platforms.json").read_text())
    with Session(engine) as session:
        seed_platform_pages(session, payload)
        seed_platform_pages(session, payload)
        assert session.scalar(
            select(func.count()).select_from(PublicPage).where(PublicPage.page_type == "platform")
        ) == 2
        assert session.scalar(
            select(func.count())
            .select_from(PublicPageTranslation)
            .join(PublicPage)
            .where(PublicPage.page_type == "platform")
        ) == 4
        assert session.scalar(
            select(func.count())
            .select_from(PublicPage)
            .where(PublicPage.page_type == "platform", PublicPage.status != "draft")
        ) == 0
