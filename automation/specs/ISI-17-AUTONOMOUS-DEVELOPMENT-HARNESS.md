# ISI-17 - Autonomous Development Harness + CI

## Status

**SPEC_READY / OWNER_APPROVED — 2026-09-09.**

Codex implementation is authorized after the planning PR is merged. Implementation must begin from the merged `main` baseline on a dedicated branch.

## Goal

Make the ISI repository capable of safely governing specification-driven autonomous development through Codex/GitHub without touching the current ISI server.

ISI-17 is the foundation for all later industrialization tasks. It does not add domain functionality to SIMPA or ORDO. It creates the rules, CI gates, task/evidence conventions, and release boundaries that later autonomous implementation tasks must obey.

## Baseline

- Current default branch: `main`.
- Existing completed implementation through ISI-14.
- Existing ISI-15 production/server readiness artifacts remain valid reference material.
- ISI-16 public production cutover is superseded as immediate next work and remains on hold.
- The owner-approved master plan and repository audit on `planning/isi-autonomous-industrialization` are binding planning inputs.
- After the planning PR is merged, Codex must record the exact merged `main` SHA as the implementation baseline.
- Existing server topology/deployment artifacts must remain supported and must not be mutated during this task.

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

## Repository-audit findings that are binding for ISI-17

ISI-17 must explicitly address these audited P0/P1 gaps:

1. no GitHub Actions CI exists on the audited `main` baseline;
2. dependency resolution is not deterministic enough for reproducible Codex/CI execution;
3. no blocking lint/static-quality baseline exists;
4. no documented type/no-regression baseline exists;
5. `Makefile` currently masks `git diff --check` failure via `|| true`;
6. no `.dockerignore` exists and container build hygiene/reproducibility needs strengthening;
7. deployment/SSH tooling exists and must be statically quarantined from autonomous workflows;
8. historical workstation QA scripts are interactive/local-machine oriented and must not become CI primitives;
9. owner-facing autonomous task status is missing;
10. final release provenance/signing is not yet release-grade and must be defined now and completed by ISI-27.

## Deliverables

### 1. Repository agent contract

Validate/finalize root `AGENTS.md` as the binding contract for Codex and implementation agents, including:

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
- artifact checksum/provenance expectations;
- target state for signed release/tag/SBOM provenance by ISI-27;
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

Add/finalize `automation/evidence/README.md` defining evidence artifacts for every task. Evidence must be text/JSON/log-oriented and must never contain production secrets, credentials, raw tokens, sensitive institution data, or unnecessary PII.

Minimum task evidence must identify:

- baseline commit;
- final task commit;
- commands executed;
- pass/fail status;
- migration state if applicable;
- test counts/summary;
- known warnings;
- deferred server verification items;
- PR/review status.

### 6. Owner-facing status surface

Add `automation/STATUS.md` or a deterministic generated equivalent. It must make the active task understandable without reading code.

Minimum fields:

- task ID/title;
- state from `SPEC_READY -> IMPLEMENTING -> IMPLEMENTED -> CI_VERIFIED -> REVIEW_VERIFIED -> MERGE_READY -> MERGED`;
- baseline SHA;
- implementation branch/PR;
- CI gate summary;
- reviewer status;
- evidence path;
- known warnings/deferred items;
- explicit server-verification state.

GitHub PR checks remain authoritative; this status surface is navigation/visibility only.

### 7. Deterministic dependency resolution

Add a reproducible dependency-lock or constraints mechanism derived from `pyproject.toml` and compatible with Python 3.11.

Requirements:

- do not perform a broad unrelated dependency upgrade;
- Codex/local CI/GitHub CI must use the same resolved dependency set or a provably equivalent deterministic install contract;
- dependency updates must remain reviewable and intentional.

### 8. CI baseline

Create GitHub Actions workflows that run on pull requests and relevant branch pushes.

Required job groups and gates:

1. **policy**
   - validate task registry/spec/evidence contracts;
   - validate AGENTS/server freeze rules;
   - statically forbid CI use of SSH/SCP, server deploy scripts, DNS/ingress mutation and production credentials/data.

2. **quality**
   - Python 3.11 supported environment;
   - deterministic dependency installation;
   - `python -m pip check`;
   - `python -m compileall -q src tests`;
   - blocking lint/static-quality baseline;
   - documented type/no-regression baseline;
   - `git diff --check` as a hard gate.

3. **tests**
   - full Python test suite;
   - machine-readable or otherwise durable test summary artifact where practical.

4. **architecture-security**
   - focused tenant isolation;
   - product entitlement enforcement;
   - SIMPA/ORDO isolation;
   - sensitive SIMPA local-only AI policy regression;
   - authentication/session/security regressions;
   - production fail-closed configuration regressions.

5. **migration**
   - Alembic offline render/consistency check;
   - verify expected single head;
   - ephemeral PostgreSQL 17 service;
   - live upgrade from empty database to `head`;
   - fail on migration error or unexpected revision state.

6. **compose**
   - static validation of supported compose files with synthetic/non-secret environment values;
   - must not launch the repository production/server runtime;
   - must not contact the current server.

7. **supply-chain**
   - maintained secret scanning;
   - maintained dependency vulnerability audit;
   - Python SAST/security scanning;
   - explicit documented severity/failure policy;
   - no silent suppression of high-confidence critical findings.

8. **build**
   - application container build/verification without deployment;
   - add `.dockerignore` and ensure local/runtime/secrets artifacts are excluded;
   - no registry push or server action required.

9. **acceptance**
   - aggregate required jobs into one unambiguous merge gate.

