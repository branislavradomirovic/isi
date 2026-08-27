from pathlib import Path


def test_migration_chain_and_safety_contract():
    path = Path("migrations/versions/20260827_0003_public_content_model.py")
    text = path.read_text()
    assert 'revision = "20260827_0003"' in text
    assert 'down_revision = "20260827_0002"' in text
    for table in (
        "public_pages", "public_page_translations", "public_legacy_sources", "public_media_assets", "public_redirects",
        "public_people", "public_activities", "public_publications", "public_documents", "public_programs", "public_partners",
    ):
        assert table in text
