from pathlib import Path


def test_migration_revision_and_tables():
    text = Path("migrations/versions/20260828_0005_shared_data_platform.py").read_text()
    assert 'revision = "20260828_0005"' in text
    assert 'down_revision = "20260827_0004"' in text
    for table in (
        "core_data_sources",
        "core_data_source_versions",
        "core_ingestion_jobs",
        "core_data_quality_results",
        "core_data_audit_events",
    ):
        assert table in text
