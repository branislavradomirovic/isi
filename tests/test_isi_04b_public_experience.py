from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.public.catalog_service import document_catalog_from_html, library_catalog_from_html


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "src/public/templates"
STATIC = ROOT / "src/public/static"


def test_home_removes_retired_initiatives_and_uses_flagship_logos():
    text = (TEMPLATES / "index.html").read_text(encoding="utf-8")
    assert "ANCSEE" not in text
    assert "WBSIB" not in text
    assert "Academic Network for Cooperation" not in text
    assert "Western Balkan Social Inclusion Barometer" not in text
    assert "/static/img/simpa-mark.svg" in text
    assert "/static/img/ordo-mark.svg" in text


def test_dedicated_catalog_templates_and_inclusive_page_exist():
    for name in ("documents.html", "library.html", "inclusive_development.html"):
        assert (TEMPLATES / name).is_file(), name
    routes = (ROOT / "src/public/routes.py").read_text(encoding="utf-8")
    assert 'page.page_type == "document_index"' in routes
    assert 'page.page_type == "library_index"' in routes
    assert 'page.page_key == "legacy.inkluzivni-razvoj"' in routes


def test_document_catalog_preserves_source_links_and_groups_institutions():
    html = """
    <div>
      <a href="https://www.un.org/sustainabledevelopment/">Agenda 2030 za održivi razvoj (SDGs)</a>
      <a href="https://commission.europa.eu/example">Evropski stub socijalnih prava 2017</a>
      <a href="https://www.srbija.gov.rs/example">Strategija za socijalno uključivanje u Republici Srbiji 2022</a>
      <a href="https://www.unicef.org/example">UNICEF – Stanje dece u svetu 2023</a>
    </div>
    """
    groups = document_catalog_from_html(html)
    by_key = {group.key: group for group in groups}
    assert {"un", "eu", "serbia", "unicef"}.issubset(by_key)
    assert by_key["un"].items[0].href == "https://www.un.org/sustainabledevelopment/"
    assert by_key["eu"].items[0].year == "2017"
    assert by_key["serbia"].items[0].document_type == "Strategija"
    assert by_key["unicef"].items[0].title.startswith("UNICEF")


def test_catalog_does_not_invent_links_from_plain_text():
    html = "<h2>Agenda 2030 za održivi razvoj</h2><p>Tekst bez linka.</p>"
    assert document_catalog_from_html(html) == []
    assert library_catalog_from_html(html) == []


def test_library_catalog_preserves_nearby_image_and_collection():
    html = """
    <article><a href="/media/legacy/publikacija.pdf"><img src="/media/legacy/cover.jpg">Siromaštvo i socijalna isključenost u Srbiji 2023</a></article>
    <article><a href="/media/legacy/rad.pdf">Mladi i tržište rada u Srbiji 2024</a></article>
    """
    entries = library_catalog_from_html(html)
    assert len(entries) == 2
    assert entries[0].image_src == "/media/legacy/cover.jpg"
    assert entries[0].collection == "Socijalna inkluzija"
    assert entries[1].collection == "Zapošljavanje i rad"
    assert entries[1].year == "2024"


def test_public_visual_assets_and_styles_are_present():
    for path in (
        STATIC / "img/icons.svg",
        STATIC / "img/simpa-mark.svg",
        STATIC / "img/ordo-mark.svg",
        STATIC / "css/experience.css",
    ):
        assert path.is_file(), path
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert "/static/css/experience.css" in base


def test_all_public_templates_parse_with_jinja():
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
    for path in TEMPLATES.rglob("*.html"):
        env.parse(path.read_text(encoding="utf-8"))
