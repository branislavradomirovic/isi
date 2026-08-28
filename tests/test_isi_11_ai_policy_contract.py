from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ordo_ai_uses_shared_gateway_and_ordo_local_policy():
    service = (ROOT / "src/domains/ordo/analytics_service.py").read_text()
    assert "create_ai_job" in service
    assert 'product_code="ORDO"' in service
    assert 'prompt_key="ordo.decision_support.synthesis"' in service
    assert 'policy_key="ordo-decision-support-local"' in service
    assert 'sensitivity="internal"' in service
    assert "ollama" not in service.lower()


def test_policy_and_prompt_force_human_review_and_no_fake_prediction():
    migration = (ROOT / "migrations/versions/20260828_0010_ordo_analytics_ai.py").read_text()
    assert '"policy_key": "ordo-decision-support-local"' in migration
    assert '"provider_policy": "local_only"' in migration
    assert '"allow_external": False' in migration
    assert '"require_human_review": True' in migration
    assert "forecast_performed must be false" in migration
    assert "human_review_required must be true" in migration
    assert "do not make the development decision" in migration
