# ISI Autonomous Industrialization — Repository Audit

Status: planning evidence for PR #1. This audit is static and repository-grounded. Runtime execution of the test suite is intentionally deferred to the ISI-17 implementation/CI task.

Baseline audited: `main` at `bf4a648b1e118a0b087b437579d2f3f12ef2db94` (`Harden ISI precutover ingress configuration`).

## 1. Executive assessment

The ISI repository is materially more mature than a prototype and is a strong candidate for specification-driven autonomous development. The codebase already has a disciplined phase/spec/evidence model, an extensive regression suite, orderly Alembic migrations, explicit SIMPA/ORDO domain separation, production-oriented security hardening, and substantial server/release tooling.

The largest immediate gap is not application architecture. It is the absence of a repository-level autonomous engineering harness: there is no `.github` directory on the audited `main` baseline, no GitHub Actions CI, no deterministic dependency lock, no enforced lint/type/security pipeline, and no single task-level status/evidence dashboard. ISI-17 should therefore focus on making the repository itself the deterministic control plane before any later industrialization task is delegated to Codex.

## 2. Architecture confirmed

The existing source layout supports the locked product model:

- `src/domains/simpa/` contains SIMPA domain models/services/analytics/reporting adapters.
- `src/domains/ordo/` contains ORDO domain models/services/analytics/reporting adapters.
- shared capabilities live under `src/platform/` and cover identity/access, authentication, data, AI, reporting, administration, security, workspaces and related infrastructure.
- `src/platform/models.py` aggregates SQLAlchemy/Alembic model imports, including SIMPA and ORDO model registrations, without collapsing their runtime domain logic into one product.
- FastAPI remains the API/public backend and Streamlit remains the authenticated analytical UI.
- PostgreSQL, Redis/RQ and S3-compatible object storage remain the deployment contracts.

Conclusion: no horizontal framework rewrite is justified for industrialization. The autonomous track should preserve this architecture and improve quality, operability, methodology, security and release discipline around it.

## 3. Existing strengths to preserve

### 3.1 Phase-driven engineering history

`automation/tasks.json`, `automation/specs/` and `automation/evidence/` already establish the beginnings of a machine-readable engineering process. Existing specifications use locked baselines, explicit non-goals, migrations, acceptance gates and evidence. This is directly compatible with Codex task execution.

### 3.2 Strong regression surface

The test suite already covers architecture contracts, authentication/access, app context, public-site behavior, data platform, storage/ingestion, AI policy and structured output, SIMPA, ORDO, reporting, administration, security hardening and server/deployment contracts.

Representative existing guards include:

- architecture paths and SIMPA/ORDO boundaries;
- production workflow lock behavior;
- security configuration, headers, sessions and rate limiting;
- data/AI/product isolation;
- production/server deployment contracts.

ISI-17 should orchestrate and strengthen these tests rather than replace them.

### 3.3 Orderly database evolution

Alembic migrations progress sequentially through the current security-hardening revision `20260828_0013`. `migrations/env.py` loads the shared SQLAlchemy metadata registry and supports online/offline migration execution. This provides a sound basis for CI migration acceptance.

### 3.4 Existing server/release discipline

The repository already includes release archive creation, SHA-256 manifests, server deployment scripts, preflight tooling, backup/restore rehearsal and server acceptance scripts. The existing release builder requires a clean committed worktree and produces a Git-SHA-addressed archive.

These assets should be preserved for the final controlled-server task. They must not be invoked by autonomous development CI.

### 3.5 Security baseline

ISI-14 already introduced substantial fail-closed production hardening. Industrialization should extend that baseline rather than replace the authentication/security architecture.

## 4. Immediate gaps found

### 4.1 No repository CI control plane — P0

The audited `main` branch has no `.github` directory. There are therefore no GitHub Actions checks capable of independently accepting/rejecting a Codex pull request.

Required ISI-17 action: create blocking CI workflows before later autonomous implementation begins.

### 4.2 Dependency resolution is not reproducible — P0

`pyproject.toml` uses bounded dependency ranges and the development extra currently contains only `pytest` and `pytest-cov`. No deterministic dependency lock/constraints artifact is present in the audited root.

Required ISI-17 action: add a reproducible Python dependency lock/constraints mechanism derived from `pyproject.toml`, without performing an unrelated broad package upgrade. CI and Codex must install the same resolved dependency set.

### 4.3 No configured lint/type baseline — P0/P1

The audited `pyproject.toml` does not configure Ruff, mypy/Pyright or an equivalent static-quality toolchain.

Required ISI-17 action: establish a low-noise blocking lint/compile baseline and a documented type-check baseline. Do not hide existing defects behind blanket ignores. If full-project strict typing cannot be made clean inside ISI-17 without a disproportionate rewrite, record the exact baseline and enforce an incremental no-regression boundary, with full promotion scheduled no later than ISI-20.

### 4.4 Current Makefile analysis target masks one failure — P0

`Makefile` currently runs `git diff --check 2>/dev/null || true` under `analyze`, which means whitespace-integrity failure cannot fail the target.

Required ISI-17 action: make repository acceptance fail closed; no `|| true` is allowed for required gates.

### 4.5 Container build reproducibility/hygiene needs strengthening — P1

`docker/Dockerfile` currently uses `python:3.11-slim`, installs the package from ranged dependencies, then performs `COPY . .`. No `.dockerignore` exists on the audited baseline.

