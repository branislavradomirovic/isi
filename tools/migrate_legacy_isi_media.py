from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.database import build_engine, build_session_factory
from src.public_migration.media_redirect_validation import (
    build_acceptance_report,
    download_media_assets,
    finalize_redirect_plan,
    normalize_draft_links,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate legacy isi.rs media and finalize safe legacy route mapping.")
    parser.add_argument("--storage-root", default="var/media/public")
    parser.add_argument("--media-manifest", default="data/migration/legacy_isi/media_manifest.json")
    parser.add_argument("--link-report", default="data/migration/legacy_isi/link_normalization_report.json")
    parser.add_argument("--redirect-map", default="data/migration/legacy_isi/final_redirect_map.csv")
    parser.add_argument("--acceptance-report", default="data/migration/legacy_isi/migration_acceptance_report.json")
    args = parser.parse_args()

    engine = build_engine()
    factory = build_session_factory(engine)

    # Media metadata is committed only after every same-site asset is verified.
    with factory() as session:
        media_manifest = download_media_assets(
            session,
            storage_root=args.storage_root,
            manifest_path=args.media_manifest,
        )
        session.commit()

    # Link rewrites and redirect status finalization are atomic together. Any
    # unresolved same-site link causes rollback and leaves the report for review.
    with factory() as session:
        link_report = normalize_draft_links(session, report_path=args.link_report)
        if link_report["unresolved_internal"]:
            session.rollback()
            print(json.dumps(link_report, ensure_ascii=False, indent=2))
            raise SystemExit("ERROR: unresolved same-site links remain; review link_normalization_report.json")
        redirect_report = finalize_redirect_plan(session, csv_path=args.redirect_map)
        session.commit()

    with factory() as session:
        acceptance = build_acceptance_report(
            session,
            storage_root=args.storage_root,
            media_manifest_path=args.media_manifest,
            link_report_path=args.link_report,
            final_redirect_csv=args.redirect_map,
            output_path=args.acceptance_report,
        )

    output = {
        "media": {
            "assets_total": media_manifest["assets_total"],
            "verified_count": media_manifest["verified_count"],
            "unique_blob_count": media_manifest["unique_blob_count"],
            "duplicate_asset_count": media_manifest["duplicate_asset_count"],
        },
        "links": {
            "links_seen": link_report["links_seen"],
            "media_rewritten": link_report["media_rewritten"],
            "pages_rewritten": link_report["pages_rewritten"],
            "unresolved_internal": link_report["unresolved_internal"],
        },
        "redirects": redirect_report,
        "acceptance_passed": acceptance["acceptance_passed"],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if not acceptance["acceptance_passed"]:
        raise SystemExit("ERROR: ISI-03C migration acceptance failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
