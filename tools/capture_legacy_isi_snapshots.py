from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.public_migration.legacy_snapshot import capture_snapshots


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture read-only normalized content snapshots for the committed ISI-03A inventory.")
    parser.add_argument("--inventory", default="data/migration/legacy_isi/inventory.json")
    parser.add_argument("--output-dir", default="data/migration/legacy_isi/snapshots")
    args = parser.parse_args()
    manifest = capture_snapshots(args.inventory, args.output_dir)
    print(json.dumps({
        "expected_pages": manifest["expected_pages"],
        "success_count": manifest["success_count"],
        "failure_count": manifest["failure_count"],
        "drift_count": manifest["drift_count"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
