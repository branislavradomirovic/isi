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
    factory = build_session_factory(build_engine())
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(PublicLegacySource)) == len(successful)
        assert session.scalar(select(func.count()).select_from(PublicPageTranslation)) == len(logical_translations)
        assert session.scalar(select(func.count()).select_from(PublicPage)) == len(logical_pages)
        assert session.scalar(select(func.count()).select_from(PublicMediaAsset)) == len(inventory.get("assets", []))
        assert session.scalar(select(func.count()).select_from(PublicRedirect)) == report["redirect_candidates"]
        assert report["logical_page_translations"] == len(logical_translations)
        assert report["logical_pages"] == len(logical_pages)
        assert report["legacy_alias_pages"] == len(successful) - len(logical_translations)
        assert session.scalar(select(func.count()).select_from(PublicPage).where(PublicPage.status != "draft")) == 0
        assert session.scalar(select(func.count()).select_from(PublicRedirect).where(PublicRedirect.status != "pending")) == 0
        translations = session.scalars(select(PublicPageTranslation)).all()
        assert translations
        assert all("<script" not in item.body_html.lower() for item in translations)
        assert all(item.body_text.strip() for item in translations)
