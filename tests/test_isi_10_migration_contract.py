from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_migration_is_0008_to_0009_and_conceptual_only():
    text = (ROOT / "migrations/versions/20260828_0009_ordo_domain_foundation.py").read_text()
    assert 'revision = "20260828_0009"' in text
    assert 'down_revision = "20260828_0008"' in text
    for token in ("ordo_pillars", "ordo_dimensions", "ordo_assets", "ordo_stakeholders", "ordo_indicator_observations"):
        assert token in text
    assert '"methodology_status": "conceptual"' in text
    assert '"methodology_status": "validated"' not in text
