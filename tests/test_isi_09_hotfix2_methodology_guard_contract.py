from pathlib import Path


MIGRATION = Path("migrations/versions/20260828_0008_simpa_analytics_ai.py")
GUARD_TEST = Path("tests/test_isi_09_methodology_guard.py")


def test_methodology_guard_checks_semantics_not_prompt_seed_implementation():
    test_text = GUARD_TEST.read_text()
    assert '"INSERT INTO core_ai_prompt_versions"' in test_text
    assert '"CAST(:output_schema AS JSON)"' in test_text
    assert '"op.bulk_insert(methodologies" not in migration' in test_text
    assert '"INSERT INTO simpa_indicator_methodologies" not in migration' in test_text
    assert 'assert "op.bulk_insert(versions" in migration' not in test_text


def test_migration_preserves_safety_and_offline_safe_prompt_seed():
    migration = MIGRATION.read_text()
    assert "simpa_indicator_methodologies" in migration
    assert "op.bulk_insert(prompts" in migration
    assert "simpa.monitoring.synthesis" in migration
    assert "INSERT INTO core_ai_prompt_versions" in migration
    assert "CAST(:output_schema AS JSON)" in migration
    assert "op.bulk_insert(methodologies" not in migration
    assert "INSERT INTO simpa_indicator_methodologies" not in migration
