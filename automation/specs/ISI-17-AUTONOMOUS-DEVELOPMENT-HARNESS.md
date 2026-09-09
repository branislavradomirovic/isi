# ISI-17 - Autonomous Development Harness + CI

## Status

Planning specification for owner review. This task must not begin implementation until explicitly approved.

## Goal

Make the ISI repository capable of safely governing specification-driven autonomous development through Codex/GitHub without touching the current ISI server.

ISI-17 is the foundation for all later industrialization tasks. It does not add domain functionality to SIMPA or ORDO. It creates the rules, CI gates, task/evidence conventions, and release boundaries that later autonomous implementation tasks must obey.

## Baseline

- Current default branch: `main`.
- Existing completed implementation through ISI-14.
- Existing ISI-15 production/server readiness artifacts remain valid reference material.
- ISI-16 public production cutover is superseded as the immediate next task by this autonomous industrialization track and must remain deferred until a later explicitly approved deployment phase.
- Existing server topology and deployment artifacts must remain supported and must not be mutated during this task.

## Locked architecture

- ISI remains the institutional platform.
- SIMPA and ORDO remain the only domain applications.
- No COSMOS software/domain layer may be introduced.
- FastAPI remains backend/API/public-site technology.
- Streamlit remains authenticated application UI.
- PostgreSQL remains the primary relational database.
- Redis/RQ remains the queue/background-job mechanism unless a separate approved ADR changes it.
- S3-compatible storage remains the object-storage contract.
- Shared AI gateway remains the only domain path to model providers.
- Existing tenant, workspace, role/permission and product-entitlement boundaries remain unchanged.

## Deliverables

### 1. Repository agent contract

Add/validate root `AGENTS.md` containing binding rules for Codex and implementation agents, including:

- product/domain boundaries;
- server/deployment prohibition;
- secret handling;
- database migration rules;
- test integrity rules;
- AI human-review invariants;
- data isolation/provenance requirements;
- completion status terminology.

### 2. Autonomous-development lock

Add `docs/ops/ISI-AUTONOMOUS-DEVELOPMENT-LOCK.md` defining:

- GitHub as development control plane;
- current server as deployment target only;
- forbidden remote/server actions;
- forbidden production secret/data usage;
- approval boundaries;
- distinction among IMPLEMENTED / CI_VERIFIED / SERVER_VERIFIED / DEFERRED_SERVER_VERIFICATION.

### 3. Release policy

Add `docs/ops/ISI-RELEASE-POLICY.md` defining:

- branch/PR-based development;
- deterministic acceptance before merge;
- immutable release/tag expectations;
- release notes/changelog expectations;
- deployment only from an approved release candidate;
- rollback expectations;
- no casual production `git pull` as the final operating model.

### 4. Standard task specification template

Add `automation/specs/TASK-TEMPLATE.md` with mandatory sections:

- status;
- baseline;
- dependencies;
- objective;
- existing architecture;
- locked boundaries;
- required behavior;
- DB/API/UI/worker/config impact;
- security/privacy requirements;
- test requirements;
- exact acceptance commands;
- evidence requirements;
- non-goals;
- forbidden changes;
- completion definition;
- deferred server verification.

### 5. Evidence contract

Add `automation/evidence/README.md` defining evidence artifacts for every task. Evidence must be text/JSON/log-oriented and must never contain production secrets, credentials, raw tokens, sensitive institution data, or unnecessary PII.

Minimum task evidence should identify:

- baseline commit;
- final task commit;
- commands executed;
- pass/fail status;
- migration state if applicable;
- test counts/summary;
- known warnings;
- deferred server verification items;
- PR/review status.

### 6. CI baseline

Create GitHub Actions workflows (or the repository-supported equivalent) that run on pull requests and relevant branch pushes.

Required baseline gates:

1. Python environment setup using the repository-supported Python version.
2. Dependency installation using committed dependency definitions.
3. `python -m pip check`.
4. Repository formatting/lint checks using existing tools where already configured; if a new tool is added, justify it explicitly.
5. Static/type analysis using existing tools where available; do not introduce a high-noise blocker without first establishing a clean baseline.
6. Full Python test suite.
7. Focused security/tenant/product-isolation regressions.
8. Alembic offline render/consistency check.
9. Ephemeral PostgreSQL migration acceptance where feasible in GitHub Actions.
10. Docker Compose configuration validation for supported compose files.
11. Secret scanning using a maintained GitHub-compatible mechanism.
12. Dependency vulnerability scanning using a maintained GitHub-compatible mechanism.
13. SAST/security scanning appropriate to Python/FastAPI code, with findings configured to avoid silently ignoring high-confidence critical issues.
14. `git diff --check` or equivalent whitespace integrity gate.

