from pathlib import Path


def test_migration_revision_and_scope_contract():
    text = Path("migrations/versions/20260827_0004_domain_knowledge_public_sections.py").read_text()
    assert 'revision = "20260827_0004"' in text
    assert 'down_revision = "20260827_0003"' in text
    for table in ["knowledge_domains", "knowledge_sources", "knowledge_source_domains", "public_page_sections", "public_page_section_translations", "public_page_section_items", "public_page_section_item_translations"]:
        assert f'"{table}"' in text
    lowered = text.lower()
    assert "embedding" not in lowered
    assert "vector" not in lowered
    assert "knowledge_chunks" not in lowered
