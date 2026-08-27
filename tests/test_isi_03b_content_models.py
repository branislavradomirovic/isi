from src.core.database import Base
from src.public_content import models  # noqa: F401


def test_public_content_tables_are_registered():
    expected = {
        "public_pages", "public_page_translations", "public_legacy_sources", "public_media_assets", "public_redirects",
        "public_people", "public_person_translations", "public_activities", "public_activity_translations",
        "public_publications", "public_publication_translations", "public_documents", "public_document_translations",
        "public_programs", "public_program_translations", "public_partners", "public_partner_translations",
    }
    assert expected.issubset(set(Base.metadata.tables))
