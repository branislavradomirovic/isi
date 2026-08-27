from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.database import build_engine, build_session_factory
from src.public_migration.media_redirect_validation import build_acceptance_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only ISI-03C migration acceptance validator.")
    parser.add_argument("--storage-root", default="var/media/public")
    parser.add_argument("--media-manifest", default="data/migration/legacy_isi/media_manifest.json")
    parser.add_argument("--link-report", default="data/migration/legacy_isi/link_normalization_report.json")
    parser.add_argument("--redirect-map", default="data/migration/legacy_isi/final_redirect_map.csv")
    parser.add_argument("--report", default="data/migration/legacy_isi/migration_acceptance_report.json")
    args = parser.parse_args()

    factory = build_session_factory(build_engine())
    with factory() as session:
        report = build_acceptance_report(
            session,
            storage_root=args.storage_root,
            media_manifest_path=args.media_manifest,
            link_report_path=args.link_report,
            final_redirect_csv=args.redirect_map,
            output_path=args.report,
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["acceptance_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
