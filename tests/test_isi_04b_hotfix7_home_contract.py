from pathlib import Path

INDEX = Path("src/public/templates/index.html")


def test_home_keeps_database_excerpt_without_replaying_legacy_body():
    text = INDEX.read_text(encoding="utf-8")
    assert 'data-content-source="database"' in text
    assert 'data-page-excerpt="{{ page.excerpt }}"' in text
    assert "{{ page.excerpt }}" in text
    assert "{{ page.body_html | safe }}" not in text


def test_home_contract_fix_does_not_reintroduce_retired_initiatives():
    text = INDEX.read_text(encoding="utf-8")
    assert "ANCSEE" not in text
    assert "WBSIB" not in text


def test_hotfix7_is_non_visual_and_preserves_semantic_home_shell():
    text = INDEX.read_text(encoding="utf-8")
    assert 'class="semantic-home-hero"' in text
    assert "semantic-system-diagram" in text
    assert "semantic-flagship-section" in text
    assert "/static/img/simpa-mark.svg" in text
    assert "/static/img/ordo-mark.svg" in text
