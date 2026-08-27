from __future__ import annotations

import json
from pathlib import Path

from src.core.database import build_engine, build_session_factory
import src.platform.models  # noqa: F401  # register complete SQLAlchemy metadata for CLI execution
from src.knowledge.seed import seed_knowledge_registry
from src.public.section_seed import seed_public_sections

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    domain_payload = json.loads((ROOT / "data/knowledge/domain_registry.json").read_text())
    source_payload = json.loads((ROOT / "data/knowledge/source_registry.json").read_text())
    section_payload = json.loads((ROOT / "data/public/domain_sections.json").read_text())
    factory = build_session_factory(build_engine())
    with factory() as session:
        knowledge = seed_knowledge_registry(session, domain_payload, source_payload)
        sections = seed_public_sections(session, section_payload)
    print(json.dumps({"knowledge": knowledge, "public_content": sections}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
