import json
import os
from pathlib import Path

import pytest
from sqlalchemy import func, select

from src.core.database import build_engine, build_session_factory
from src.public_content.models import PublicLegacySource, PublicMediaAsset, PublicPage, PublicPageTranslation, PublicRedirect
from src.public_migration.content_importer import page_key_for


@pytest.mark.skipif(os.getenv("ISI_RUN_NATIVE_DB_TESTS") != "1", reason="native PostgreSQL acceptance test")
def test_native_postgres_public_content_import_matches_inventory():
    inventory = json.loads(Path("data/migration/legacy_isi/inventory.json").read_text())
    successful = [
        row for row in inventory["pages"]
        if row.get("content_type") == "page" and 200 <= int(row.get("http_status", 0)) < 400
    ]
    logical_translations = {
        (page_key_for(row["legacy_path"], row["language"]), row["language"])
        for row in successful
    }
    logical_pages = {page_key for page_key, _locale in logical_translations}
    report = json.loads(Path("data/migration/legacy_isi/import_report.json").read_text())
    fixture_root = Path(os.environ.get("ISI_NATIVE_FIXTURE_REPORT_ROOT", "test-results/native-postgres/legacy"))
    fixture_summary = json.loads((fixture_root / "fixture-summary.json").read_text())
    redirect_summary = fixture_summary["redirects"]

    factory = build_session_factory(build_engine())
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(PublicLegacySource)) == len(successful)

        legacy_page_ids = {
            page_id
            for page_id in session.scalars(
                select(PublicLegacySource.mapped_page_id).where(PublicLegacySource.mapped_page_id.is_not(None))
            ).all()
            if page_id is not None
        }
        assert len(legacy_page_ids) == len(logical_pages)

        imported_pairs = set(
            session.execute(
                select(PublicPage.page_key, PublicPageTranslation.locale)
                .join(PublicPageTranslation, PublicPageTranslation.page_id == PublicPage.id)
                .where(PublicPage.id.in_(legacy_page_ids))
            ).all()
        )
        assert imported_pairs == logical_translations

        assert session.scalar(select(func.count()).select_from(PublicMediaAsset)) == len(inventory.get("assets", []))
        assert session.scalar(select(func.count()).select_from(PublicRedirect)) == report["redirect_candidates"]
        assert report["logical_page_translations"] == len(logical_translations)
        assert report["logical_pages"] == len(logical_pages)
        assert report["legacy_alias_pages"] == len(successful) - len(logical_translations)
        assert session.scalar(select(func.count()).select_from(PublicPage).where(PublicPage.status != "draft")) == 0

        # The native CI fixture intentionally runs the ISI-03C redirect-finalization
        # stage before this regression suite. Assert the finalized redirect plan
        # exactly rather than the earlier post-import "all pending" intermediate state.
        assert session.scalar(
            select(func.count()).select_from(PublicRedirect).where(PublicRedirect.status == "approved")
        ) == redirect_summary["redirect_count"]
        assert session.scalar(
            select(func.count()).select_from(PublicRedirect).where(PublicRedirect.status == "disabled")
        ) == redirect_summary["preserve_count"]
        assert session.scalar(
            select(func.count()).select_from(PublicRedirect).where(PublicRedirect.status == "pending")
        ) == redirect_summary["pending_count"]

        translations = session.scalars(select(PublicPageTranslation)).all()
        assert translations
        assert all("<script" not in item.body_html.lower() for item in translations)
        assert all(item.body_text.strip() for item in translations)
