from pathlib import Path


def test_inventory_tool_is_read_only_source_crawler():
    text = Path("src/public_migration/legacy_inventory.py").read_text()
    assert "httpx.Client" in text
    assert "client.get" in text
    for forbidden in ("client.post", "client.put", "client.patch", "client.delete"):
        assert forbidden not in text
    for forbidden in ("DROP DATABASE", "CREATE DATABASE", "alembic upgrade", "docker compose up"):
        assert forbidden not in text


def test_isi03a_does_not_define_public_content_database_models_yet():
    assert not Path("src/public_migration/models.py").exists()