Where container/image vulnerability scanning is not practical in the first ISI-17 implementation, the workflow architecture must reserve it as a required follow-up gate before ISI-20 closes. The task report must not falsely claim it is implemented.

### 7. Deterministic completion gate

Add a local acceptance runner such as `tools/ci/run_isi17_acceptance.sh` that executes all locally reproducible ISI-17 gates and fails on the first hard error or returns a non-zero aggregate status.

The script must:

- be non-destructive;
- not access production/server systems;
- not require production credentials;
- print clear phase boundaries;
- preserve useful failure output;
- end with an unambiguous PASS/FAIL summary.

### 8. Task registry update

Update `automation/tasks.json` so that:

- ISI-15 remains historical/current readiness context;
- ISI-16 production cutover is marked `deferred`/`on_hold` rather than executable next work;
- ISI-17 becomes the first task of the industrialization track;
- subsequent ISI-18 through ISI-28 tasks are registered with dependencies and high-level titles;
- ISI-28 is the only future task allowed to perform the current-server controlled upgrade and remains explicitly deferred pending owner approval.

The registry must remain valid JSON and easy for agents/tools to parse.

## Required security invariants

- CI must not expose repository or workflow secrets in logs.
- No workflow may SSH to the current server.
- No workflow may change DNS, ingress, SMTP production configuration, server Ollama configuration, or production data.
- Pull requests from untrusted contexts must not receive privileged production credentials.
- CI test data must be synthetic/non-sensitive.

## Required architectural regression tests

ISI-17 must preserve or explicitly run existing tests proving:

- tenant isolation;
- product entitlement enforcement;
- SIMPA cannot read ORDO domain resources and vice versa;
- sensitive SIMPA AI policy remains local-only where currently required;
- authentication/session/security regressions remain green;
- production configuration remains fail-closed where already specified.

## Non-goals

- No deployment to current server.
- No production DNS/TLS change.
- No production SMTP activation/change.
- No production secret-manager deployment.
- No external penetration test.
- No SIMPA indicator formula or LISI methodology implementation.
- No ORDO validated methodology implementation.
- No model/provider replacement.
- No Streamlit/FastAPI rewrite.
- No Kubernetes migration.
- No broad dependency upgrade.
- No user-visible feature redesign.

## Forbidden changes

- Do not weaken or delete existing tests.
- Do not mark failing checks as allowed-to-fail merely to obtain green CI without an explicit documented reason approved in the task spec.
- Do not bypass Alembic migrations through direct schema hacks.
- Do not merge SIMPA and ORDO domain semantics into shared modules.
- Do not add COSMOS to the runtime architecture.
- Do not commit secrets or real institutional data.
- Do not create automatic production deployment workflows.

## Acceptance criteria

ISI-17 may be marked `IMPLEMENTED` only when:

1. all required governance documents exist;
2. `AGENTS.md` exists and captures the locked boundaries;
3. task/evidence templates exist;
4. task registry represents the industrialization track correctly;
5. CI workflows are syntactically valid;
6. local acceptance runner succeeds on a clean supported development environment;
7. full existing regression suite passes;
8. no current-server access is required;
9. the implementation PR documents any temporarily deferred CI gate honestly.

ISI-17 may be marked `CI_VERIFIED` only after the pull request's required GitHub Actions checks are green.

`SERVER_VERIFIED` is not applicable to this task. Final status must include `DEFERRED_SERVER_VERIFICATION`.

## Evidence

Create `automation/evidence/ISI-17/` with at minimum:

- `acceptance-summary.md`;
- machine-readable test/CI summary where practical;
- list of workflow files/gates enabled;
- known warnings/deferred gates;
- confirmation that no server action was performed.

## Next

After owner acceptance and merge of ISI-17: `ISI-18-OBSERVABILITY-OPERATIONAL-DIAGNOSTICS`.
