from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class PgVectorCapability:
    available: bool
    enabled: bool
    native_table: bool


def pgvector_capability(session: Session) -> PgVectorCapability:
    try:
        available = bool(
            session.execute(text("SELECT EXISTS (SELECT 1 FROM pg_available_extensions WHERE name='vector')")).scalar()
        )
        enabled = bool(
            session.execute(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector')")).scalar()
        )
        native_table = bool(
            session.execute(text("SELECT to_regclass('public.core_ai_embedding_vectors') IS NOT NULL")).scalar()
        )
        return PgVectorCapability(available=available, enabled=enabled, native_table=native_table)
    except Exception:
        return PgVectorCapability(available=False, enabled=False, native_table=False)


def persist_native_vector(session: Session, embedding_id: uuid.UUID, vector: list[float]) -> bool:
    capability = pgvector_capability(session)
    if not capability.enabled or not capability.native_table:
        return False
    vector_literal = json.dumps([float(item) for item in vector], separators=(",", ":"))
    session.execute(
        text(
            "INSERT INTO core_ai_embedding_vectors (embedding_id, embedding) "
            "VALUES (:embedding_id, CAST(:embedding AS vector)) "
            "ON CONFLICT (embedding_id) DO UPDATE SET embedding = EXCLUDED.embedding"
        ),
        {"embedding_id": embedding_id, "embedding": vector_literal},
    )
    return True