Required action: ISI-17 should add `.dockerignore` and deterministic dependency installation expectations. Image digest/signing/SBOM and deeper container hardening may be completed across ISI-20/ISI-27, but ISI-17 must at minimum ensure that CI builds are reproducible enough to detect regressions and do not unnecessarily include local/runtime artifacts.

### 4.6 Current release/deploy scripts must be explicitly quarantined from CI — P0

`tools/release/deploy_server_release.sh` performs SSH/SCP deployment and is intentionally locked to the current target host. This is valid future deployment tooling, but it creates a critical autonomous-development boundary.

Required ISI-17 action: CI must include a static policy test proving autonomous workflows do not invoke `tools/release/deploy_server_release.sh`, `tools/server/deploy_release_on_server.sh`, SSH/SCP, DNS mutation or other server-mutating commands. The files may remain in the repository for ISI-28.

### 4.7 Existing workstation QA scripts contain local-machine assumptions — P1

At least the ISI-14 local QA launcher defaults to a developer-specific macOS repository path and can open a browser. These are historical/manual QA helpers, not suitable as CI primitives.

Required ISI-17 action: do not reuse workstation launcher scripts as CI. Extract deterministic non-interactive checks into `tools/ci/` and keep historical QA scripts backward compatible unless a dedicated cleanup is justified.

### 4.8 Commit provenance is not yet release-grade — P1

The audited latest `main` commit is unsigned. This is not a blocker for ISI-17 implementation, but the final industrial release process needs stronger provenance.

Required action: define immutable tag/release provenance in ISI-17 release policy and complete signing/SBOM/provenance controls by ISI-27.

### 4.9 Human-readable autonomous status view is missing — P0 usability

`automation/tasks.json` is machine-readable, but the owner currently lacks one simple human-facing place to see which task is being implemented, its PR, CI state, review state and deferred server verification.

Required ISI-17 action: add `automation/STATUS.md` (or a deterministic generated equivalent) plus a standard PR status block. GitHub PR checks remain authoritative; the status file is a navigation/dashboard surface, not a substitute for CI.

## 5. ISI-17 CI design locked by this audit

The first autonomous implementation task should create a CI architecture with separate, observable jobs rather than one opaque script.

Minimum job groups:

1. `policy` — validate task registry/spec/evidence contracts, AGENTS/server freeze and forbidden workflow operations.
2. `quality` — Python 3.11 supported environment, deterministic dependencies, compile, lint, whitespace integrity and type baseline.
3. `tests` — full `python -m pytest` regression suite with test summary artifact.
4. `architecture-security` — focused authorization, tenant/product isolation, SIMPA/ORDO boundary and ISI-14 security regressions.
5. `migration` — Alembic offline render plus live upgrade to head on ephemeral PostgreSQL 17; fail if multiple/unexpected heads or migration failure occurs.
6. `compose` — static `docker compose config` validation for supported compose manifests using synthetic/non-secret environment values; no server deployment.
7. `supply-chain` — secret scan, dependency vulnerability audit and Python SAST with explicit severity/failure policy.
8. `build` — application container build as a non-deploying artifact/verification step; deeper image CVE/signing gates may be progressively hardened by ISI-20/ISI-27.
9. `acceptance` — aggregate required jobs into one unambiguous merge gate.

All workflows must run without production secrets and must contain no SSH/server deployment action.

## 6. Proposed exact local acceptance skeleton

The ISI-17 implementation should provide a non-interactive runner under `tools/ci/` that is semantically equivalent to the repository CI. At minimum it should execute or delegate to:

```text
python -m compileall -q src tests
python -m pip check
<blocking lint command established by ISI-17>
<type/no-regression command established by ISI-17>
python -m pytest -q
alembic upgrade head against an isolated PostgreSQL test database
alembic upgrade head --sql (or the repository-safe offline equivalent)
docker compose config
docker compose -f docker-compose.staging.yml config
docker compose -f docker-compose.server.yml config with synthetic env/paths only
<secret scan>
<dependency vulnerability audit>
<Python SAST>
git diff --check
```

CI may use GitHub service containers instead of running the repository's production/server Docker topology. No local-developer Docker runtime requirement is introduced by this design.

## 7. Tracking contract for autonomous execution

Every autonomous task PR must show, at minimum:

- Task ID and specification link.
- Baseline SHA and current head SHA.
- Codex implementation status.
- Required CI jobs and their state.
- Reviewer status.
- Evidence directory link.
- Known warnings/deferred items.
- Explicit `DEFERRED_SERVER_VERIFICATION` until ISI-28.

Recommended task state sequence:

`SPEC_READY -> IMPLEMENTING -> IMPLEMENTED -> CI_VERIFIED -> REVIEW_VERIFIED -> MERGE_READY -> MERGED`

A failure returns the task to `IMPLEMENTING`; it must never be hidden by changing the gate to allowed-to-fail without an approved specification change.

## 8. Audit conclusion

The repository architecture does not need to be redesigned before autonomous development. ISI-17 should first install the deterministic control harness around the mature codebase that already exists.

Planning recommendation: after this audit is accepted, refine/lock ISI-17 around the P0 findings above, merge the planning PR, then start Codex only on ISI-17. Do not start ISI-18 or any later implementation until ISI-17 has demonstrated a green Codex -> PR -> CI -> review loop.
