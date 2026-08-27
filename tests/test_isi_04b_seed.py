import json
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from src.core.database import Base
import src.platform.models  # noqa: F401
from src.knowledge.models import KnowledgeDomain, KnowledgeSource, KnowledgeSourceDomain
from src.knowledge.seed import seed_knowledge_registry
from src.public.section_seed import seed_public_sections
from src.public_content.models import PublicPage, PublicPageTranslation
from src.public_content.sections import PublicPageSection, PublicPageSectionItem


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _pages(session):
    for key, typ in [("home", "home"), ("platform.simpa", "platform"), ("platform.ordo", "platform")]:
        page = PublicPage(page_key=key, page_type=typ, status="draft")
        session.add(page); session.flush()
        session.add(PublicPageTranslation(page_id=page.id, locale="sr-Latn", route_path={"home":"/","platform.simpa":"/simpa/","platform.ordo":"/ordo/"}[key], title=key, summary="x", body_html="<p>x</p>", body_text="x", seo_title=key, meta_description="x"))
    session.commit()


def test_seed_is_idempotent_and_sections_remain_draft():
    domains = json.loads(Path("data/knowledge/domain_registry.json").read_text())
    sources = json.loads(Path("data/knowledge/source_registry.json").read_text())
    sections = json.loads(Path("data/public/domain_sections.json").read_text())
    with _session() as session:
        _pages(session)
        seed_knowledge_registry(session, domains, sources)
        seed_public_sections(session, sections)
        first = (
            session.scalar(select(func.count()).select_from(KnowledgeDomain)),
            session.scalar(select(func.count()).select_from(KnowledgeSource)),
            session.scalar(select(func.count()).select_from(KnowledgeSourceDomain)),
            session.scalar(select(func.count()).select_from(PublicPageSection)),
            session.scalar(select(func.count()).select_from(PublicPageSectionItem)),
        )
        seed_knowledge_registry(session, domains, sources)
        seed_public_sections(session, sections)
        second = (
            session.scalar(select(func.count()).select_from(KnowledgeDomain)),
            session.scalar(select(func.count()).select_from(KnowledgeSource)),
            session.scalar(select(func.count()).select_from(KnowledgeSourceDomain)),
            session.scalar(select(func.count()).select_from(PublicPageSection)),
            session.scalar(select(func.count()).select_from(PublicPageSectionItem)),
        )
        assert first == second
        assert first[0] >= 40 and first[1] == 2 and first[3] >= 15 and first[4] >= 80
        assert session.scalar(select(func.count()).select_from(PublicPageSection).where(PublicPageSection.status != "draft")) == 0
