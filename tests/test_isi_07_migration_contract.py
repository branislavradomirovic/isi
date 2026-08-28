from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ai_migration_revision_and_pgvector_probe():
    text = (ROOT / "migrations/versions/20260828_0006_shared_ai_foundation.py").read_text()
    assert 'revision = "20260828_0006"' in text
    assert 'down_revision = "20260828_0005"' in text
    assert "pg_extension" in text
    assert "CREATE EXTENSION" not in text
    assert "core_ai_embedding_vectors" in text
