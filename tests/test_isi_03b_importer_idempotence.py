import csv
import json
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from src.core.database import Base
from src.public_content import models  # noqa: F401
from src.public_content.models import PublicLegacySource, PublicMediaAsset, PublicPage, PublicPageTranslation, PublicRedirect
from src.public_migration.content_importer import import_legacy_content


def _write_snapshot(path: Path, *, url: str, legacy_path: str, locale: str, title: str):
    payload = {
        "schema_version": 1,
        "source_url": url,
        "legacy_path": legacy_path,
        "language": locale,
        "fetched_at": "2026-08-27T12:00:00+00:00",
        "content_title": title,
        "body_html": f"<h1>{title}</h1><p>Sadržaj</p>",
        "body_text": f"{title} Sadržaj",
        "content_sha256": "a" * 64,
        "source_html_sha256": "b" * 64,
        "inventory_content_sha256": "c" * 64,
        "current_inventory_style_sha256": "c" * 64,
        "extraction_method": "main",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_import_is_idempotent_and_keeps_home_translations_draft(tmp_path: Path):
    inventory = {
        "schema_version": 1,
        "base_url": "https://isi.rs/",
        "pages": [
            {
                "source_url": "https://isi.rs/", "legacy_path": "/", "title": "ISI", "language": "sr-Latn",
                "http_status": 200, "canonical_url": "https://isi.rs/", "meta_description": "", "content_type": "page",
                "content_sha256": "c" * 64,
            },
            {
                "source_url": "https://isi.rs/en/homepage-english/", "legacy_path": "/en/homepage-english/", "title": "ISI EN", "language": "en",
                "http_status": 200, "canonical_url": "https://isi.rs/en/homepage-english/", "meta_description": "", "content_type": "page",
                "content_sha256": "c" * 64,
            },
        ],
        "assets": [
            {"source_url": "https://isi.rs/wp-content/a.pdf", "legacy_path": "/wp-content/a.pdf", "asset_type": "document", "extension": ".pdf", "language": "sr-Latn", "discovered_from": "https://isi.rs/"}
        ],
    }
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    sr = snapshot_dir / "sr.json"
    en = snapshot_dir / "en.json"
    _write_snapshot(sr, url="https://isi.rs/", legacy_path="/", locale="sr-Latn", title="Institut")
    _write_snapshot(en, url="https://isi.rs/en/homepage-english/", legacy_path="/en/homepage-english/", locale="en", title="Institute")
    manifest = {
        "schema_version": 1,
        "failure_count": 0,
        "drift_count": 0,
        "snapshot_records": [
            {"source_url": "https://isi.rs/", "snapshot_file": str(sr)},
            {"source_url": "https://isi.rs/en/homepage-english/", "snapshot_file": str(en)},
        ],
    }
    manifest_path = tmp_path / "snapshot_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    redirects_path = tmp_path / "redirect_map.csv"
    with redirects_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["legacy_path", "candidate_new_path", "locale", "review_status", "notes"])
        writer.writeheader()
        writer.writerow({"legacy_path": "/", "candidate_new_path": "/", "locale": "sr-Latn", "review_status": "pending", "notes": ""})
        writer.writerow({"legacy_path": "/en/homepage-english/", "candidate_new_path": "/en/homepage-english/", "locale": "en", "review_status": "pending", "notes": ""})

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    report_path = tmp_path / "report.json"
    with factory() as session:
        import_legacy_content(session, inventory_path=inventory_path, snapshot_manifest_path=manifest_path, redirect_map_path=redirects_path, report_path=report_path)
        session.commit()
        import_legacy_content(session, inventory_path=inventory_path, snapshot_manifest_path=manifest_path, redirect_map_path=redirects_path, report_path=report_path)
        session.commit()
        assert session.scalar(select(func.count()).select_from(PublicPage)) == 1
        assert session.scalar(select(func.count()).select_from(PublicPageTranslation)) == 2
        assert session.scalar(select(func.count()).select_from(PublicLegacySource)) == 2
        assert session.scalar(select(func.count()).select_from(PublicMediaAsset)) == 1
        assert session.scalar(select(func.count()).select_from(PublicRedirect)) == 2
        page = session.scalar(select(PublicPage))
        assert page.page_key == "home"
        assert page.page_type == "home"
        assert page.status == "draft"
        assert session.scalar(select(func.count()).select_from(PublicRedirect).where(PublicRedirect.status != "pending")) == 0


def test_trailing_slash_aliases_share_one_translation_and_preserve_sources(tmp_path: Path):
    inventory = {
        "schema_version": 1,
        "base_url": "https://isi.rs/",
        "pages": [
            {
                "source_url": "https://isi.rs/biblioteka", "legacy_path": "/biblioteka", "title": "Biblioteka",
                "language": "sr-Latn", "http_status": 200, "canonical_url": "https://isi.rs/biblioteka/",
                "meta_description": "", "content_type": "page", "content_sha256": "c" * 64,
            },
            {
                "source_url": "https://isi.rs/biblioteka/", "legacy_path": "/biblioteka/", "title": "Biblioteka",
                "language": "sr-Latn", "http_status": 200, "canonical_url": "https://isi.rs/biblioteka/",
                "meta_description": "", "content_type": "page", "content_sha256": "c" * 64,
            },
        ],
        "assets": [],
    }
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    no_slash = snapshot_dir / "biblioteka-no-slash.json"
    slash = snapshot_dir / "biblioteka-slash.json"
    _write_snapshot(no_slash, url="https://isi.rs/biblioteka", legacy_path="/biblioteka", locale="sr-Latn", title="Biblioteka")
    _write_snapshot(slash, url="https://isi.rs/biblioteka/", legacy_path="/biblioteka/", locale="sr-Latn", title="Biblioteka")
    manifest_path = tmp_path / "snapshot_manifest.json"
    manifest_path.write_text(json.dumps({
        "schema_version": 1,
        "failure_count": 0,
        "drift_count": 0,
        "snapshot_records": [
            {"source_url": "https://isi.rs/biblioteka", "snapshot_file": str(no_slash)},
            {"source_url": "https://isi.rs/biblioteka/", "snapshot_file": str(slash)},
        ],
    }), encoding="utf-8")
    redirects_path = tmp_path / "redirect_map.csv"
    with redirects_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["legacy_path", "candidate_new_path", "locale", "review_status", "notes"])
        writer.writeheader()
        writer.writerow({"legacy_path": "/biblioteka", "candidate_new_path": "/biblioteka/", "locale": "sr-Latn", "review_status": "pending", "notes": "alias"})
        writer.writerow({"legacy_path": "/biblioteka/", "candidate_new_path": "/biblioteka/", "locale": "sr-Latn", "review_status": "pending", "notes": "canonical"})

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    report_path = tmp_path / "report.json"
    with factory() as session:
        report = import_legacy_content(
            session,
            inventory_path=inventory_path,
            snapshot_manifest_path=manifest_path,
            redirect_map_path=redirects_path,
            report_path=report_path,
        )
        session.commit()
        assert session.scalar(select(func.count()).select_from(PublicPage)) == 1
        assert session.scalar(select(func.count()).select_from(PublicPageTranslation)) == 1
        assert session.scalar(select(func.count()).select_from(PublicLegacySource)) == 2
        assert session.scalar(select(func.count()).select_from(PublicRedirect)) == 2
        translation = session.scalar(select(PublicPageTranslation))
        assert translation.route_path == "/biblioteka/"
        assert translation.locale == "sr-Latn"
        assert report["successful_inventory_pages"] == 2
        assert report["logical_page_translations"] == 1
        assert report["legacy_alias_pages"] == 1
