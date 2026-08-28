# ISI-15 - Production / Server Deployment Readiness

## Status
Implementation task on the locked baseline `938fa5c Complete ISI-14 security hardening`.

## Goal
Finish the application-side production deployment capability and make ISI ready for installation on the existing Ubuntu application server. ISI-15 does not use the developer workstation as a Docker staging host and does not perform public `isi.rs` cutover.

## Controlling workflow
`docs/ops/ISI-PRODUCTION-WORKFLOW-LOCK.md` is authoritative for ISI-15 through ISI-16. No workflow substitution is allowed without explicit owner instruction.

## Locked baseline
- Git HEAD remains `938fa5cce5dd185e9cc1b763d21c6c5a8e0e61fb` until the ISI-15 implementation is accepted and manually committed.
- Python 3.11.15.
- Native development PostgreSQL remains at Alembic `20260828_0013`.
- `ISI-14-SECURITY-HARDENING = done`.
- No automatic commit, push, reset, clean, remote configuration, DNS mutation, or production data mutation.

## Application-side production capabilities
ISI-15 keeps and validates:
- fail-closed production runtime settings;
- S3-compatible storage adapter;
- Redis/RQ data and AI job backends;
- real SMTP delivery adapter for verification, reset, and invitation;
- production-safe invitation responses with no raw token disclosure;
- FastAPI health/readiness endpoints;
- API, Streamlit, data-worker, and AI-worker container entry paths;
- reverse-proxy topology capable of routing `/` and `/api/v1` to FastAPI and `/app` to Streamlit;
- PostgreSQL/Redis/object-storage persistence contracts;
- backup/restore tooling and automated smoke probes;
- committed legacy migration acceptance artifacts without publishing drafts early.

## Existing staging artifacts
`docker-compose.staging.yml` and the staging probe scripts remain implementation/reference artifacts produced during ISI-15. They are not an instruction to run a Docker runtime on the developer workstation.

`tools/staging/run_isi15_staging_qa.sh` is intentionally fail-closed after the workflow lock. Runtime validation moves to the actual Ubuntu server deployment phase.

## Shared-server deployment design
The final server topology is derived from a read-only server preflight. The intended service boundary is:

- dedicated ISI Docker Compose project;
- dedicated ISI PostgreSQL service and durable volume;
- dedicated ISI Redis service;
- dedicated ISI object-storage namespace/volume;
- FastAPI API/public service;
- Streamlit authenticated application under `/app`;
- `isi-data` worker;
- `isi-ai` worker;
- reverse-proxy integration with the server's observed edge configuration;
- reuse of the existing server Ollama runtime; no ISI Ollama container.

Port numbers, host paths, edge proxy rules, production domains, and shared network attachment are not guessed in ISI-15. They are locked only after server preflight evidence.

## Local automated acceptance
The owner is not required to perform manual browser QA. ISI-15 local acceptance is automated:
1. workflow-lock contract;
2. ISI-13/ISI-14 safety regressions;
3. complete ISI-15 focused suite;
4. production staging static audit;
5. full Python regression via `python -m pytest`;
6. dependency consistency;
7. native PostgreSQL remains reachable and Alembic remains `20260828_0013`;
8. deployment files pass static/source contracts;
9. `git diff --check`;
10. read-only server preflight script is present and itself has a non-mutating contract.

No local Docker runtime is part of acceptance.

## Server preflight
Before creating the exact ISI server deployment release, run `tools/server/isi_server_preflight.sh` on the target Ubuntu server. It is read-only and must not read application `.env` contents.

The preflight establishes:
- running Compose projects and their working directories;
- current host port ownership;
- Caddy/nginx/other reverse-proxy state;
- Docker networks and durable resources;
- CPU/RAM/disk capacity;
- shared Ollama endpoint availability;
- safe ISI project path, internal host bind port, and proxy integration strategy.

## External functional QA
Manual/functional QA is not an ISI-15 owner gate. After ISI is installed and automated server acceptance is green, the build is handed to colleagues for functional testing.

## Non-goals
- no local Docker runtime;
- no manual browser QA by the owner;
- no `isi.rs` DNS/TLS/public cutover in ISI-15;
- no duplicate Ollama service;
- no production database/object-store/email mutation before the server deployment gate;
- no automatic commit or push.

## Next
After automated ISI-15 implementation acceptance and manual commit: `ISI-16-ISI-RS-PRODUCTION-CUTOVER`, beginning with read-only server preflight evidence and then controlled server installation/cutover.
