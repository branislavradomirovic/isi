from pathlib import Path


def test_computation_is_guarded_by_validated_methodology():
    text = Path("src/domains/simpa/analytics_service.py").read_text()
    assert 'indicator.methodology_status != "validated"' in text
    assert 'raise SimpaAnalyticsError("methodology_not_validated")' in text
    assert 'SimpaIndicatorMethodology.status == "validated"' in text
    assert 'row.payload["quality_status"] == "validated"' in text
    assert "revalidate_analytics_run" in text
    assert "source_observation_ids=[]" in text


def test_no_validated_methodology_is_seeded_by_migration():
    migration = Path("migrations/versions/20260828_0008_simpa_analytics_ai.py").read_text()
    assert "simpa_indicator_methodologies" in migration
    assert "op.bulk_insert(prompts" in migration
    assert "simpa.monitoring.synthesis" in migration
    assert "INSERT INTO core_ai_prompt_versions" in migration
    assert "CAST(:output_schema AS JSON)" in migration
    assert "op.bulk_insert(methodologies" not in migration
    assert "INSERT INTO simpa_indicator_methodologies" not in migration
