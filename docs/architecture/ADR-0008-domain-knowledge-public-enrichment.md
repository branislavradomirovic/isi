# ADR-0008 — Domain knowledge registry and structured public enrichment

## Status
Accepted for ISI-04B.

## Decision
ISI maintains one shared knowledge registry with explicit product and domain classification. Knowledge is never treated as an undifferentiated corpus.

Top-level product scopes are `ISI`, `SIMPA`, `ORDO`, and `SHARED`. Sources additionally declare `PUBLIC` or `ORGANIZATION` knowledge scope. Organization-scoped sources require an organization identifier. Public sources must not carry one.

ISI-04B introduces metadata and content structure only. It does **not** introduce vector embeddings, chunking, retrieval, prompt execution, or AI inference. Those belong to the later shared AI/RAG foundation.

The public website gains database-backed structured sections and section items. These are domain-classified, bilingual and draft-only. Templates render them generically instead of hardcoding SIMPA/ORDO methodology into HTML.

## Provenance
The initial source registry contains two reviewed, hash-pinned primary methodology sources supplied for the project: SIMPA social-protection methodology and ORDO destination-development methodology. Public copy is editorially condensed from those sources. Historical COSMOS naming in source documents is provenance only and is not part of current public brand hierarchy.

## RAG boundary
`rag_eligible` is metadata for future policy. It does not trigger ingestion. Future retrieval must enforce organization + product + domain boundaries before semantic similarity is evaluated.

## Safety
All public pages and new structured sections remain `draft`. Production draft preview remains forbidden. No redirects are activated and no cutover occurs in ISI-04B.
