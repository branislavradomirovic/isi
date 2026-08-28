from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ai_model_tables_are_explicit_and_scoped():
    text = (ROOT / "src/platform/ai/models.py").read_text()
    for table in (
        "core_ai_models",
        "core_ai_prompts",
        "core_ai_prompt_versions",
        "core_ai_policy_profiles",
        "core_ai_jobs",
        "core_ai_job_attempts",
        "core_ai_audit_events",
        "core_ai_embeddings",
    ):
        assert table in text
    assert "organization_id" in text
    assert "workspace_id" in text
    assert "product_code" in text
    assert "request_sha256" in text
    assert "human_review_status" in text
