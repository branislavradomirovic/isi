from pathlib import Path


def test_simpa_ai_uses_shared_gateway_and_local_sensitive_policy():
    service = Path("src/domains/simpa/analytics_service.py").read_text()
    assert "create_ai_job" in service
    assert 'product_code="SIMPA"' in service
    assert 'prompt_key="simpa.monitoring.synthesis"' in service
    assert 'policy_key="simpa-sensitive-local" if sensitivity == "sensitive" else "shared-local-only"' in service
    assert "ollama" not in service.lower()


def test_structured_prompt_requires_human_review():
    migration = Path("migrations/versions/20260828_0008_simpa_analytics_ai.py").read_text()
    assert '"human_review_required"' in migration
    assert "human_review_required must be true" in migration
    assert "Do not diagnose people" in migration
