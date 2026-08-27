from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.public_migration.legacy_inventory import DEFAULT_SEEDS, crawl_site, write_inventory_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a read-only inventory of the current isi.rs public website.")
    parser.add_argument("--base-url", default="https://isi.rs/")
    parser.add_argument("--output-dir", default="data/migration/legacy_isi")
    parser.add_argument("--max-pages", type=int, default=300)
    parser.add_argument("--delay-seconds", type=float, default=0.05)
    args = parser.parse_args()

    bundle = crawl_site(
        args.base_url,
        max_pages=args.max_pages,
        seeds=DEFAULT_SEEDS,
        delay_seconds=args.delay_seconds,
    )
    summary = write_inventory_artifacts(bundle, Path(args.output_dir))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
