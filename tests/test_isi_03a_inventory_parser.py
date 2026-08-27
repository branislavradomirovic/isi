from src.public_migration.legacy_inventory import _PageParser, _canonicalize_url, _classify_asset, _language_for


def test_parser_extracts_metadata_links_assets_and_body():
    parser = _PageParser()
    parser.feed(
        """
        <html lang="sr-Latn"><head><title>Institut za socijalnu inkluziju</title>
        <meta name="description" content="  Znanje   je naš oblik solidarnosti. ">
        <link rel="canonical" href="https://isi.rs/nasledje/" /></head>
        <body><h1>Nasleđe</h1><a href="/tim/">Tim</a>
        <a href="/wp-content/uploads/x.pdf">PDF</a><img src="/img/logo.png" />
        <script>ignore me</script></body></html>
        """
    )
    assert parser.title == "Institut za socijalnu inkluziju"
    assert parser.description.strip().startswith("Znanje")
    assert "/tim/" in parser.links
    assert "/img/logo.png" in parser.assets
    assert "ignore me" not in parser.body_text


def test_url_and_language_contracts():
    assert _canonicalize_url("/tim/", "https://isi.rs/") == "https://isi.rs/tim/"
    assert _canonicalize_url("https://example.com/x", "https://isi.rs/") is None
    assert _classify_asset("/a/report.pdf") == "document"
    assert _classify_asset("/a/photo.webp") == "image"
    assert _language_for("/en/homepage-english/", None) == "en"
    assert _language_for("/nasledje/", "sr-Latn") == "sr-Latn"
