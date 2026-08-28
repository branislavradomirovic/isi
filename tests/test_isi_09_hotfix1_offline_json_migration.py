from pathlib import Path


MIGRATION = Path("migrations/versions/20260828_0008_simpa_analytics_ai.py")


def test_prompt_version_seed_is_offline_json_safe():
    text = MIGRATION.read_text()
    assert 'CAST(:output_schema AS JSON)' in text
    assert 'json.dumps(schema, sort_keys=True)' in text
    assert 'sa.bindparam("output_schema"' in text
    assert 'type_=sa.Text()' in text
    assert 'op.bulk_insert(versions' not in text


def test_prompt_seed_semantics_are_preserved():
    text = MIGRATION.read_text()
    assert 'simpa.monitoring.synthesis' in text
    assert 'human_review_required must be true' in text
    assert 'Evidence-bounded decision support requiring human review' in text
    assert 'op.bulk_insert(prompts' in text
