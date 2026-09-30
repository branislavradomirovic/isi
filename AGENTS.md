# ISI Autonomous Development Instructions

This repository is developed using specification-driven autonomous engineering. These instructions are binding for Codex and any other implementation agent unless a task specification or owner instruction explicitly narrows them further.

## Canonical authority and mandatory bootstrap

`docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md` is the canonical roadmap, architecture, development-governance and phase-boundary authority. `TECHNICAL_DOCUMENTATION.md` is the controlled living technical reference and must remain synchronized with the MasterPlan and as-built code. Read the complete MasterPlan before any task design or implementation.

Before editing or invoking Codex for every new chat/task/function/recovery:

1. verify canonical repository path, `main`, HEAD/tree, `origin/main`, one worktree, index and worktree state;
2. verify relevant exact-main `ISI required acceptance` evidence;
3. read the MasterPlan, this file, task/status ledgers, relevant specification, ADRs and ops contracts;
4. inspect actual relevant code/migrations/tests/services/APIs/workers/data/AI boundaries;
5. reconstruct accepted SHAs, recoveries, architectural decisions and owner approvals;
6. produce `DONE / PARTIAL / MISSING / DRIFT` against the MasterPlan;
7. perform the mandatory legacy/drift audit and resolve/classify findings;
8. only then lock the next exact mutable surface and implementation contract.

A new chat must retrieve available repository truth instead of asking the owner to repeat retrievable project history.

## Mandatory legacy/drift audit

Search for stale status/task text, duplicate/dead architecture, temporary/recovery code that became permanent, historical tests freezing mutable global state, stale branches/worktrees/clones, superseded schema/API/configuration, contradictory docs/ADRs/runbooks, stale flags/env/CI exemptions, raw-source governance bypasses, accidental generated dependencies and deprecated runtime/AI/deployment paths.

Classify every finding as `LEGITIMATE_HISTORY`, `REQUIRED_COMPATIBILITY`, `REMOVE_BEFORE_NEXT_SLICE`, or `REMOVE_IN_NAMED_PHASE(<phase>)`. Incompatible unclassified legacy blocks the next implementation slice.

## Canonical System Inventory maintenance

The MasterPlan `Canonical SYSTEM INVENTORY - complete product map` is the mandatory as-built/target/legacy component map. Every bootstrap reconciles the relevant inventory rows against actual code before implementation. Any task that adds, removes, renames, replaces or changes ownership/boundaries of a customer surface, service, model family, worker/job mechanism, AI provider, report component, security boundary, storage/deployment component, configuration family, external integration, test authority or legacy item must update the inventory in the same candidate. If there is no inventory impact, the task specification states `Canonical system inventory impact: NONE` and gives evidence.

## Codex execution authority

- ISI uses the standard `codex` CLI authenticated with Branislav's single canonical Outlook Codex account `branislav.radomirovic@outlook.com`.
- Project-specific Codex wrappers and project-specific `CODEX_HOME` profiles are legacy and must not be required by active ISI development.
- Codex credentials are machine-local and must never be committed or synchronized through GitHub.
- Codex is not invoked until bootstrap, architecture review and exact scope lock are complete.
- Normal implementation handoff is a locked MD contract plus runner and independent analyzer, not an ad-hoc conversational prompt.
- Codex must not stage, commit, push, deploy, use production secrets, create alternate workspaces or redefine architecture/scope/acceptance.
- The independent analyzer does not invoke Codex and does not mutate repository content/control state.

## Dual-Mac workstation handoff

- MacBook Air and iMac are supported owner development workstations.
- GitHub `origin/main` is the only source-code handoff authority between them.
- A handoff source must be on `main`, have `HEAD == origin/main`, a clean index/worktree, empty stash and exactly one development worktree.
- The same ISI project must not be actively developed on both workstations at the same time.
- Do not copy virtual environments, `.env` files, PostgreSQL/Redis/Docker state, logs, caches or machine-local credentials between Macs.
- Any new workstation/system dependency must be recorded first in the Master Plan and `docs/ops/ISI-DEVELOPMENT-WORKSTATION-REQUIREMENTS.md`.

## GitHub acceptance authority

Normal development is direct on canonical local `main`; branches/PRs require an explicit owner exception. Local tests, deterministic package runners and independent analyzers are the development validation lane. After deterministic validation, independent analysis and assistant human review, exact-file staging requires explicit owner approval and commit/push goes directly to `main`. A development push does not authorize GitHub-hosted full acceptance CI.

**DO NOT enable or introduce automatic GitHub-hosted Actions triggers for full CI during development. Do not add `push:`, `pull_request:`, `schedule:` or equivalent billable triggers to full acceptance workflows unless the task explicitly authorizes it. Default full acceptance/release workflows to manual `workflow_dispatch`.**

GitHub-hosted full CI is reserved for an explicitly owner-approved acceptance, release-candidate or production checkpoint. Before manual dispatch, GitHub Actions usage must be checked; usage must be checked again after the acceptance/release cycle. `CI_VERIFIED` and `COMPLETE` require the blocking `ISI required acceptance` workflow to finish `completed / success` on the exact committed `main` SHA after explicit checkpoint approval.

GitHub is source-control/CI evidence during industrialization, not a production deployment plane. Server mutation remains deferred to owner-approved ISI-28.


