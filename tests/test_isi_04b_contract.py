import json
from pathlib import Path


def test_required_domain_knowledge_artifacts_exist():
    required = [
        "src/knowledge/models.py", "src/knowledge/seed.py", "src/public_content/sections.py",
        "src/public/section_seed.py", "src/public/section_service.py",
        "data/knowledge/domain_registry.json", "data/knowledge/source_registry.json",
        "data/public/domain_sections.json", "src/public/static/css/domain.css",
        "migrations/versions/20260827_0004_domain_knowledge_public_sections.py",
    ]
    for path in required:
        assert Path(path).is_file(), path


def test_domain_registry_has_clear_product_scopes_and_no_cosmos():
    payload = json.loads(Path("data/knowledge/domain_registry.json").read_text())
    domains = payload["domains"]
    assert {row["product_scope"] for row in domains} == {"ISI", "SIMPA", "ORDO", "SHARED"}
    assert len(domains) >= 40
    assert any(row["code"] == "simpa.social_protection" for row in domains)
    assert any(row["code"] == "ordo.destination_development" for row in domains)
    assert "COSMOS" not in json.dumps(payload, ensure_ascii=False)


def test_primary_source_registry_is_hash_pinned_and_domain_classified():
    payload = json.loads(Path("data/knowledge/source_registry.json").read_text())
    by_key = {row["source_key"]: row for row in payload["sources"]}
    simpa = by_key["public.simpa.social_protection.v1"]
    ordo = by_key["public.ordo.destination_methodology.v1"]
    assert simpa["content_sha256"] == "8b59fbc8624cde841da48e1e318964942c133a6e2e7153ac30025d15ff309e13"
    assert ordo["content_sha256"] == "68c3af1d9228709c6ae8d1bfceb749b76f8416d65b2c61bc1c31f4fc424df85b"
    assert len(simpa["domain_codes"]) >= 15
    assert len(ordo["domain_codes"]) >= 14
    assert simpa["knowledge_scope"] == ordo["knowledge_scope"] == "PUBLIC"


def test_public_enrichment_is_bilingual_draft_seed_content_and_cosmos_free():
    payload = json.loads(Path("data/public/domain_sections.json").read_text())
    assert len(payload["sections"]) >= 15
    assert {row["page_key"] for row in payload["sections"]} == {"home", "platform.simpa", "platform.ordo"}
    for section in payload["sections"]:
        assert set(section["translations"]) == {"sr-Latn", "en"}
        assert section["domain_code"]
        for item in section["items"]:
            assert set(item["translations"]) == {"sr-Latn", "en"}
    assert "COSMOS" not in json.dumps(payload, ensure_ascii=False)
