from pathlib import Path
import subprocess


MIGRATION = Path("migrations/versions/20260914_0026_domain_consumption_enforcement.py")


def test_0026_is_additive_and_preserves_legacy_rows():
    text = MIGRATION.read_text()
    assert 'revision = "20260914_0026"' in text
    assert 'down_revision = "20260913_0025"' in text
    assert 'server_default="LEGACY_OBSERVATION"' in text
    for table in ("simpa_analytics_runs", "ordo_analytics_runs"):
        assert table in text
    for column in (
        "analytical_artifact_type", "analytical_snapshot_id",
        "analytical_feature_version_id", "analytical_artifact_fingerprint",
        "dataset_contract_version_id", "dataset_contract_fingerprint",
        "analytical_quality_state",
    ):
        assert column in text
    assert "core_analytical_dataset_snapshots" in text
    assert "core_analytical_feature_versions" in text
    assert "core_analytical_dataset_contract_versions" in text


def test_0026_does_not_claim_forever_current_head():
    text = MIGRATION.read_text()
    assert "alembic heads" not in text.casefold()
    assert "current global head" not in text.casefold()


def test_0026_upgrade_offline_sql_is_renderable():
    sql = subprocess.run(
        ["alembic", "upgrade", "20260914_0026", "--sql"],
        check=True, capture_output=True, text=True,
    ).stdout
    assert "analytical_artifact_type" in sql
    identifiers = [
        f"{kind}_{prefix}_run_{suffix}"
        for kind, suffixes in (
            ("fk", ("snapshot", "feature", "contract")),
            ("ck", ("artifact_type", "artifact_binding", "governed_identity")),
            ("ix", ("analytical_snapshot", "analytical_feature", "dataset_contract")),
        )
        for prefix in ("simpa", "ordo")
        for suffix in suffixes
    ]
    assert max(map(len, identifiers)) <= 63