## Product architecture

- ISI is the institutional platform of the Institute for Social Inclusion.
- The platform contains two domain products only: SIMPA and ORDO.
- SIMPA and ORDO share infrastructure services but must remain separate domain modules.
- Do not introduce COSMOS as an application, domain, menu, product, tenant, database namespace, or user-visible layer.
- Shared code may contain infrastructure, identity, security, data-platform, AI-gateway, reporting, audit, and operational capabilities. It must not absorb SIMPA- or ORDO-specific indicators, methodology, analytical logic, prompts, or policy semantics.

## Autonomous-development boundary

- GitHub is the development control plane.
- The existing ISI server is a deployment target, not a development environment.
- Do not SSH to the server, mutate DNS, change central ingress, change production SMTP, rotate production credentials, modify server Ollama models, or deploy automatically.
- Do not request, store, print, commit, or expose production secrets.
- Server-side verification remains deferred until an explicitly approved deployment task.
- The owner-locked shared edge is central Nginx `central-ingress-nginx-1` (Compose project `central-ingress`, service `nginx`); Caddy is not current ISI target authority.
- ISI target endpoint is `https://isi.opus.rs:8445/`; `isi_ingress` with `isi-api`/`isi-streamlit` is the intended shared-edge integration point, while repository `isi-edge` is pre-cutover compatibility only.
- Krcuga `:8443` and OralScanXAI `:8444` are strict non-target services for ISI deployment work and must never be disrupted by an ISI change.

## Work protocol

For every task:

1. Complete the MasterPlan-first canonical bootstrap above, then read the task specification, relevant ADRs and the current task registry.
2. Verify the required baseline and dependencies before editing.
3. Perform normal owner-driven development only on the canonical local `main` branch. Do not create, switch to, rename, or use feature, implementation, review, temporary, or automation branches unless the owner explicitly authorizes an exception.
4. Preserve backward compatibility unless the specification explicitly authorizes a breaking change.
5. Add or update tests for every behavior change.
6. Never delete, weaken, skip, xfail, or bypass a failing test merely to make acceptance green.
7. Never fabricate domain formulas, indicator validation, thresholds, risk scores, forecasts, causal effects, recommendations, or institutional conclusions.
8. All database changes require an Alembic migration plus upgrade/downgrade or equivalent acceptance coverage.
9. Preserve Organization -> Membership -> Role/Permission -> Product entitlement -> Workspace authorization boundaries.
10. Preserve tenant isolation and SIMPA/ORDO isolation in services, APIs, workers, knowledge namespaces, reports, and AI flows.
11. Keep AI human-in-the-loop for institutional decision support. AI output must remain evidence-bounded, reviewable, attributable, and auditable.
12. Run the full task acceptance gate before declaring implementation complete.
13. Record required evidence under `automation/evidence/<TASK-ID>/` or the location defined by the task.
14. Do not create additional worktrees, clones, repositories, or checkout workspaces for task isolation unless the owner explicitly authorizes an exception.
15. Keep task changes unstaged and uncommitted on `main` until deterministic validation succeeds and the owner approves the exact candidate. Codex must never stage, commit, or push unless the owner explicitly authorizes that action.
16. After owner approval, the repository workflow is a direct commit and push to `main`. Full GitHub-hosted acceptance is then run only for a separately explicit approved acceptance/release checkpoint, after an Actions-usage pre-check, by manual `workflow_dispatch` against the exact `main` SHA; usage is checked again after the run. A pull request or merge is not part of the normal owner-driven workflow.
17. A task is not complete because the agent says it is complete; the deterministic acceptance gates must pass.

## Security and privacy invariants

- Never write raw passwords, reset tokens, invitation tokens, API secrets, authorization headers, session cookies, security peppers, or equivalent credentials to logs, tests, fixtures, audit records, screenshots, or evidence files.
- Client/institution data must not become shared cross-tenant or cross-product knowledge automatically.
- Sensitive SIMPA data must follow the existing local-only AI policy unless an explicitly approved policy change states otherwise.
- Preserve provenance and methodology versioning for computed analytical results.
- Prefer fail-closed behavior for production-sensitive configuration and authorization ambiguity.

## Code-quality rules

- Favor small, testable services and explicit domain contracts over hidden coupling.
- Avoid framework rewrites unless a task explicitly requires one.
- Streamlit remains the authenticated application UI unless a future accepted ADR changes it.
- FastAPI remains the public/API backend unless a future accepted ADR changes it.
- Existing Docker Compose deployment topology remains supported.
- New dependencies require justification and compatibility checks.
- Do not perform broad dependency upgrades as collateral work.

## Completion language

Use only evidence-backed status labels:

- `IMPLEMENTED` - an unstaged/uncommitted reviewed candidate exists on canonical `main` and local/task gates pass as available.
- `CI_VERIFIED` - all blocking GitHub Actions jobs pass on the exact committed `main` SHA.
- `REVIEW_VERIFIED` - review of the exact candidate or final `main` SHA has no unresolved technical blocker.
- `SERVER_VERIFIED` - the explicitly approved server acceptance was executed successfully.
- `DEFERRED_SERVER_VERIFICATION` - implementation is complete but the current task intentionally does not touch the server.

Never label a capability production-verified when only code/CI verification exists.
