# ISI Observability & Operational Diagnostics Contract

Status: ISI-18 implementation contract. Server integration remains `DEFERRED_SERVER_VERIFICATION`.

## Privacy boundary

Observability is shared platform infrastructure. It never records raw request bodies, query strings, authorization/cookie values, passwords, tokens, AI prompts or outputs, uploaded payloads, filenames, storage keys, tenant identifiers, organization/workspace/user identifiers, or production credentials. Dynamic URL identifiers are normalized to `:id` before use as metric labels.

## Correlation and logs

Every FastAPI request receives a bounded request ID. A valid incoming `X-Request-ID` is propagated; invalid or missing values are replaced with a generated identifier and the selected value is returned in `X-Request-ID`. Application logging uses JSON records with an allow-list of extra fields and deterministic credential/Bearer redaction.

## Metric families

- `isi_http_requests_total`: method, normalized route, status class, outcome.
- `isi_http_request_latency_ms_{count,sum}`: method, normalized route, outcome.
- `isi_queue_dispatch_total`: job kind, backend, outcome.
- `isi_worker_executions_total` and `isi_worker_execution_latency_ms_{count,sum}`: job kind, outcome.
- `isi_ai_executions_total` and `isi_ai_execution_latency_ms_{count,sum}`: provider, registry model key, registry prompt key, product code, outcome. No AI content is emitted.
- `isi_ingestion_executions_total`, `isi_ingestion_execution_latency_ms_{count,sum}`, `isi_ingestion_rows_{count,sum}`, `isi_ingestion_columns_{count,sum}`: detected format and outcome only. No source names or storage keys are emitted.

The in-process registry provides deterministic JSON and Prometheus text serialization. HTTP export is disabled by default and requires the non-secret `OBSERVABILITY_HTTP_METRICS_ENABLED=true` configuration.

## Readiness

`/api/v1/diagnostics/readiness` checks PostgreSQL, Redis only when an RQ backend is configured, and configured local/S3-compatible object storage. Output is restricted to overall status plus component/state/reason-code triples. Connection strings, endpoints, buckets, paths and exception text are never returned. A failed required component returns HTTP 503.

## Deferred operational work

Prometheus/Grafana/Loki/OpenTelemetry deployment, production dashboard wiring, alert routing, on-call integration, production dependency verification and current-server capacity verification are explicitly deferred. No ISI-18 repository work contacts or mutates the current server; those activities remain owner-gated under ISI-28.
