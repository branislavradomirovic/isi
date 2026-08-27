from pathlib import Path


def test_snapshot_source_uses_get_only():
    text = Path("src/public_migration/legacy_snapshot.py").read_text()
    assert "client.get" in text
    for forbidden in ("client.post", "client.put", "client.patch", "client.delete"):
        assert forbidden not in text


def test_importer_never_auto_publishes_or_approves_redirects():
    text = Path("src/public_migration/content_importer.py").read_text()
    assert 'status="draft"' in text
    assert '"status": "pending"' in text
    assert '"status": "published"' not in text
    assert '"status": "approved"' not in text
