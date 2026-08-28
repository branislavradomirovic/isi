# ISI Production Workflow Lock

This document is the controlling workflow from ISI-15 through production. It may be changed only by an explicit owner instruction.

## Locked sequence

1. Complete the ISI application and production-deployment code locally.
2. Run automated local validation only. Do not run the ISI Docker runtime on the developer workstation.
3. Keep ISI-15 uncommitted until automated implementation validation is green and the diff is reviewed.
4. Perform a read-only preflight of the existing Ubuntu application server before choosing ISI host ports, proxy routes, shared-service addresses, or production paths.
5. Build the exact ISI server deployment package from the observed server state.
6. Deploy ISI as an independent Docker Compose project on the existing Ubuntu server, alongside the existing applications without modifying or stopping them.
7. ISI owns its PostgreSQL database, Redis service, object-storage namespace/volume, API, Streamlit service, data worker, and AI worker.
8. ISI must reuse the existing server Ollama runtime. Do not start a second Ollama instance for ISI.
9. Production secrets live only on the server. Never commit real database, SMTP, S3, auth, TLS, or AI credentials.
10. Run Alembic and automated server acceptance after deployment: health/readiness, DB, Redis/RQ, storage, SMTP configuration/delivery, AI connectivity, persistence, backup/restore, auth/product isolation, reporting, and administration smoke checks.
11. Public DNS/TLS/cutover changes happen only in ISI-16 and only after the server stack is healthy.
12. The owner does not perform manual browser QA. Functional/manual acceptance is handed to colleagues only after the application is installed and automated production acceptance is green.
13. No script in this workflow may commit, push, reset, clean, or reconfigure Git remotes automatically.
14. Any blocker stops the sequence at the failing gate. Do not skip gates and do not substitute a different workflow without explicit owner approval.

## Developer workstation boundary

Allowed locally:
- source changes;
- Python tests;
- static deployment/configuration audits;
- Alembic checks against the existing native development PostgreSQL;
- read-only Git inspection;
- building deployment artifacts without starting their runtime.

Forbidden locally:
- starting the ISI production/staging Docker Compose runtime;
- creating ISI PostgreSQL/Redis/MinIO/Mailpit/Nginx containers;
- using the workstation as the production-like staging host;
- production DNS/TLS changes;
- real production SMTP recipients or production data.

## Server boundary

Before any ISI server mutation, run the read-only server preflight and record:
- Docker/Compose state and existing Compose projects;
- listening ports;
- reverse-proxy ownership and routes;
- CPU, memory, disk, and Docker storage;
- existing application working directories;
- existing Ollama reachability and models;
- safe path and port space for ISI.

The exact ISI production Compose file and edge route are finalized only from that evidence.
