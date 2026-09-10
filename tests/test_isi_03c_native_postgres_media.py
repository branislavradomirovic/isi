from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

import pytest
from sqlalchemy import func, select

from src.core.database import build_engine, build_session_factory
from src.public_content.models import PublicMediaAsset, PublicPage, PublicPageTranslation, PublicRedirect
from src.public_migration.media_redirect_validation import validate_internal_links


@pytest.mark.skipif(os.getenv("ISI_RUN_NATIVE_DB_TESTS") != "1", reason="native PostgreSQL acceptance test")
def test_native_postgres_media_redirect_and_link_contract():
    report_root = Path(os.getenv("ISI_NATIVE_FIXTURE_REPORT_ROOT", "data/migration/legacy_isi"))
    storage_root = Path(os.getenv("ISI_NATIVE_MEDIA_ROOT", "var/media/public"))
    import_report = json.loads((report_root / "import_report.json").read_text())
    media_manifest = json.loads((report_root / "media_manifest.json").read_text())
    acceptance = json.loads((report_root / "migration_acceptance_report.json").read_text())
    factory = build_session_factory(build_engine())
    with factory() as db:
        assets = db.scalars(select(PublicMediaAsset).order_by(PublicMediaAsset.source_url)).all()
        assert len(assets) == import_report["inventory_assets"]
        assert media_manifest["assets_total"] == len(assets)
        assert all(asset.migration_status == "verified" for asset in assets)
        for asset in assets:
            path = storage_root / asset.storage_path
            assert path.is_file()
            assert hashlib.sha256(path.read_bytes()).hexdigest() == asset.content_sha256

        assert db.scalar(select(func.count()).select_from(PublicPage).where(PublicPage.status != "draft")) == 0
        assert db.scalar(select(func.count()).select_from(PublicRedirect).where(PublicRedirect.status == "pending")) == 0
        approved = db.scalar(select(func.count()).select_from(PublicRedirect).where(PublicRedirect.status == "approved"))
        disabled = db.scalar(select(func.count()).select_from(PublicRedirect).where(PublicRedirect.status == "disabled"))
        assert approved == import_report["legacy_alias_pages"]
        assert disabled == import_report["logical_page_translations"]

        link_check = validate_internal_links(db, storage_root=storage_root)
        assert link_check["unresolved_count"] == 0
        translations = db.scalars(select(PublicPageTranslation)).all()
        assert all("https://isi.rs/wp-content/" not in (row.body_html or "") for row in translations)

    with (report_root / "final_redirect_map.csv").open(newline="", encoding="utf-8") as handle:
        redirect_rows = list(csv.DictReader(handle))
    assert sum(row["action"] == "redirect" for row in redirect_rows) == import_report["legacy_alias_pages"]
    assert sum(row["action"] == "preserve" for row in redirect_rows) == import_report["logical_page_translations"]
    assert acceptance["acceptance_passed"] is True
