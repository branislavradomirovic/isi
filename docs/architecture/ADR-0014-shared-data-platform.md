# ADR-0014 — Shared Data Platform

## Decision
ISI uses one shared data infrastructure with strict organization/product/workspace scoping. SIMPA and ORDO do not duplicate upload, storage, ingestion, job, provenance or audit infrastructure.

Raw file bytes live outside PostgreSQL. PostgreSQL stores source/version/job/quality/audit metadata. The local development backend is a tenant-scoped content-addressed filesystem; the storage contract permits an S3-compatible backend in production.

Redis/RQ is the background worker topology. Development may use deterministic inline execution through the same worker function.

## Consequences
- Domain data transformations remain outside the shared layer.
- Every read/write operation revalidates the existing auth context and product/workspace access.
- A source from one workspace can never be resolved merely by knowing its UUID from another workspace.
- AI/RAG ingestion is explicitly deferred to ISI-07.
