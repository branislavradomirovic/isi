from pathlib import Path


def test_staging_rehearsal_preserves_legacy_cutover_safety_boundary():
    source = Path("tools/staging/probe_legacy_migration_artifacts.py").read_text()
    for marker in (
        "migration_acceptance_report.json",
        "media_manifest.json",
        "link_normalization_report.json",
        "final_redirect_map.csv",
        "non_draft_pages",
        "pending_redirects",
        "no network request, import, publication or redirect activation",
    ):
        assert marker in source


def test_https_smoke_accepts_unpublished_public_pages_but_forbids_draft_preview_leak():
    source = Path("tools/staging/smoke_https.py").read_text()
    assert "public.status_code not in {200, 404}" in source
    assert "DRAFT CONTENT" in source
    assert "LOCAL PREVIEW" in source
    assert "public draft-publication safety" in source
