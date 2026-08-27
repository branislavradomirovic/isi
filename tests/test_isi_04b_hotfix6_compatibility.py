from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "src" / "public" / "templates"


def test_header_preserves_hotfix4_contract_and_uses_hotfix5_transparent_logo():
    header = (TEMPLATES / "partials" / "header.html").read_text(encoding="utf-8")
    assert "approved-brand" in header
    assert "approved-brand-logo" in header
    assert "/static/img/brand/isi-logo-transparent.svg" in header
    assert "/static/img/brand/isi-logo.svg" in header


def test_domain_item_keeps_approved_and_semantic_classes():
    partial = (TEMPLATES / "partials" / "domain_sections.html").read_text(encoding="utf-8")
    assert "approved-domain-item semantic-domain-item" in partial
    assert "semantic_icon(section.key" in partial


def test_hotfix6_does_not_revert_semantic_polish():
    header = (TEMPLATES / "partials" / "header.html").read_text(encoding="utf-8")
    partial = (TEMPLATES / "partials" / "domain_sections.html").read_text(encoding="utf-8")
    assert "semantic-platform-nav" in header
    assert "semantic-domain-stack" in partial
