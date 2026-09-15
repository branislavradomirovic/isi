from __future__ import annotations

from pathlib import Path
import subprocess


MIGRATION = Path("migrations/versions/20260915_0028_simpa_reference_calculation_suites.py")


def test_0028_exact_chain_simpa_only_tables_constraints_and_backfill():
    text = MIGRATION.read_text()
    assert 'revision = "20260915_0028"' in text
    assert 'down_revision = "20260914_0027"' in text
    assert "ordo_" not in text.casefold()
    for table in ("simpa_methodology_reference_suites", "simpa_methodology_reference_cases"):
        assert table in text
    for value in (
        "SIMPA-REFERENCE-SUITE-v1",
        "reference_evidence_mode",
        "legacy_unknown",
        "legacy_inline",
        "suite_v1",
        "suite_fingerprint",
        "case_fingerprint",
        "result_fingerprint",
        "created_by_membership_id",
        "executed_by_membership_id",
    ):
        assert value in text
    assert "WHEN reference_check_status = 'legacy_unknown' THEN 'legacy_unknown'" in text
    assert "ELSE 'legacy_inline' END" in text


def test_0028_is_the_sole_current_alembic_head():
    heads = subprocess.run(["alembic", "heads"], check=True, capture_output=True, text=True).stdout
    assert "20260915_0028 (head)" in heads
    assert heads.count("(head)") == 1


def test_0028_offline_upgrade_and_downgrade_render():
    upgrade = subprocess.run(
        ["alembic", "upgrade", "20260915_0028", "--sql"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "ADD COLUMN reference_evidence_mode" in upgrade
    assert "CREATE TABLE simpa_methodology_reference_suites" in upgrade
    assert "CREATE TABLE simpa_methodology_reference_cases" in upgrade
    assert "legacy_inline" in upgrade
    downgrade = subprocess.run(
        ["alembic", "downgrade", "20260915_0028:20260914_0027", "--sql"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "DROP TABLE simpa_methodology_reference_cases" in downgrade
    assert "DROP TABLE simpa_methodology_reference_suites" in downgrade
    assert "DROP COLUMN reference_evidence_mode" in downgrade
