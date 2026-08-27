from __future__ import annotations

from pathlib import Path

from src.public.catalog_service import activity_catalog_from_html, document_catalog_from_html

ROOT = Path(__file__).resolve().parents[1]


def test_activity_catalog_reuses_source_image_and_classifies_semantically():
    html = """
    <div><img src='/media/legacy/conference.jpg'><a href='/conference/'>Međunarodna konferencija o društvenoj pravdi 2026</a><p>23. april 2026. Beograd. Program i javni dijalog.</p></div>
    <div><a href='/workshop/'>Regionalna radionica o socijalnim indikatorima</a><p>15. oktobar 2025. Novi Sad.</p></div>
    """
    rows = activity_catalog_from_html(html)
    assert rows[0].kind == "Konferencija"
    assert rows[0].image_src == "/media/legacy/conference.jpg"
    assert rows[0].location == "Beograd"
    assert rows[1].kind == "Radionica"
    assert rows[1].location == "Novi Sad"


def test_activities_template_always_has_local_visual_fallbacks():
    text = (ROOT / "src/public/templates/activities.html").read_text(encoding="utf-8")
    for asset in ("hero.svg", "conference.svg", "workshop.svg", "dialogue.svg", "training.svg"):
        assert f"/static/img/activities/{asset}" in text
        assert (ROOT / "src/public/static/img/activities" / asset).exists()


def test_document_catalog_has_more_specific_institution_groups():
    html = """
    <a href='https://stat.gov.rs/a.pdf'>Statistički godišnjak 2023</a>
    <a href='https://undp.org/rs/a.pdf'>UNDP Srbija analiza siromaštva 2024</a>
    <a href='/lokalni-plan.pdf'>Vodič za lokalne akcione planove opština 2023</a>
    """
    groups = document_catalog_from_html(html)
    keys = {group.key for group in groups}
    assert {"rzs", "undp", "local"}.issubset(keys)
