# ISI Autonomous Development Instructions

This repository is developed using specification-driven autonomous engineering. These instructions are binding for Codex and any other implementation agent unless a task specification or owner instruction explicitly narrows them further.

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

## Work protocol

For every task:

1. Read this file, the task specification, relevant ADRs, and the current task registry.
2. Verify the required baseline and dependencies before editing.
3. Work on a dedicated branch unless the owner explicitly instructs otherwise.
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
14. Open/update the pull request with an exact implementation summary, tests executed, known limitations, and deferred server-verification items.
15. A task is not complete because the agent says it is complete; the deterministic acceptance gates must pass.

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

- `IMPLEMENTED` - code exists and local/task tests pass.
- `CI_VERIFIED` - repository CI acceptance passes.
- `SERVER_VERIFIED` - the explicitly approved server acceptance was executed successfully.
- `DEFERRED_SERVER_VERIFICATION` - implementation is complete but the current task intentionally does not touch the server.

Never label a capability production-verified when only code/CI verification exists.
