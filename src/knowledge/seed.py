from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.knowledge.models import KnowledgeDomain, KnowledgeSource, KnowledgeSourceDomain


def seed_knowledge_registry(session: Session, domain_payload: dict, source_payload: dict) -> dict[str, int]:
    """Idempotently seed public domain taxonomy and reviewed source metadata."""
    counts = {"domains": 0, "sources": 0, "source_domains": 0}
    by_code: dict[str, KnowledgeDomain] = {}
    for row in domain_payload["domains"]:
        domain = session.scalar(select(KnowledgeDomain).where(KnowledgeDomain.code == row["code"]))
        if domain is None:
            domain = KnowledgeDomain(code=row["code"], product_scope=row["product_scope"], title_sr=row["title_sr"], title_en=row["title_en"])
            session.add(domain)
            session.flush()
        domain.product_scope = row["product_scope"]
        domain.title_sr = row["title_sr"]
        domain.title_en = row["title_en"]
        domain.description_sr = row.get("description_sr", "")
        domain.description_en = row.get("description_en", "")
        domain.sort_order = row.get("sort_order", 1000)
        domain.is_active = True
        by_code[row["code"]] = domain
        counts["domains"] += 1
    session.flush()
    for row in domain_payload["domains"]:
        parent_code = row.get("parent_code")
        by_code[row["code"]].parent_id = by_code[parent_code].id if parent_code else None

    for row in source_payload["sources"]:
        source = session.scalar(select(KnowledgeSource).where(KnowledgeSource.source_key == row["source_key"]))
        if source is None:
            source = KnowledgeSource(source_key=row["source_key"], knowledge_scope=row["knowledge_scope"], product_scope=row["product_scope"], locale=row["locale"], source_type=row["source_type"], title=row["title"])
            session.add(source)
            session.flush()
        for field in ("knowledge_scope", "product_scope", "locale", "source_type", "title", "source_uri", "origin_name", "authority_level", "review_status", "sensitivity", "rag_eligible", "content_sha256", "provenance"):
            setattr(source, field, row.get(field, getattr(source, field)))
        counts["sources"] += 1
        desired = set(row.get("domain_codes", []))
        existing = {link.domain_id: link for link in session.scalars(select(KnowledgeSourceDomain).where(KnowledgeSourceDomain.source_id == source.id)).all()}
        desired_ids = {by_code[code].id for code in desired}
        for domain_id, link in list(existing.items()):
            if domain_id not in desired_ids:
                session.delete(link)
        for idx, code in enumerate(row.get("domain_codes", [])):
            domain = by_code[code]
            link = existing.get(domain.id)
            if link is None:
                link = KnowledgeSourceDomain(source_id=source.id, domain_id=domain.id)
                session.add(link)
            link.is_primary = idx == 0
            counts["source_domains"] += 1
    session.commit()
    return counts
