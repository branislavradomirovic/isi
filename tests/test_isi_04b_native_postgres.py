import os

import pytest
from sqlalchemy import func, select, text

from src.core.database import build_engine, build_session_factory
from src.knowledge.models import KnowledgeDomain, KnowledgeSource
from src.public_content.models import PublicPage
from src.public_content.sections import PublicPageSection


@pytest.mark.skipif(os.getenv("ISI_RUN_NATIVE_DB_TESTS") != "1", reason="native PostgreSQL acceptance test")
def test_native_postgres_has_domain_registry_and_draft_enrichment_without_vector_tables():
    engine=build_engine(); factory=build_session_factory(engine)
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(KnowledgeDomain)) >= 40
        assert session.scalar(select(func.count()).select_from(KnowledgeSource)) == 2
        assert session.scalar(select(func.count()).select_from(PublicPageSection)) >= 15
        assert session.scalar(select(func.count()).select_from(PublicPageSection).where(PublicPageSection.status != "draft")) == 0
        assert session.scalar(select(func.count()).select_from(PublicPage).where(PublicPage.status != "draft")) == 0
        names=set(session.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'")).scalars())
        assert not {name for name in names if "embedding" in name or "vector" in name or "knowledge_chunk" in name}
