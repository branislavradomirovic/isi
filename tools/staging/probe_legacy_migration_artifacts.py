from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path("data/migration/legacy_isi")


def _json(name: str) -> object:
    path = ROOT / name
    if not path.is_file():
        raise RuntimeError(f"missing committed legacy migration artifact: {path}")
    return json.loads(path.read_text())


def main() -> int:
    acceptance = _json("migration_acceptance_report.json")
    _json("media_manifest.json")
    _json("link_normalization_report.json")
    redirects_path = ROOT / "final_redirect_map.csv"
    if not redirects_path.is_file():
        raise RuntimeError(f"missing committed legacy migration artifact: {redirects_path}")

    if not isinstance(acceptance, dict) or acceptance.get("acceptance_passed") is not True:
        raise RuntimeError("legacy migration acceptance report is not PASS")

    media = acceptance.get("media") or {}
    links = acceptance.get("links") or {}
    publication = acceptance.get("publication") or {}
    redirects = acceptance.get("redirects") or {}

    expected = {
        "media.assets_total": (media.get("assets_total"), 27),
        "media.verified_assets": (media.get("verified_assets"), 27),
        "media.unique_blobs": (media.get("unique_blobs"), 27),
        "media.error_count": (media.get("error_count"), 0),
        "links.translations": (links.get("translations"), 13),
        "links.unresolved_count": (links.get("unresolved_count"), 0),
        "publication.non_draft_pages": (publication.get("non_draft_pages"), 0),
        "redirects.approved_alias_redirects": (redirects.get("approved_alias_redirects"), 1),
        "redirects.preserved_routes": (redirects.get("preserved_routes"), 13),
        "redirects.pending_redirects": (redirects.get("pending_redirects"), 0),
    }
    mismatches = [f"{name}: got {got!r}, expected {want!r}" for name, (got, want) in expected.items() if got != want]
    if acceptance.get("missing_artifacts") not in ([], None):
        mismatches.append(f"missing_artifacts={acceptance.get('missing_artifacts')!r}")
    if mismatches:
        raise RuntimeError("legacy migration artifact drift: " + "; ".join(mismatches))

    with redirects_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 14:
        raise RuntimeError(f"legacy redirect map row count changed: {len(rows)} != 14")

    print("PASS committed isi.rs migration artifacts remain accepted and draft-only")
    print("PASS legacy migration rehearsal is read-only: no network request, import, publication or redirect activation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
