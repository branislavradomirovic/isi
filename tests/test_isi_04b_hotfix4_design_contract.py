from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "src" / "public" / "templates"
STATIC = ROOT / "src" / "public" / "static"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def test_approved_templates_compile():
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
    for name in (
        "base.html",
        "index.html",
        "platform.html",
        "documents.html",
        "library.html",
        "inclusive_development.html",
        "partials/header.html",
        "partials/footer.html",
        "partials/domain_sections.html",
    ):
        env.get_template(name)


def test_official_isi_logo_is_installed_from_user_asset():
    manifest = json.loads((ROOT / "data" / "public" / "isi_brand_manifest.json").read_text())
    source = ROOT / manifest["source_path"]
    served = ROOT / manifest["served_path"]
    assert source.exists()
    assert served.exists()
    assert _sha256(source) == manifest["source_sha256"]
    assert _sha256(served) == manifest["served_sha256"]
    if manifest["source_type"] != "pdf":
        assert manifest["source_sha256"] == manifest["served_sha256"]
    assert manifest["policy"].startswith("copied from user-owned assets/ISILogo")


def test_header_and_footer_use_installed_isi_logo():
    header = (TEMPLATES / "partials" / "header.html").read_text()
    footer = (TEMPLATES / "partials" / "footer.html").read_text()
    for text in (header, footer):
        assert "__ISI_LOGO_SRC__" not in text
        assert "/static/img/brand/isi-logo." in text
    assert "approved-brand" in header
    assert "approved-footer-brand" in footer


def test_retired_initiatives_are_out_of_new_public_home_scope():
    home = (TEMPLATES / "index.html").read_text().casefold()
    routes = (ROOT / "src" / "public" / "routes.py").read_text().casefold()
    for token in (
        "ancsee",
        "academic network for cooperation",
        "wbsib",
        "western balkan social inclusion barometer",
    ):
        assert token not in home
    assert "retired_public_tokens" in routes


def test_approved_design_assets_and_brand_marks_exist():
    for rel in (
        "css/approved-design.css",
        "js/approved-design.js",
        "img/icons.svg",
        "img/simpa-mark.svg",
        "img/ordo-mark.svg",
    ):
        assert (STATIC / rel).is_file(), rel
        assert (STATIC / rel).stat().st_size > 100
    css = (STATIC / "css" / "approved-design.css").read_text()
    assert ".approved-home-hero" in css
    assert ".approved-institution-row" in css
    assert ".approved-library-grid" in css
    assert ".approved-inclusive-pillars" in css
    assert ".approved-domain-item" in css


def test_home_uses_real_catalog_previews_not_fabricated_stats():
    home = (TEMPLATES / "index.html").read_text()
    routes = (ROOT / "src" / "public" / "routes.py").read_text()
    assert "home_document_groups" in home
    assert "home_library_entries" in home
    assert "_preview_catalogs" in routes
    # No invented public-impact numbers are hard-coded into the approved homepage.
    for phrase in ("50 institucija", "120 politika", "2.356", "128 dokumenata"):
        assert phrase not in home


def test_domain_sections_do_not_reserve_empty_fixed_height_cards():
    partial = (TEMPLATES / "partials" / "domain_sections.html").read_text()
    css = (STATIC / "css" / "approved-design.css").read_text()
    assert "approved-domain-item" in partial
    assert "min-height:150px" in css
    assert "min-height:300px" not in css
