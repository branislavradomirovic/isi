from __future__ import annotations

from pathlib import Path
import subprocess


MIGRATION = Path("migrations/versions/20260915_0029_simpa_statistical_model_contracts.py")


def test_0029_exact_chain_simpa_only_tables_constraints_and_foreign_keys():
    text = MIGRATION.read_text()
    assert 'revision = "20260915_0029"' in text
    assert 'down_revision = "20260915_0028"' in text
    assert "ordo_" not in text.casefold()
    for value in (
        "simpa_statistical_model_contracts",
        "simpa_statistical_model_results",
        "SIMPA-STATISTICAL-MODEL-CONTRACT-v1",
        "SIMPA-STATISTICAL-MODEL-v1",
        "target_methodology_contract_fingerprint",
        "statistical_contract_fingerprint",
        "input_content_fingerprint",
        "production_eligible",
        "uq_simpa_statistical_result_run_contract",
        'ondelete="RESTRICT"',
    ):
        assert value in text
    for family in ("ols", "poisson_glm", "binomial_logit", "fractional_logit"):
        assert family in text


def test_0029_is_the_sole_alembic_head():
    heads = subprocess.run(["alembic", "heads"], check=True, capture_output=True, text=True).stdout
    assert "20260915_0029 (head)" in heads
    assert heads.count("(head)") == 1


def test_0029_offline_upgrade_and_downgrade_render():
    upgrade = subprocess.run(
        ["alembic", "upgrade", "20260915_0029", "--sql"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "CREATE TABLE simpa_statistical_model_contracts" in upgrade
    assert "CREATE TABLE simpa_statistical_model_results" in upgrade
    assert "SIMPA-STATISTICAL-MODEL-CONTRACT-v1" in upgrade
    downgrade = subprocess.run(
        ["alembic", "downgrade", "20260915_0029:20260915_0028", "--sql"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "DROP TABLE simpa_statistical_model_results" in downgrade
    assert "DROP TABLE simpa_statistical_model_contracts" in downgrade
