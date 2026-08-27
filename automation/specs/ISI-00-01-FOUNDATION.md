# ISI-00-01 — Architecture Freeze + Repository Foundation

## Status
READY FOR IMPLEMENTATION

## Mission
Create the first clean, executable skeleton for **ISI Platform** (Institut za Socijalnu Inkluziju) using the architecture baseline already approved:

> ISI is one institutional and technology platform. SIMPA and ORDO are two flagship domain applications that share the platform core, but keep separate domain models, UI, indicator registries, analytical logic, and AI profiles. The new `isi.rs` public website is FastAPI/Jinja, while the authenticated application is Streamlit over a shared FastAPI/PostgreSQL/Redis/AI backend.

This task establishes the foundation only. It must not implement product functionality prematurely.

---

## Locked architectural decisions

1. **One platform, two domains**
   - Shared platform core.
   - Separate `domains/simpa` and `domains/ordo` boundaries.
   - No COSMOS public/product layer.

2. **Public/private UI separation**
   - Public institutional website: FastAPI + Jinja2 + HTML/CSS/SVG + minimal JS.
   - Authenticated application: Streamlit.
   - The public site must never depend on Streamlit rendering.

3. **Backend topology**
   - FastAPI API service.
   - PostgreSQL as primary relational database.
   - Redis for cache/job infrastructure.
   - RQ-compatible worker foundation.
   - Streamlit private application consumes the API layer.

4. **Data architecture**
   - SQLAlchemy 2.x.
   - Alembic migrations.
   - PostgreSQL-first configuration.
   - No product-specific tables in this task.

5. **AI architecture**
   - Only an empty/shared `core/ai` boundary is reserved later.
   - No provider-specific business logic in ISI-00/01.
   - Future SIMPA and ORDO AI profiles must remain domain-specific.

6. **Multitenancy direction**
   - Organization is the future tenant boundary.
   - Role and product entitlement are separate concepts.
   - Full identity/organization/entitlement implementation is deferred to ISI-02.

7. **Migration direction**
   - Existing `https://isi.rs/` remains live during development.
   - Complete content inventory and migration is deferred to ISI-03.
   - New public design is deferred to ISI-04.

8. **Development workflow**
   - Local -> tests -> staging -> production.
   - Runner/analyzer never commit or push to remote.
   - Each phase has explicit gates.

---

## In scope

Create a new Python repository skeleton containing:

- Python project metadata.
- FastAPI bootstrap.
- Public Jinja landing placeholder.
- API health endpoint.
- Streamlit authenticated-app placeholder.
- PostgreSQL configuration.
- Redis configuration.
- SQLAlchemy Base/session foundation.
- Alembic bootstrap.
- Background worker bootstrap.
- Dockerfiles and Docker Compose.
- Structured logging foundation.
- Environment schema and `.env.example`.
- `pytest` baseline.
- Makefile commands.
- Architecture decision records (ADRs).
- `automation/tasks.json` and this task spec.
- SIMPA and ORDO domain package boundaries only.

---

## Explicitly out of scope

Do **not** implement yet:

- production landing-page design;
- migration of `isi.rs` content;
- authentication/login/register/reset;
- organization/user tables;
- RBAC/permissions;
- product entitlements;
- SIMPA features;
- ORDO features;
- indicators;
- data ingestion;
- AI providers or prompts;
- RAG/pgvector;
- reports;
- admin UI;
- billing;
- external integrations.

If any of these are needed merely to make the skeleton boot, use a placeholder boundary, not a fake implementation.

---

## Required repository structure

```text
isi-platform/
├── .env.example
├── .gitignore
├── README.md
├── Makefile
├── alembic.ini
├── docker-compose.yml
├── pyproject.toml
├── automation/
│   ├── tasks.json
│   └── specs/
│       └── ISI-00-01-FOUNDATION.md
├── migrations/
│   ├── env.py
│   └── versions/
├── docs/
│   └── architecture/
│       ├── ADR-0001-platform-baseline.md
│       ├── ADR-0002-public-private-ui.md
│       ├── ADR-0003-domain-boundaries.md
│       └── ADR-0004-service-topology.md
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── logging.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py
│   ├── public/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── templates/
│   │   │   ├── base.html
│   │   │   └── index.html
│   │   └── static/css/site.css
│   ├── streamlit_app/
│   │   ├── __init__.py
│   │   └── app.py
│   ├── workers/
│   │   ├── __init__.py
│   │   └── worker.py
│   └── domains/
│       ├── __init__.py
│       ├── simpa/__init__.py
│       └── ordo/__init__.py
└── tests/
    ├── test_architecture_contract.py
    └── test_health.py
```

