from __future__ import annotations

import json
from pathlib import Path

from src.core.database import build_engine, build_session_factory
from src.public.platform_seed import seed_platform_pages

SOURCE = Path("data/public/flagship_platforms.json")


def main() -> int:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    factory = build_session_factory(build_engine())
    with factory() as session:
        report = seed_platform_pages(session, payload)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
