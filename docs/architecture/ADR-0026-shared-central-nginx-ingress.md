# ADR-0026 - Shared Central Nginx Ingress Authority

Status: **OWNER-APPROVED CANONICAL DECISION**  
Decision date: **2026-10-01**

## Context

ISI shares a production host/infrastructure boundary with Krcuga and OralScanXAI. Older ISI deployment material and ADR-0024 captured a historical topology in which Caddy still participated in parts of the host routing. Later production reconciliation in OralScanXAI established the current shared-host edge as central Nginx (`central-ingress-nginx-1`, Compose project `central-ingress`, service `nginx`) and explicitly preserved Krcuga `:8443`, OralScanXAI `:8444` and ISI `:8445`.

The ISI repository already models the correct private integration boundary: `api` and `streamlit` attach to external Docker network `isi_ingress` using aliases `isi-api` and `isi-streamlit`. The repository `edge` service is profile-gated as `precutover` and binds loopback `:8445` only for isolated acceptance.

## Decision

1. The final owner-approved shared edge for ISI is central Nginx `central-ingress-nginx-1`, Compose project `central-ingress`, service `nginx`.
2. Caddy is not current ISI target authority. Historical Caddy references remain legitimate history where they describe an earlier observed server state.
3. The owner-locked public ISI endpoint is `https://isi.opus.rs:8445/`.
4. Shared-host application ports remain isolated as:
   - Krcuga `:8443`;
   - OralScanXAI `:8444`;
   - ISI `:8445`.
5. ISI remains an independent Compose project with its own PostgreSQL, Redis, MinIO, API, Streamlit, data-worker and ai-worker services.
6. ISI production routing is expected to use `isi_ingress` with upstream identities `isi-api:8000` and `isi-streamlit:8501`. The exact central-Nginx route/certificate/upstream configuration is physically verified under ISI-28 before any change.
7. Repository `isi-edge` / `docker/nginx/isi-server-precutover.conf` is pre-cutover compatibility only. It must not become a second production ingress authority.
8. No server, DNS, certificate, central-ingress, SMTP, production-secret/data or server-Ollama mutation is authorized by this ADR. Those operations remain exclusive to explicitly owner-approved ISI-28.
9. Any ISI-28 ingress operation must fail closed if it cannot prove that Krcuga and OralScanXAI remain healthy and unchanged outside the explicitly approved shared-ingress change.

## Routing target

```text
https://isi.opus.rs:8445/
        |
        v
shared external/NAT boundary
        |
        v
central-ingress-nginx-1
        |
        +--> /app/     -> isi-streamlit:8501
        |
        +--> /, /api/ -> isi-api:8000
                         |
                         +-- PostgreSQL 17
                         +-- Redis/RQ
                         +-- MinIO/S3-compatible storage
                         +-- data-worker
                         +-- ai-worker
                         +-- host Ollama through governed AI gateway
```

This diagram is the owner-locked target architecture, not a claim that the route was reconfigured or revalidated by this governance-only change.

## Supersession

This ADR supersedes only the active-ingress/Caddy assumptions in ADR-0024 and related historical ISI-15/ISI-16 material. ADR-0024 remains useful historical evidence of the 2026-08-28 server audit and must not be rewritten as if that earlier observation never existed.

## Consequences

- MasterPlan, status/task ledgers, AGENTS and technical documentation must use central Nginx as the final shared-edge authority.
- Future work must not build a parallel ISI production edge.
- ISI-26 and ISI-27 remain repository/application work and do not mutate the shared host.
- ISI-28 begins with a fresh read-only server audit and only then may reconcile the live shared-Nginx route to this owner-approved target.
