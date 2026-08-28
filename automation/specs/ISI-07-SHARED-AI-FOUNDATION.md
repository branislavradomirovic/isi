# ISI-07 — Shared AI Foundation

## Status
Implementation package. The task remains `ready` until native-DB, API, Streamlit and browser/AI QA are accepted.

## Baseline
- Git HEAD: `1f7c70e` (`Complete ISI shared data platform`)
- Python: 3.11.15
- Alembic before: `20260828_0005`
- Required predecessor: `ISI-06-SHARED-DATA-PLATFORM = done`
- Local PostgreSQL: native Homebrew PostgreSQL; this task never starts Docker PostgreSQL

## Purpose
Build one provider-independent, tenant-safe AI substrate shared by SIMPA and ORDO. ISI-07 provides orchestration, policy, provenance, model/prompt registries, structured output, job lifecycle, embeddings and RAG namespace guards. Domain intelligence remains outside this phase.

## Locked boundaries
1. AI is decision-support. Human professional/institutional responsibility remains explicit.
2. SIMPA and ORDO share infrastructure, never domain prompts, domain models or private RAG namespaces implicitly.
3. Every private AI job and embedding is scoped by organization + product + workspace.
4. `ai.run` is required server-side for execution. Browser state is never trusted for authorization.
5. Sensitive SIMPA requests are always `local_only`; external fallback is forbidden regardless of caller preference.
6. No external provider is implemented as a default. The provider interface is extensible; Ollama is the concrete local provider in this phase.
7. A deterministic development stub exists only for local QA and tests. Production mode rejects it.
8. Request/output provenance records model, prompt version, policy, hashes, attempts, timing and review state.
9. Raw prompt/output content never appears in audit events. Job payload retention is explicit and configurable.
10. No domain-specific SIMPA recommendation, ORDO scenario, scoring, diagnosis, eligibility or institutional decision is created here.
11. No commit or push is performed by package scripts.

## Architecture

```text
SIMPA ─┐
       ├── Shared AI Orchestrator
ORDO ──┘        │
                ├── Policy guard
                ├── Model registry
                ├── Prompt/version registry
                ├── Provider gateway
                │     ├── OllamaProvider
                │     └── DevStubProvider (development/test only)
                ├── Structured-output validator
                ├── AI job + attempt lifecycle
                ├── Audit/provenance + telemetry
                ├── Embedding repository
                └── RAG namespace guard
```

## RAG namespaces
Allowed namespace families are deliberately explicit:

- `PUBLIC/ISI`
- `PUBLIC/SIMPA`
- `PUBLIC/ORDO`
- `ORG-<organization UUID>/SIMPA`
- `ORG-<organization UUID>/ORDO`

Private namespace access must match both the active organization and active product. `PUBLIC/ISI` may be read from either product. A private SIMPA namespace can never be resolved from ORDO context and vice versa.

## Provider policy
Policy profiles support:
- `local_only`
- `local_preferred`
- `any`

Current concrete execution path is local Ollama. External-provider integration is intentionally absent in ISI-07, but the gateway contract supports later providers without changing domain services.

Hard rule:

```text
product=SIMPA + sensitivity=sensitive => local_only
```

No caller, prompt or fallback policy may weaken that rule.

## Model registry
`core_ai_models` records:
- stable model key;
- provider type/name;
- concrete model name;
- purpose (`chat` or `embedding`);
- product scope (`SHARED`, `SIMPA`, `ORDO`);
- local/external capability;
- context/output limits;
- embedding dimensions when known;
- enabled state and timestamps.

Registry entries are configuration/provenance, not domain models.

## Prompt registry
`core_ai_prompts` + `core_ai_prompt_versions` provide immutable versioned prompt material:
- stable prompt key;
- product scope;
- purpose;
- version number;
- system/user templates;
- optional structured-output schema;
- checksum;
- draft/active/retired lifecycle.

Domain prompt content is intentionally deferred to ISI-09 and ISI-11. ISI-07 seeds only a harmless shared foundation diagnostic prompt.

## Policy profiles
`core_ai_policy_profiles` records provider policy, sensitivity class, external-provider allowance, human-review requirement and retry limit. Generic shared policies are seeded; domain-specific governance comes later.

## AI jobs
`core_ai_jobs` is tenant/workspace/product scoped and records:
- prompt/model/policy references;
- request hash and optional retained request text;
- output text / structured output;
- status (`queued`, `running`, `succeeded`, `failed`, `review_required`);
- provider/model snapshots;
- retry count;
- latency and token telemetry when returned by provider;
- normalized failures;
- human-review state;
- lifecycle timestamps.

`core_ai_job_attempts` stores attempt-level provider telemetry and failure diagnostics.

`core_ai_audit_events` is append-only operational provenance and never stores raw request/output text.

## Embeddings and pgvector
`core_ai_embeddings` always stores tenant/product/workspace scope, namespace, source identity, content hash, model, dimensions and a portable JSON vector representation.

The migration checks whether the PostgreSQL `vector` extension is already enabled:
- when enabled by the database administrator/environment, it creates `core_ai_embedding_vectors` with native `vector` storage;
- when not enabled, migration still succeeds and the portable JSON representation remains functional;
- runtime capability reporting distinguishes extension availability, enabled state and native-table state;
- no package automatically installs operating-system packages or escalates database privileges.

This gives ISI a non-blocking pgvector foundation while preserving a deterministic local setup.

## Structured output
Shared validation accepts JSON-object schemas with required fields and primitive property types. Invalid JSON/schema output is normalized as a provider/orchestrator failure; it is never silently accepted as valid structured data.

## Queueing
- `AI_JOB_BACKEND=inline` is deterministic local-development default.
- `AI_JOB_BACKEND=rq` uses Redis/RQ queue `isi-ai`.
- workers reopen their own DB session and re-check job scope/policy from durable records.

## API
Authenticated endpoints under `/api/v1/ai`:
- `GET /capabilities`
- `GET /models`
- `GET /prompts`
- `GET /jobs`
- `POST /jobs`
- `GET /jobs/{job_id}`
- `POST /embeddings`

All private endpoints revalidate organization/product/workspace plus `ai.run`.

## Streamlit
The shared shell gains an `AI` navigation entry only when `ai.run` is present. ISI-07 UI shows:
- active AI policy and provider capability;
- model/prompt registry;
- tenant/product/workspace-scoped recent jobs;
- a development-only foundation diagnostic action when the QA stub is enabled.

It does not pretend to be SIMPA or ORDO domain intelligence.

## Local QA
The one-command QA launcher:
- provisions existing SIMPA/ORDO/dual identities;
- starts FastAPI on 8004;
- enables the development stub only for that QA process;
- bootstraps generic AI registry rows;
- runs real login/context/AI API smoke tests;
- executes isolated SIMPA and ORDO diagnostic jobs;
- verifies cross-product job isolation and sensitive-SIMPA local-only enforcement;
- reports Ollama availability without requiring it;
- starts Streamlit on 8504;
- opens the browser;
- owns stable stop/status scripts.

## Acceptance
The package passes only when:
- exact clean baseline `1f7c70e` is detected;
- ISI-06 is `done`;
- Alembic starts at `20260828_0005`;
- migration `20260828_0006` renders offline and upgrades native PostgreSQL;
- focused AI policy/namespace/provider/structured-output/model/API tests pass;
- native PostgreSQL AI isolation/capability acceptance passes;
- full repository tests pass;
- Docker Compose deployment topology remains valid;
- `git diff --check` passes;
- task remains `ready` for browser/AI QA;
- no commit/push occurs.
