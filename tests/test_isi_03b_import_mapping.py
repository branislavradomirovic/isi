from src.public_migration.content_importer import navigation_meta, page_key_for, page_type_for


def test_home_translations_share_logical_page():
    assert page_key_for("/", "sr-Latn") == "home"
    assert page_key_for("/en/homepage-english/", "en") == "home"


def test_known_legacy_routes_have_explicit_page_types():
    assert page_type_for("/") == "home"
    assert page_type_for("/en/homepage-english/") == "home"
    assert page_type_for("/tim/") == "team_index"
    assert page_type_for("/aktivnosti/") == "activity_index"
    assert page_type_for("/dokumenti/") == "document_index"
    assert page_type_for("/biblioteka") == "library_index"
    assert page_type_for("/inkluzivni-razvoj/") == "program"
    assert page_type_for("/nasledje/") == "heritage"


def test_navigation_metadata_is_deterministic():
    assert navigation_meta("/tim/") == (True, 10)
    assert navigation_meta("/nasledje/") == (True, 60)
    assert navigation_meta("/some-page/") == (False, 1000)
