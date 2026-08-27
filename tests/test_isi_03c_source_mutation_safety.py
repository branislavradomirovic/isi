from pathlib import Path


def test_legacy_network_path_is_read_only_get_only():
    text = Path("src/public_migration/media_redirect_validation.py").read_text().lower()
    assert 'client.stream("get"' in text
    for forbidden in ('.post(', '.put(', '.patch(', '.delete('):
        assert forbidden not in text
    assert "wp-admin" not in text


def test_media_storage_is_gitignored():
    text = Path(".gitignore").read_text()
    assert "var/media/" in text
