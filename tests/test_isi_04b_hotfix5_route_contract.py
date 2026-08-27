from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_routes_register_semantic_globals_and_activity_renderer():
    text = (ROOT / "src/public/routes.py").read_text(encoding="utf-8")
    assert "templates.env.globals.update" in text
    assert "semantic_icon=semantic_icon" in text
    assert "document_icon=document_icon" in text
    assert "activity_icon=activity_icon" in text
    assert "activity_catalog_from_html" in text
    assert 'name="activities.html"' in text


def test_base_loads_semantic_polish_after_approved_design():
    text = (ROOT / "src/public/templates/base.html").read_text(encoding="utf-8")
    approved = text.index("/static/css/approved-design.css")
    semantic = text.index("/static/css/semantic-polish.css")
    assert semantic > approved
