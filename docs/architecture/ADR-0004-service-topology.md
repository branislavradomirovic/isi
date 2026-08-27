# ADR-0004 — Service Topology

Status: Accepted

Foundation services are PostgreSQL, Redis, FastAPI API/public web, Streamlit authenticated app, and an RQ-compatible worker. AI runtime is intentionally deferred until the shared AI foundation phase.

## Local development

Local ISI development uses the existing native PostgreSQL server on `localhost:5432`. ISI owns a separate database named `isi` and uses a dedicated least-privilege login role named `isi_app`. Existing project databases are isolated and must not be modified.

Redis is not required by ISI-02A and its local runtime decision is deferred until a feature requires it.

## Self-contained deployment

`docker-compose.yml` retains PostgreSQL and Redis as internal services for self-contained deployment and CI scenarios. Their database/cache ports are not published to the host by default, avoiding collisions with native development services. API and worker containers communicate with them through the Compose network.
