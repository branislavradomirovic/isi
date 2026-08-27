from src.public_migration.legacy_snapshot import extract_public_content


def test_snapshot_extracts_content_and_removes_site_chrome():
    html = """
    <html><head><title>Nasleđe - ISI</title><script>alert(1)</script></head>
    <body><header>MENU</header><main><article><h1>Nasleđe</h1><p>Važan sadržaj.</p>
    <a href="/dokumenti/">Dokumenti</a></article></main><footer>FOOTER</footer></body></html>
    """
    result = extract_public_content(html, "https://isi.rs/nasledje/")
    assert "Važan sadržaj" in result["body_text"]
    assert "MENU" not in result["body_text"]
    assert "FOOTER" not in result["body_text"]
    assert "script" not in result["body_html"].lower()
    assert 'href="https://isi.rs/dokumenti/"' in result["body_html"]
    assert result["content_title"] == "Nasleđe"
