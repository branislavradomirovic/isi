# ISI-06 — Shared Data Platform

## Status
Implementation package. The task remains `ready` until native-DB, API, Streamlit and browser QA are accepted.

## Baseline
- Git HEAD: `0884600` (`Complete ISI authenticated app shell`)
- Python: 3.11.15
- Alembic before: `20260827_0004`
- Required predecessor: `ISI-05-AUTHENTICATED-APP-SHELL = done`
- Local PostgreSQL: native Homebrew PostgreSQL, never Docker-managed by this task

## Purpose
Build the shared, tenant-safe data foundation used by both SIMPA and ORDO before any domain-specific analytics or AI work begins.

## Locked boundaries
1. `Organization` remains the tenant boundary.
2. Every data source, version and ingestion job is scoped by organization + product + workspace.
3. SIMPA and ORDO share infrastructure but never share workspace data implicitly.
4. Roles and product access remain separate. Data operations use existing `data.read`, `data.upload` and `data.validate` permissions.
5. Domain business data is not stored in generic JSON blobs.
6. Raw uploaded bytes are content-addressed and deduplicated only inside their tenant/product/workspace scope.
7. Development storage is local filesystem. The storage interface is S3-compatible-ready; production credential wiring is deferred to staging.
8. Redis/RQ is the production background-job path. Development defaults to deterministic inline execution so the local environment does not require Docker Redis.
9. No AI, RAG, embeddings, forecasting or domain-specific SIMPA/ORDO transformations are introduced here.
10. No commit/push is performed by package scripts.

## Data model

### `core_data_sources`
Logical source owned by exactly one organization/product/workspace.

Key fields:
- id
- organization_id
- workspace_id
- product_code
- name
- source_kind (`dataset`, `document`)
- status (`active`, `archived`)
- created_by_membership_id
- created_at / updated_at

### `core_data_source_versions`
Immutable uploaded version metadata.

Key fields:
- source_id + monotonically increasing `version_no`
- original_filename / extension / content_type
- size_bytes
- sha256
- storage_key
- ingest_status
- detected_format
- row_count / column_count / sheet_count
- schema_fingerprint
- created_by_membership_id
- created_at

The raw payload is not stored in PostgreSQL.

### `core_ingestion_jobs`
Durable lifecycle for inspect/validate work:
`queued -> running -> succeeded|failed`.

Records backend (`inline` or `rq`), progress, attempts, timestamps, RQ id, and normalized failure information.

### `core_data_quality_results`
Structured checks such as non-empty payload, recognized format, parseability, table shape and document registration.

### `core_data_audit_events`
Append-only shared data audit events for upload, version creation, ingestion, validation and failures.

## Supported ingestion foundation
- CSV: encoding best effort, header/row count, column count, schema fingerprint.
- JSON: object/list parsing, record and field counts, schema fingerprint.
- XLSX: ZIP/XML structural inspection without adding a new spreadsheet dependency; sheet count plus first-sheet dimensions with zip-bomb guards.
- TXT: text/line inspection.
- PDF / DOCX: safe document registration and integrity metadata in this phase; semantic extraction belongs to later document/AI work.

No `.xls` legacy binary parser is claimed.

## Storage
`src/platform/data/storage.py` defines the storage contract.

Development default:
- backend `local`
- root `.isi-data`
- relative key: `<org>/<product>/<workspace>/<sha-prefix>/<sha>.<ext>`
- atomic write
- no overwrite of a different blob
- duplicate bytes in the same scope reuse the same blob

The S3-compatible adapter boundary is explicit, but the SDK/credential implementation is intentionally deferred to deployment hardening.

## API
Authenticated endpoints under `/api/v1/data`:
- `GET /sources`
- `POST /sources`
- `GET /sources/{source_id}`
- `POST /sources/{source_id}/versions`
- `POST /versions/{version_id}/validate`
- `GET /jobs/{job_id}`

Every endpoint revalidates organization/product/workspace selection and required permission on the server.

## Background jobs
`DATA_JOB_BACKEND=inline` is the deterministic local-development default.

`DATA_JOB_BACKEND=rq` dispatches `src.workers.data_jobs.run_ingestion_job` to Redis/RQ. The worker always reopens its own DB session and storage backend and never trusts browser state.

## Streamlit
The existing `Podaci` navigation item becomes a real ISI-06 workspace:
- current organization/product/workspace scope
- source catalog
- upload form when `data.upload` is granted
- actual version/job/quality state
- no fabricated metrics

## Security controls
- deny-by-default permission checks
- server-side workspace/product/organization validation
- configured maximum upload size
- extension allowlist
- base64 validation
- filename normalization
- no user filename used as storage path
- XLSX zip-size guards
- no cross-tenant source lookup
- no raw file bytes returned by the API

## Acceptance
The package passes only when:
- clean exact baseline `0884600` is detected;
- predecessor task is done;
- migration `20260827_0005` renders and upgrades native PostgreSQL;
- focused model/storage/ingestion/service/API tests pass;
- native PostgreSQL isolation tests pass;
- full repository tests pass;
- Docker Compose config remains valid;
- `git diff --check` passes;
- task remains `ready` for browser QA;
- no commit/push occurs.
