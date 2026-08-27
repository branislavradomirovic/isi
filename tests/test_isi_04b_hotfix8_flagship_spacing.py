from pathlib import Path

CSS = Path("src/public/static/css/semantic-polish.css")
INDEX = Path("src/public/templates/index.html")


def test_hotfix8_css_marker_and_single_line_contract():
    css = CSS.read_text()
    assert "ISI-04B-HOTFIX-8-FLAGSHIP-LOCKUP-SPACING" in css
    tail = css.split("ISI-04B-HOTFIX-8-FLAGSHIP-LOCKUP-SPACING", 1)[1]
    assert ".semantic-flagship-lockup h2" in tail
    assert "white-space: nowrap" in tail
    assert "word-break: keep-all" in tail
    assert "overflow-wrap: normal" in tail


def test_hotfix8_adds_lockup_breathing_room_without_template_rewrite():
    css = CSS.read_text()
    tail = css.split("ISI-04B-HOTFIX-8-FLAGSHIP-LOCKUP-SPACING", 1)[1]
    assert "padding-right: 10px" in tail
    assert "width: 90px" in tail
    assert "height: 90px" in tail
    index = INDEX.read_text()
    assert "semantic-flagship-lockup" in index
    assert "simpa-mark.svg" in index
    assert "ordo-mark.svg" in index


def test_platform_names_remain_database_driven():
    index = INDEX.read_text()
    assert "{{ platform.title }}" in index
    assert "platform.page_key == 'platform.simpa'" in index
