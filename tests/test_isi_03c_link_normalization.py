from src.public_migration.media_redirect_validation import rewrite_internal_url


def maps():
    return {
        "asset_by_url": {"https://isi.rs/wp-content/a.pdf": "/media/legacy/aa/hash.pdf"},
        "asset_by_path": {"/wp-content/a.pdf": "/media/legacy/aa/hash.pdf"},
        "canonical_routes": {"/biblioteka/": "/biblioteka/", "/": "/"},
        "route_by_source_url": {"https://isi.rs/biblioteka": "/biblioteka/"},
        "route_by_legacy_locale": {("/biblioteka", "sr-Latn"): "/biblioteka/"},
    }


def test_rewrite_media_and_alias_page_links():
    media = rewrite_internal_url("https://isi.rs/wp-content/a.pdf", locale="sr-Latn", maps=maps())
    page = rewrite_internal_url("https://isi.rs/biblioteka", locale="sr-Latn", maps=maps())
    assert media.kind == "media" and media.value == "/media/legacy/aa/hash.pdf"
    assert page.kind == "page" and page.value == "/biblioteka/"


def test_unmapped_same_site_link_is_blocking_but_external_is_preserved():
    internal = rewrite_internal_url("/missing/", locale="sr-Latn", maps=maps())
    external = rewrite_internal_url("https://example.org/report", locale="sr-Latn", maps=maps())
    assert internal.kind == "unresolved"
    assert external.kind == "external"
    assert external.value == "https://example.org/report"
