from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ordo_knowledge_context_is_namespace_locked():
    text = (ROOT / "src/domains/ordo/analytics_service.py").read_text()
    assert 'private_namespace(organization_id, "ORDO")' in text
    assert 'public_namespace("ORDO")' in text
    assert 'public_namespace("ISI")' in text
    assert 'product_code="ORDO"' in text
    assert 'private_namespace(organization_id, "SIMPA")' not in text
    assert 'public_namespace("SIMPA")' not in text
    assert "does not claim semantic retrieval" in text
