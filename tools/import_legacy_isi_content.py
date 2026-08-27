from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.database import build_engine, build_session_factory
from src.public_migration.content_importer import import_legacy_content


def main() -> int:
    parser = argparse.ArgumentParser(description="Import committed legacy ISI snapshots into the new draft public-content schema.")
    parser.add_argument("--inventory", default="data/migration/legacy_isi/inventory.json")
    parser.add_argument("--snapshot-manifest", default="data/migration/legacy_isi/snapshot_manifest.json")
    parser.add_argument("--redirect-map", default="data/migration/legacy_isi/redirect_map.csv")
    parser.add_argument("--report", default="data/migration/legacy_isi/import_report.json")
    args = parser.parse_args()

    factory = build_session_factory(build_engine())
    with factory() as session:
        report = import_legacy_content(
            session,
            inventory_path=args.inventory,
            snapshot_manifest_path=args.snapshot_manifest,
            redirect_map_path=args.redirect_map,
            report_path=args.report,
        )
        session.commit()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
