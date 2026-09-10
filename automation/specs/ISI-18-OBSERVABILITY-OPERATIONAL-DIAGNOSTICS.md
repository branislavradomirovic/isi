# ISI-18 — Observability & Operational Diagnostics

Status: **IMPLEMENTING**  
Server verification: **DEFERRED_SERVER_VERIFICATION**

## Status

Owner-authorized repository-only implementation. No current-server access is permitted.

## Baseline

- `ISI-17-AUTONOMOUS-DEVELOPMENT-HARNESS` is `MERGED` and all required acceptance gates are green.
- FastAPI, Streamlit, PostgreSQL, Redis/RQ, S3-compatible storage and the shared AI gateway remain the locked architecture.
- Existing security, tenant/product isolation, AI policy and production-freeze invariants remain binding.

## Dependencies

- `ISI-17-AUTONOMOUS-DEVELOPMENT-HARNESS`
- Existing health endpoint, queue/worker adapters, AI job registry and data-ingestion worker.

## Objective

Make application failures and degradation diagnosable from privacy-safe, code-verifiable telemetry without requiring or contacting the future production monitoring host.

## Existing architecture

Observability is a shared platform capability. It may instrument shared infrastructure and domain-neutral execution paths, but it must not introduce SIMPA/ORDO domain logic or a new application/product layer.

## Locked boundaries

- No SSH/SCP, deployment, DNS, ingress, production SMTP, production credential/data, or server Ollama access.
- No raw request bodies, query strings, authorization headers, cookies, passwords, tokens, prompts, client/institution data or tenant identifiers in logs/metric labels.
- No COSMOS application/runtime/domain/tenant/menu/product/software layer.
- Do not weaken existing CI, security, authorization, product or tenant isolation gates.

## Required behavior

1. Generate or safely accept a bounded correlation/request ID for every FastAPI request and return it in `X-Request-ID`.
2. Emit structured JSON application logs with request correlation and deterministic redaction of common credential/token patterns.
3. Record privacy-safe FastAPI request count, status/error class and latency metrics without query strings or unbounded identifiers.
4. Record queue dispatch outcomes and worker execution outcomes/latency for AI and ingestion jobs.
5. Record AI execution telemetry using registry-safe labels (provider, model key, prompt key, product code, outcome) without prompt/request/output content.
6. Record ingestion telemetry using bounded format/outcome labels and numeric row/column observations without source filenames, object keys or tenant IDs.
7. Provide application-visible readiness diagnostics for PostgreSQL, Redis when RQ is configured, and local/S3-compatible object storage where configured.
8. Readiness output must expose only component/state/reason-code style diagnostics; it must not expose URLs, credentials, buckets, filesystem paths or exception text.
9. Provide deterministic JSON and Prometheus-text metric export contracts. HTTP metric export is disabled by default and may be enabled explicitly by non-secret configuration.
10. Record committed task evidence and an operations contract documenting metric names, labels, readiness semantics and deferred dashboard/server work.

## Impact

Shared operational instrumentation only. No schema migration is required for in-process telemetry. Runtime behavior remains backward compatible; observability failure must not cause business requests to fail except the explicit readiness endpoint reporting unhealthy dependencies.

## Security and privacy

- Redact credential-like values before structured logging.
- Log only an allow-list of structured fields.
- Normalize dynamic path segments before use as metric labels.
- Cap and normalize metric label values to prevent high-cardinality/PII leakage.
- Never log raw AI prompts, model outputs, uploaded data, filenames, object keys, authorization/session material or organization/workspace/user identifiers.

## Tests

- Correlation ID propagation and invalid-ID replacement.
- JSON structured log/redaction contract.
- Metric label/path privacy contract and Prometheus export.
- Request status/latency accounting.
- Queue/worker/AI/ingestion metric helper contract.
- Readiness dependency result aggregation and privacy contract.
- Existing full repository, architecture/security, native PostgreSQL, migration, compose, supply-chain and build gates remain required.

## Exact acceptance commands

```bash
python -m pytest -q tests/test_isi_18_observability.py tests/test_isi_18_readiness.py
python -m pytest -q
python -m tools.ci.policy_check
tools/ci/native_postgres_tests.sh
tools/ci/migration_check.sh offline
```

GitHub Actions `acceptance` must pass on the PR head before merge.

## Evidence

Store under `automation/evidence/ISI-18/`:

- `kickoff.md`
- `acceptance-summary.md`
- `results.json`

PR description and review must cite the final head SHA and CI run.

## Non-goals

- Deploying Prometheus/Grafana/Loki/OpenTelemetry collectors or any monitoring host.
- Production dashboards, alert routing or on-call integration.
- Current-server capacity or production dependency verification.
- Domain methodology changes.

## Forbidden changes

- No server/DNS/ingress/production SMTP/production secret/data/server Ollama access or mutation.
- No test/gate suppression.
- No secrets or tenant/domain data in logs, metrics or evidence.
- No application/runtime/domain/tenant/menu/product/software layer named COSMOS.

## Completion definition

`IMPLEMENTED` when the repository implementation and task tests exist; `CI_VERIFIED` only after all required GitHub checks pass; `REVIEW_VERIFIED` only after independent review has no unresolved blocker; `MERGE_READY` only when evidence/status are synchronized; `MERGED` only after integration to `main` and post-merge acceptance is green.

## Deferred server verification

Production monitoring host integration, production dependency health, dashboard wiring and current-server behavior remain `DEFERRED_SERVER_VERIFICATION` through ISI-27. ISI-28 requires separate explicit owner approval.
