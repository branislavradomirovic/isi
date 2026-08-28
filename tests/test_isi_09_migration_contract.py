from pathlib import Path


def test_migration_chain_and_tables():
    text = Path("migrations/versions/20260828_0008_simpa_analytics_ai.py").read_text()
    assert 'revision = "20260828_0008"' in text
    assert 'down_revision = "20260828_0007"' in text
    for table in ("simpa_indicator_methodologies", "simpa_analytics_runs", "simpa_indicator_results", "simpa_ai_syntheses"):
        assert table in text
    assert "simpa.monitoring.synthesis" in text