Docker support may add `docker/` files as needed.

---

## API contract for this phase

### `GET /api/v1/health`
Must return HTTP 200 and a stable payload equivalent to:

```json
{
  "status": "ok",
  "service": "isi-api",
  "phase": "foundation"
}
```

### `GET /`
Must render the FastAPI/Jinja public placeholder and clearly identify:

- Institut za socijalnu inkluziju;
- SIMPA;
- ORDO;
- that the page is a foundation placeholder, not final design.

No production marketing claims are required in this phase.

---

## Configuration contract

Environment-backed settings must reserve at least:

- `ISI_ENV`
- `ISI_LOG_LEVEL`
- `DATABASE_URL`
- `REDIS_URL`
- `API_HOST`
- `API_PORT`
- `STREAMLIT_PORT`
- `PUBLIC_BASE_URL`
- `APP_BASE_URL`

No secrets committed to Git.

---

## Docker Compose contract

Services:

1. `postgres`
2. `redis`
3. `api`
4. `streamlit`
5. `worker`

Rules:

- API waits for PostgreSQL and Redis health where practical.
- Streamlit depends on the API service.
- Worker depends on Redis and PostgreSQL.
- Local ports must be explicit and overridable via environment variables.
- No AI model service in this phase.

---

## Testing contract

Required tests:

### Architecture contract
Assert that:

- SIMPA and ORDO domain packages both exist.
- public templates exist.
- Streamlit private app exists.
- core database/config modules exist.
- architecture ADRs exist.
- automation task registry exists.

### API health
Using FastAPI TestClient:

- `/api/v1/health` -> 200.
- payload is stable.
- `/` -> 200 and Jinja-rendered institutional placeholder.

### Static checks

- `python -m compileall -q src tests`
- `pytest -q`
- `git diff --check` when Git is initialized.
- `docker compose config` when Docker Compose is available.

---

## Acceptance gates

ISI-00/01 is accepted only if all are true:

- [ ] repository is cleanly created from this package;
- [ ] expected structure exists;
- [ ] FastAPI app imports successfully;
- [ ] Jinja public home renders;
- [ ] health endpoint passes;
- [ ] Streamlit bootstrap imports/compiles;
- [ ] SQLAlchemy foundation imports;
- [ ] Alembic config exists;
- [ ] Redis/RQ worker foundation exists;
- [ ] SIMPA and ORDO domain boundaries exist and contain no fake product logic;
- [ ] `pytest -q` passes;
- [ ] compileall passes;
- [ ] Docker Compose config validates when available;
- [ ] runner makes no Git commit/push;
- [ ] analyzer performs no source mutation;
- [ ] no production `isi.rs` cutover occurs.

---

## Runner contract

`run-ISI-00-01-FOUNDATION.sh`:

- creates the new repository from packaged payload;
- refuses to overwrite an existing non-empty target unless explicitly authorized;
- initializes Git if requested/defaulted;
- creates `.venv` and installs dependencies unless disabled;
- runs foundation tests;
- never commits;
- never pushes;
- prints exact next analyzer command.

---

## Analyzer contract

`analyze-ISI-00-01-FOUNDATION.sh` is read-only with respect to project source.

It must:

- verify required paths;
- validate architecture strings/contracts;
- run compileall;
- run pytest when dependencies are available;
- run `docker compose config` when Docker is available;
- run `git diff --check` and show status when Git exists;
- fail non-zero on a mandatory contract violation;
- print `ISI-00-01 FOUNDATION ANALYSIS PASSED` only after gates pass.

---

## Rollback

Because this task creates a new repository, rollback is simple:

- do not modify the existing production `isi.rs`;
- do not modify OralScan;
- delete the newly created ISI repository if the foundation is rejected.

---

## Next task after acceptance

`ISI-02-IDENTITY-ORGANIZATIONS-ENTITLEMENTS`

Scope will include:

- User
- Organization
- Membership
- Role/Permission
- Product
- Product Entitlement
- Workspace
- login/session foundation
- access matrix tests for SIMPA-only, ORDO-only, and dual-product users

Do not start ISI-02 until this foundation is accepted.
