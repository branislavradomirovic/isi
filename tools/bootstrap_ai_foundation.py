from __future__ import annotations

import argparse

from src.core.database import build_session_factory
from src.platform.ai.embeddings import pgvector_capability
from src.platform.ai.service import bootstrap_ai_registry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-dev-stub", action="store_true")
    args = parser.parse_args()
    factory = build_session_factory()
    with factory() as session:
        bootstrap_ai_registry(session, include_dev_stub=args.include_dev_stub)
        session.commit()
        cap = pgvector_capability(session)
    print("ISI-07 AI registry bootstrap PASS")
    print(f"development_stub={'enabled' if args.include_dev_stub else 'not-seeded'}")
    print(f"pgvector_available={str(cap.available).lower()}")
    print(f"pgvector_enabled={str(cap.enabled).lower()}")
    print(f"native_vector_table={str(cap.native_table).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
