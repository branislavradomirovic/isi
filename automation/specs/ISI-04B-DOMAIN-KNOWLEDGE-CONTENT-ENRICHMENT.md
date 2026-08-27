# ISI-04B — Domain Knowledge Registry + Public Content Enrichment

## Goal
Turn the accepted ISI-04 visual baseline into a substantially richer institutional presentation while establishing a durable domain-classification layer for future AI/RAG work.

## Baseline
- Git branch `main`
- committed HEAD `2965383`
- current ISI-04 partial worktree from the public-site package + HOTFIX-1 + HOTFIX-2
- Alembic `20260827_0003`
- all public pages remain draft

## Scope
1. Add Alembic `20260827_0004`.
2. Add `knowledge_domains`, `knowledge_sources`, `knowledge_source_domains`.
3. Add structured public section tables and bilingual section items.
4. Seed a hierarchical ISI/SIMPA/ORDO/SHARED domain registry.
5. Register the supplied SIMPA and ORDO methodology documents as reviewed, hash-pinned public sources.
6. Enrich Home, SIMPA and ORDO with detailed, source-grounded structured sections.
7. Render the structured sections through generic Jinja templates and a dedicated professional CSS layer.
8. Preserve draft-only preview and production safety.

## Explicit non-goals
- no embeddings
- no pgvector tables
- no chunking/RAG pipeline
- no LLM/provider calls
- no production publication
- no redirect activation/cutover
- no automatic commit/push
- no reintroduction of COSMOS branding

## Domain boundary
The public hierarchy remains ISI → SIMPA / ORDO. Shared methodology can be reused, but SIMPA and ORDO retain distinct domain registries.

## Acceptance
- migration graph reaches one head at `20260827_0004`
- at least 40 domain entries
- exactly two initial reviewed primary source records
- source SHA-256 values match the supplied PDFs
- at least 15 structured bilingual sections and 80 section items
- all new sections remain draft
- all public pages remain draft
- no vector/embedding/chunk tables exist
- full pytest suite passes
- Docker Compose deployment config remains valid
- browser preview of `/`, `/simpa/`, `/ordo/` is materially richer and visually coherent
