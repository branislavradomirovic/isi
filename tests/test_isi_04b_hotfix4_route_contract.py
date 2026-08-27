from __future__ import annotations

from pathlib import Path


def test_approved_routes_have_specialized_templates_and_home_previews():
    text = Path("src/public/routes.py").read_text()
    assert 'name="documents.html"' in text
    assert 'name="library.html"' in text
    assert 'name="inclusive_development.html"' in text
    assert 'context["home_document_groups"]' in text
    assert 'context["home_library_entries"]' in text


def test_public_brand_hierarchy_is_isi_then_simpa_and_ordo():
    home = Path("src/public/templates/index.html").read_text()
    header = Path("src/public/templates/partials/header.html").read_text()
    assert "ISI –" in home
    assert "SIMPA" in home and "ORDO" in home
    assert "approved-brand-logo" in header
