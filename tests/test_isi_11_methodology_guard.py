from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_indicator_computation_requires_validated_methodology_and_observation():
    text = (ROOT / "src/domains/ordo/analytics_service.py").read_text()
    assert 'indicator.methodology_status != "validated"' in text
    assert 'raise OrdoAnalyticsError("methodology_not_validated")' in text
    assert 'OrdoIndicatorMethodology.status == "validated"' in text
    assert 'OrdoIndicatorObservation.quality_status == "validated"' in text


def test_migration_does_not_seed_validated_ordo_methodologies():
    text = (ROOT / "migrations/versions/20260828_0010_ordo_analytics_ai.py").read_text()
    assert "ordo_indicator_methodologies" in text
    assert "op.bulk_insert(prompts" in text
    assert "CAST(:output_schema AS JSON)" in text
    assert "op.bulk_insert(methodologies" not in text
    assert "INSERT INTO ordo_indicator_methodologies" not in text
