from pathlib import Path


def test_simpa_migration_contract():
    text = Path("migrations/versions/20260828_0007_simpa_domain_foundation.py").read_text()
    assert 'revision = "20260828_0007"' in text
    assert 'down_revision = "20260828_0006"' in text
    for table in [
        "simpa_dimensions", "simpa_source_types", "simpa_indicator_definitions",
        "simpa_local_system_profiles", "simpa_local_actors", "simpa_monitoring_cycles",
        "simpa_data_mappings", "simpa_indicator_observations",
    ]:
        assert table in text
    assert '"methodology_status": "conceptual"' in text
    assert "core_data_sources.id" in text
    assert "core_data_source_versions.id" in text
