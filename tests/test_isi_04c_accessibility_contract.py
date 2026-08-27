from pathlib import Path


def test_header_accessibility_contract():
    text = Path("src/public/templates/partials/header.html").read_text()
    assert 'aria-controls="primary-nav"' in text
    assert 'aria-expanded="false"' in text
    assert 'aria-current="page"' in text
    assert 'aria-label=' in text


def test_activity_search_and_meaningful_images_are_accessible():
    text = Path("src/public/templates/activities.html").read_text()
    assert "Pretražite aktivnosti" in text
    assert 'alt="{{ entry.title }}"' in text
    assert 'loading="lazy"' in text
    assert 'decoding="async"' in text


def test_navigation_escape_and_external_link_safety_exist():
    text = Path("src/public/static/js/public-readiness.js").read_text()
    assert "event.key === 'Escape'" in text
    assert "restoreFocus: true" in text
    assert "noopener" in text and "noreferrer" in text


def test_library_and_home_resource_images_use_meaningful_alt_text():
    library = Path("src/public/templates/library.html").read_text()
    home = Path("src/public/templates/index.html").read_text()
    assert 'alt="{{ entry.title }}"' in library
    assert 'alt="{{ entry.title }}"' in home
