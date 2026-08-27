from pathlib import Path


def test_public_website_contract_files_exist():
    required = [
        "src/public/content_service.py",
        "src/public/routes.py",
        "src/public/templates/base.html",
        "src/public/templates/index.html",
        "src/public/templates/page.html",
        "src/public/templates/platform.html",
        "src/public/static/css/site.css",
        "src/public/static/js/site.js",
        "data/public/flagship_platforms.json",
        "tools/seed_public_platform_pages.py",
    ]
    for path in required:
        assert Path(path).is_file(), path


def test_design_does_not_reintroduce_cosmos_or_public_streamlit():
    text = "\n".join(Path(path).read_text() for path in [
        "src/public/templates/base.html",
        "src/public/templates/index.html",
        "src/public/templates/platform.html",
        "data/public/flagship_platforms.json",
    ])
    assert "COSMOS" not in text
    assert "streamlit" not in text.lower()


def test_templates_use_database_content_without_replaying_retired_home_body():
    index = Path("src/public/templates/index.html").read_text()
    platform = Path("src/public/templates/platform.html").read_text()
    # The home shell still consumes migrated database metadata, but deliberately does
    # not replay the raw legacy home body because it contains retired initiatives.
    assert "{{ page.excerpt }}" in index
    assert "{{ page.body_html | safe }}" not in index
    assert "ANCSEE" not in index
    assert "WBSIB" not in index
    # Domain platform long-form content remains database-driven.
    assert "{{ page.body_html | safe }}" in platform
