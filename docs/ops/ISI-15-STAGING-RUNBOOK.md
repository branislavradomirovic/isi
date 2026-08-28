# ISI-15 Production Deployment Readiness Runbook

## Workflow boundary
The controlling process is `docs/ops/ISI-PRODUCTION-WORKFLOW-LOCK.md`.

The developer workstation is not a Docker staging host. The prior loopback Docker rehearsal path is retired. Do not start `docker-compose.staging.yml` locally.

## Local phase
Local work is limited to implementation and automated validation:
- Python regression tests;
- static production audit;
- dependency consistency;
- native PostgreSQL/Alembic verification;
- deployment source/config contracts;
- read-only Git checks.

No local production/staging PostgreSQL, Redis, MinIO, Mailpit, API, Streamlit, worker, or nginx containers are started.

## Server phase
The actual runtime rehearsal and production installation happen on the existing Ubuntu application server.

Before mutation, run `tools/server/isi_server_preflight.sh` and review its output. The preflight is used to choose the exact ISI project directory, host bind port, reverse-proxy route, Docker-network strategy, shared Ollama endpoint, and resource limits without interfering with existing applications.

The final server deployment package must provide:
- dedicated ISI Compose project;
- dedicated PostgreSQL and Redis;
- durable S3-compatible/object storage;
- migration one-shot service;
- FastAPI and Streamlit services;
- separate data and AI workers;
- shared existing Ollama connectivity;
- production SMTP configuration;
- automated health/readiness and smoke checks;
- PostgreSQL/object backup and isolated restore proof;
- rollback commands scoped only to ISI.

## Safety
Never use `docker system prune`, broad volume/network deletion, `git clean`, `git reset`, or commands that stop unrelated Compose projects.

Production secrets remain server-local and are never printed by diagnostics or stored in Git.

## QA ownership
The owner does not perform manual browser QA. After automated server acceptance is green, colleagues receive the deployed application for functional testing.
