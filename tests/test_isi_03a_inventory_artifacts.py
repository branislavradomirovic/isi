import csv
import json
from pathlib import Path

from src.public_migration.legacy_inventory import InventoryBundle, LegacyAssetRecord, LegacyPageRecord, write_inventory_artifacts


def test_artifacts_are_machine_readable_and_redirects_are_pending(tmp_path: Path):
    page = LegacyPageRecord(
        source_url="https://isi.rs/",
        legacy_path="/",
        title="ISI",
        language="sr-Latn",
        http_status=200,
        final_url="https://isi.rs/",
        canonical_url="https://isi.rs/",
        meta_description="",
        content_type="page",
        content_chars=10,
        content_sha256="abc",
        discovered_from="seed",
        fetched_at="2026-08-27T00:00:00+00:00",
    )
    asset = LegacyAssetRecord(
        source_url="https://isi.rs/wp-content/uploads/a.pdf",
        legacy_path="/wp-content/uploads/a.pdf",
        asset_type="document",
        extension=".pdf",
        language="sr-Latn",
        discovered_from="https://isi.rs/",
    )
    bundle = InventoryBundle("https://isi.rs/", "2026-08-27T00:00:00+00:00", [page], [asset], [])
    summary = write_inventory_artifacts(bundle, tmp_path)
    assert summary["successful_html_pages"] == 1
    assert json.loads((tmp_path / "inventory.json").read_text())["pages"][0]["legacy_path"] == "/"
    with (tmp_path / "redirect_map.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [{
        "legacy_path": "/",
        "candidate_new_path": "/",
        "locale": "sr-Latn",
        "review_status": "pending",
        "notes": "Preserve or replace during ISI-03B content mapping.",
    }]
