from __future__ import annotations

from pathlib import Path
import subprocess


MIGRATION = Path("migrations/versions/20260914_0027_simpa_methodology_lifecycle_contract.py")


def test_0027_exact_chain_columns_constraints_and_simpa_only():
    text = MIGRATION.read_text()
    assert 'revision = "20260914_0027"' in text
    assert 'down_revision = "20260914_0026"' in text
    assert "ordo_" not in text.casefold()
    for column in (
        "contract_fingerprint",
        "proposed_by_membership_id",
        "proposed_at",
        "reference_check_status",
        "reference_check_fingerprint",
        "reference_check_detail",
        "retired_by_membership_id",
        "retired_at",
        "retirement_note",
    ):
        assert column in text
    for value in ("draft", "proposed", "validated", "retired", "legacy_unknown"):
        assert value in text
    assert "UPDATE simpa_indicator_methodologies SET status='draft' WHERE status='proposed'" in text


def test_0027_is_the_sole_alembic_head():
    heads = subprocess.run(
        ["alembic", "heads"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "20260914_0027 (head)" in heads
    assert heads.count("(head)") == 1


def test_0027_offline_upgrade_and_downgrade_render():
    upgrade = subprocess.run(
        ["alembic", "upgrade", "20260914_0027", "--sql"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "ADD COLUMN contract_fingerprint" in upgrade
    assert "ADD COLUMN reference_check_detail" in upgrade
    assert "legacy_unknown" in upgrade
    assert "simpa_indicator_methodologies" in upgrade

    downgrade = subprocess.run(
        ["alembic", "downgrade", "20260914_0027:20260914_0026", "--sql"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "DROP COLUMN contract_fingerprint" in downgrade
    assert "status='draft'" in downgrade