Where deeper container/image CVE scanning, signing or SBOM enforcement is not practical in ISI-17, reserve it as a mandatory follow-up no later than ISI-20/ISI-27 and state the deferral honestly.

### 9. Local deterministic completion gate

Add `tools/ci/run_isi17_acceptance.sh` or equivalent that executes all locally reproducible ISI-17 gates and fails closed.

The runner must:

- be non-destructive;
- not access production/server systems;
- not require production credentials;
- be non-interactive;
- not launch a browser;
- not depend on developer-specific absolute paths;
- print clear phase boundaries;
- preserve useful failure output;
- end with an unambiguous PASS/FAIL summary;
- never mask a required failure with `|| true` or equivalent.

Historical workstation QA scripts may remain for compatibility but must not be used as CI primitives.

### 10. Makefile/build hygiene

Update repository helper targets so required acceptance checks fail closed.

At minimum:

- remove masking of `git diff --check` failure from required analysis/acceptance paths;
- add stable entry points for CI/acceptance where useful;
- add `.dockerignore`;
- preserve existing supported Docker Compose topology.

### 11. Task registry update

Update `automation/tasks.json` so that:

- ISI-15 remains historical/current readiness context;
- ISI-16 remains `on_hold`/deferred rather than executable next work;
- ISI-17 reflects the active autonomous track state;
- ISI-18 through ISI-28 remain registered with dependencies/high-level titles;
- ISI-28 remains the only future task allowed to perform the current-server controlled upgrade and remains explicitly deferred pending owner approval.

The registry must remain valid JSON and easy for agents/tools to parse.

## Required security invariants

- CI must not expose repository or workflow secrets in logs.
- No workflow may SSH/SCP to the current server.
- No workflow may invoke server deployment scripts.
- No workflow may change DNS, ingress, SMTP production configuration, server Ollama configuration, production secrets or production data.
- Pull requests from untrusted contexts must not receive privileged production credentials.
- CI test data must be synthetic/non-sensitive.
- Existing server/deploy files may remain in the repository for ISI-28 but must be quarantined from autonomous workflows.

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
- No deletion of release/server tooling merely because autonomous workflows are forbidden from invoking it.

## Forbidden changes

- Do not weaken, delete, skip, xfail or bypass existing tests merely to obtain green CI.
- Do not mark failing required checks as allowed-to-fail merely to obtain green status without explicit approved specification change.
- Do not bypass Alembic migrations through direct schema hacks.
- Do not merge SIMPA and ORDO domain semantics into shared modules.
- Do not add COSMOS to runtime architecture.
- Do not commit secrets or real institutional data.
- Do not create automatic production deployment workflows.
- Do not call SSH/SCP/deployment/server-mutating scripts from CI.
- Do not turn historical interactive QA launchers into required CI dependencies.

## Exact acceptance contract

ISI-17 implementation must provide exact project commands, but the acceptance surface must be semantically equivalent to:

```text
python -m compileall -q src tests
python -m pip check
<blocking lint/static-quality command>
<type/no-regression command>
python -m pytest -q
<focused architecture/security regressions>
<alembic offline consistency/render check>
<isolated PostgreSQL 17 upgrade-to-head check>
docker compose config
<supported staging/server compose static-config checks using synthetic values only>
<secret scan>
<dependency vulnerability audit>
<Python SAST>
<non-deploying container build verification>
git diff --check
```

The implementation PR must list the exact realized commands and any explicitly deferred gate.

## Acceptance criteria

ISI-17 may be marked `IMPLEMENTED` only when:

1. all required governance documents exist;
2. `AGENTS.md` captures the locked boundaries;
3. task/evidence/status templates exist;
4. task registry represents the industrialization track correctly;
5. deterministic dependency install contract exists;
6. CI workflows are syntactically valid and contain the required job groups or clearly documented equivalent separation;
7. local acceptance runner succeeds on a clean supported development environment;
8. full existing regression suite passes;
9. focused architecture/security regressions pass;
10. Alembic offline and isolated PostgreSQL migration acceptance pass;
11. supported compose files validate statically with synthetic values;
12. required supply-chain/security scans execute with documented policy;
13. application image builds without deployment;
14. required gates fail closed;
15. no current-server access or production credentials are required;
16. implementation PR documents any temporarily deferred gate honestly;
17. evidence is written under `automation/evidence/ISI-17/`.

ISI-17 may be marked `CI_VERIFIED` only after the pull request's required GitHub Actions checks are green.

`SERVER_VERIFIED` is not applicable to this task. Final status must include `DEFERRED_SERVER_VERIFICATION`.

## Evidence

Create `automation/evidence/ISI-17/` with at minimum:

- `acceptance-summary.md`;
- machine-readable test/CI summary where practical;
- list of workflow files/gates enabled;
- dependency-lock/constraints provenance;
- migration acceptance result;
- security/supply-chain scan summary;
- known warnings/deferred gates;
- baseline/final commit SHAs;
- PR/review status;
- confirmation that no server action was performed.

## PR tracking contract

The ISI-17 implementation PR must include an owner-facing status block containing:

- Task: `ISI-17-AUTONOMOUS-DEVELOPMENT-HARNESS`;
- State;
- Baseline SHA;
- Head SHA;
- CI gate summary;
- Reviewer status;
- Evidence path;
- Known warnings/deferred items;
- `DEFERRED_SERVER_VERIFICATION`.

## Next

After owner acceptance and merge of a `CI_VERIFIED` ISI-17 implementation PR: `ISI-18-OBSERVABILITY-OPERATIONAL-DIAGNOSTICS`.
