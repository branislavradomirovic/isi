import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.database import Base
import src.platform.models  # noqa: F401
from src.public.section_seed import seed_public_sections
from src.public.section_service import list_page_sections
from src.public_content.models import PublicPage, PublicPageTranslation


def test_section_service_respects_draft_preview_and_locale():
    engine=create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        for key, route in [("home","/"),("platform.simpa","/simpa/"),("platform.ordo","/ordo/")]:
            page=PublicPage(page_key=key,page_type="home" if key=="home" else "platform",status="draft")
            session.add(page); session.flush()
            session.add(PublicPageTranslation(page_id=page.id,locale="sr-Latn",route_path=route,title=key,summary="x",body_html="<p>x</p>",body_text="x",seo_title=key,meta_description="x"))
        session.commit()
        seed_public_sections(session,json.loads(Path("data/public/domain_sections.json").read_text()))
        simpa=session.query(PublicPage).filter_by(page_key="platform.simpa").one()
        assert list_page_sections(session,page_id=simpa.id,locale="sr-Latn",include_drafts=False) == []
        views=list_page_sections(session,page_id=simpa.id,locale="sr-Latn",include_drafts=True)
        assert len(views) >= 6
        assert any(v.key == "responsible_data" for v in views)
        assert sum(len(v.items) for v in views) >= 35
