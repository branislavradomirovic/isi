# ISI Autonomous Industrialization Master Plan

Status: **OWNER_APPROVED canonical architecture/governance/system-inventory baseline - reconciled 2026-10-12**.

This plan is binding for the ISI industrialization track unless the owner explicitly approves a later change.

## 0. Canonical authority, architecture and mandatory development bootstrap

This section is the durable bootstrap authority for every future ISI chat, task, feature, recovery, refactor and phase closeout. It must be read before implementation planning.

### 0.1 Canonical truth and conflict resolution

The authority model is deliberately explicit:

1. A current explicit owner instruction is the highest policy/intent authority.
2. This MasterPlan is the canonical roadmap, architecture, execution-governance, sequencing and phase-boundary authority.
3. Accepted ADRs specialize architecture. They may not silently contradict this MasterPlan; conflicts require explicit reconciliation and, where architectural, a new or superseding ADR.
4. `AGENTS.md` is the executable agent/work-protocol mirror of this MasterPlan.
5. `TECHNICAL_DOCUMENTATION.md` is the controlled living technical reference for the current as-built platform and deployment target; it is subordinate to this MasterPlan and code/test truth and must be updated in the same governance change when architecture, technology, security or runtime boundaries materially change.
6. `automation/tasks.json` and `automation/STATUS.md` are synchronized execution/status ledgers, not independent architecture authorities.
7. Code, migrations, tests, schemas, APIs, workers and runtime contracts describe as-built reality and must be reconciled with approved architecture. Existing code never silently overrides an owner-approved architecture decision.
8. Exact-main GitHub Actions `ISI required acceptance` proves repository acceptance for a specific SHA. Green CI does not legitimize architectural or governance drift.

If these sources disagree, implementation stops. The disagreement is classified as drift, reconciled intentionally, and only then may the next implementation contract be locked.

### 0.2 Mandatory bootstrap for every new chat, feature or task

Before designing, prompting Codex, editing code or proposing an implementation package:

1. verify canonical repository path, branch, HEAD, tree, `origin/main`, one-worktree rule, index and worktree state;
2. verify the latest relevant exact-main `ISI required acceptance` run and the exact SHA it accepted;
3. read this complete MasterPlan first;
4. read `AGENTS.md`, `automation/tasks.json`, `automation/STATUS.md`, the task specification and all relevant ADR/ops documents;
5. inspect the actual relevant code, migrations, tests, APIs, services, workers, storage, data and AI boundaries;
6. reconstruct completed slices, accepted SHAs, recoveries, invariants and explicit owner decisions;
7. produce a `DONE / PARTIAL / MISSING / DRIFT` matrix against the applicable MasterPlan requirements;
8. reconstruct the applicable architecture, data flow and trust/control boundaries before proposing changes;
9. perform the mandatory legacy/drift audit defined below;
10. resolve or explicitly classify every detected conflict before implementation;
11. only then lock the next objective, exact mutable surface, tests, non-goals and acceptance gates;
12. Codex is prohibited until this bootstrap and scope lock are complete.

A new chat must retrieve repository truth when it is available instead of asking the owner to repeat retrievable project history.

### 0.3 Mandatory legacy/drift audit

Every bootstrap and every phase closeout must inspect for:

- stale task/status/current-slice statements;
- duplicate, dead or obsolete routes, services, models, schemas or configuration;
- compatibility shims, recovery code or temporary workarounds that accidentally became permanent;
- historical tests that assert mutable global state rather than their own historical contract;
- extra branches, worktrees, clones or temporary implementation workspaces;
- superseded schema/table/enum/API paths;
- documentation, ADR, task, spec or runbook text that contradicts this MasterPlan or accepted as-built architecture;
- stale feature flags, environment variables, CI exemptions or allowed-to-fail gates;
- downstream raw-source bypass after a governed analytical boundary exists;
- generated fixtures/artifacts accidentally left as runtime/product dependencies;
- deprecated runtime, AI/model or deployment paths.

Every finding is classified as exactly one of:

- `LEGITIMATE_HISTORY`;
- `REQUIRED_COMPATIBILITY`;
- `REMOVE_BEFORE_NEXT_SLICE`;
- `REMOVE_IN_NAMED_PHASE(<phase>)`.

Incompatible legacy without a valid history/compatibility reason is a blocker before the next implementation slice. Deferred cleanup requires a named phase and reason in canonical planning/status records.

Canonical precedent: ISI-22E R1/R2 removed historical ISI-22D tests that incorrectly asserted a mutable global Alembic current head. Historical tests must assert their own contract, not freeze future global state.

### 0.4 Canonical Codex execution contract

- ISI uses the standard `codex` CLI authenticated with Branislav's single canonical Outlook Codex account `branislav.radomirovic@outlook.com`.
- Project-specific Codex wrappers and project-specific `CODEX_HOME` authentication profiles are legacy and are not active execution authority.
- Codex credentials are machine-local and must never be committed, embedded in task packages or synchronized through GitHub.
- Codex operates only in the canonical repository/worktree and only inside a reviewer/owner-locked mutable surface.
- The normal implementation handoff is a locked MD contract + deterministic runner + independent analyzer, not an ad-hoc conversational prompt.
- Codex must not stage, commit, push, deploy, use production secrets, create alternate workspaces, or independently redefine architecture, scope or acceptance.
- The outer runner owns deterministic acceptance. The independent analyzer must not invoke Codex or mutate repository content/control state.
- Do not spend Codex tokens on read-only audits or deterministic documentation/governance work that can be completed without implementation generation.

### 0.5 Canonical Git/GitHub development contract

- Normal development is serial and directly on canonical local `main` with exactly one worktree.
- Supported owner development workstations are MacBook Air and iMac; only one is active for ISI development at a time.
- GitHub `origin/main` is the only source-code handoff authority between workstations.
- A source workstation may hand off only when it is on `main`, `HEAD == origin/main`, index/worktree are clean, stash is empty and exactly one development worktree exists.
- The destination workstation must fetch and fast-forward to the exact accepted `origin/main` SHA before development starts.
- Virtual environments, `.env` files, PostgreSQL/Redis/Docker state, logs, caches and machine-local credentials are never copied between Macs.
- Any new workstation/system dependency must be documented first in this Master Plan and `docs/ops/ISI-DEVELOPMENT-WORKSTATION-REQUIREMENTS.md`.
- Feature/review/automation/temporary branches, pull requests, extra clones and extra worktrees are not part of the normal workflow and require an explicit owner exception.
- Candidates remain unstaged/uncommitted through implementation, deterministic validation, independent analysis and human review.
- Exact-file staging requires explicit owner approval of the reviewed candidate.
- The approved candidate is committed and pushed directly to `main`.
- Development commit/push does not automatically invoke GitHub-hosted full acceptance. `CI_VERIFIED` completion requires an explicitly owner-approved acceptance/release checkpoint, Actions-usage pre-check, manual `workflow_dispatch` of `ISI required acceptance` on the exact committed `main` SHA, `completed / success`, and an Actions-usage post-check.
- GitHub is source-control and CI evidence during industrialization, not a production deployment plane.
- No automatic deployment or production secrets are authorized before ISI-28.

The binding lifecycle is:

`bootstrap -> architecture/scope audit -> locked contract -> implementation (Codex only if needed) -> outer runner -> independent analyzer -> assistant human review -> explicit owner approval -> exact-file staging -> direct main commit/push -> explicit acceptance-checkpoint approval -> Actions usage pre-check -> manual workflow_dispatch -> exact-main GitHub Actions -> Actions usage post-check -> COMPLETE`

Recovery exists only for a specific evidenced blocker and stays inside the smallest safe continuation surface. Do not restart broad implementation or rerun Codex reflexively after a narrow acceptance failure.

### 0.5A Mandatory Help, Help Coverage Matrix and XAI production-completeness gate

Owner rule approved 2026-09-16: **no customer-facing screen, function, workflow or user action may be classified `production-complete` unless its Help coverage is implemented, testable and recorded in the canonical Help Coverage Matrix.** This rule applies retrospectively to existing customer-facing capability and prospectively to every new capability. Inline captions, tooltips or error strings may contribute to coverage but do not by themselves satisfy the Help gate.

For every customer-facing screen/function/workflow/action, Help coverage must state at minimum:

1. what the function does;
2. when it should be used;
3. who may use it and the relevant role/permission boundary;
4. exact user steps/workflow;
5. meaning of fields, statuses, lifecycle states and result states;
6. at least one representative example where a useful example can be given without exposing sensitive data;
7. what the system explicitly does **not** do and the relevant non-goals;
8. common errors/failure states and safe recovery guidance;
9. security, privacy, methodological and regulatory limitations;
10. data/model/evidence provenance, version/fingerprint/quality state and human-review requirements where applicable.

The canonical Help Coverage Matrix must inventory every `CUSTOMER-FACING=YES` system-inventory row and its material user actions, with coverage status `MISSING`, `PARTIAL`, `COMPLETE` or `VERIFIED`, canonical Help/User Guide location, test/evidence authority and explicit `NOT_APPLICABLE` justification where a checklist item genuinely does not apply. Only `VERIFIED` (or explicitly justified `NOT_APPLICABLE` at the checklist-item level) satisfies the production-completeness gate.

**XAI / model-interpretation rule for both SIMPA and ORDO.** Any user-facing deterministic statistical/ML, embedding/retrieval, LLM or VLM result must have model-appropriate, faithful explanation. The product must never fabricate feature importance, confidence, causality, calibration or explanatory evidence that the underlying model/run does not support. When an explanation method is unsupported, unavailable or not calibrated, the UI/Help must say so explicitly.

At minimum, applicable XAI must expose and explain:

- model/capability identity, version and approved methodology/policy context;
- target/outcome semantics and model family for deterministic statistical/ML models;
- governed input/evidence provenance and the material fields/features used;
- how to interpret the result, including direction/magnitude where meaningful;
- coefficient/effect estimates, confidence intervals and p-values only when produced and methodologically meaningful;
- uncertainty, diagnostics, calibration and missing/dropped-data behavior;
- reproducibility/result fingerprints and production-eligibility state where available;
- scope, assumptions, failure modes, non-goals and required human review;
- for RAG/LLM/VLM: retrieved/source provenance, citations/evidence references, model/prompt/policy version, structured-output validation, fallback/failure state and a clear separation between deterministic numerical authority and generative explanation;
- confidence/probability only when it has an explicit semantics and calibration contract; otherwise no numeric confidence may be invented.

SIMPA Help/XAI must explicitly explain `DRAFT / PROPOSED / VALIDATED / RETIRED`, reference-suite execution and `PASS`, the distinction between deterministic reference evidence and human validation, `production_eligible`, continuous/count/binary-system-state/proportion-rate model semantics, coefficients/CI/p-values/diagnostics/calibration where applicable, missing data and dropped records, non-causal interpretation, and the absence of citizen scoring/eligibility automation, unapproved LISI formulas/weights/thresholds and automatic policy conclusions.

ORDO Help/XAI must explicitly explain indicator/methodology state, governed evidence provenance, scenario assumptions, the scenario-versus-forecast boundary, `NOT_ESTIMATED`, forecast intervals/backtesting/uncertainty when forecasting is actually validated, and the prohibition on presenting causal impact or predictive certainty without an approved evidence-backed methodology/model.

Help/XAI coverage is a release-blocking acceptance property, not documentation polish. ISI-23 and ISI-24 own domain Help/XAI completeness, ISI-25 owns shared AI/model evaluation/provenance/promotion/fallback XAI contracts, and ISI-27 may not accept a release candidate while any production-critical customer-facing Help/XAI coverage remains below `VERIFIED`.

### 0.5B CI / GitHub Actions Cost & Acceptance Policy

Owner rule approved 2026-09-17: GitHub-hosted full CI/acceptance is not the normal development-validation lane. During active development, local tests, deterministic package runners and independent analyzers are authoritative development validation.

- Do not enable or introduce automatic GitHub-hosted full-CI triggers for ordinary development commits, `push`, pull requests, Codex branches, schedules or routine checkpoints.
- The canonical full acceptance/release workflow defaults to manual `workflow_dispatch`.
- Adding `push:`, `pull_request:`, `schedule:` or an equivalent billable automatic trigger to a full acceptance workflow requires explicit owner/task authorization.
- GitHub-hosted full CI is reserved for an explicitly approved acceptance, release-candidate or production checkpoint.
- Commit/push approval is separate from full-CI-dispatch approval; a pushed development checkpoint does not itself authorize a hosted acceptance run.
- GitHub Actions usage must be checked immediately before and after each approved acceptance/release cycle.
- Full acceptance gates remain fail-closed and may not be weakened, skipped or made non-blocking to save minutes.
- This cost policy changes trigger authority only; it does not reduce the acceptance test set required when a full checkpoint is explicitly run.

### 0.6 Canonical platform architecture map

The system is layered as follows:

1. **Presentation** - public web plus authenticated application shell; backend remains authorization/data truth.
2. **API/security** - FastAPI, authentication, centralized RBAC, organization/membership/product-entitlement/workspace scope, audit and security controls.
3. **Domain separation** - SIMPA and ORDO are the only current domain applications; they remain domain-isolated while sharing infrastructure. COSMOS is not a runtime/application/domain layer.
4. **Shared data platform** - scoped source registrations, immutable source versions/payload identity, storage metadata and queued processing.
5. **Governed ingestion (ISI-22A-22E)** - versioned connector contracts -> versioned schema mappings -> incremental/idempotent ingestion -> normalized records -> record governance/dedup/quarantine/reconciliation -> operational policy for freshness/quality/backfill/replay/dead-letter -> immutable governed ingestion output.
6. **Reproducible analytical data boundary and governed domain consumption (ISI-22F/22G - CURRENT AS BUILT)** - governed output -> canonical analytical dataset contracts -> stable temporal/granularity keys -> explicit missing-value semantics -> reproducible dataset/snapshot/feature versions -> typed source-to-feature lineage and quality state; SIMPA/ORDO deterministic analytics consume explicitly bound and downstream-revalidated governed snapshots or eligible single-snapshot feature versions, while historical observation-derived runs remain read-only compatibility.
7. **Deterministic analytics** - indicators/statistics/ML own authoritative numerical truth, diagnostics, uncertainty, calibration and validated model outputs.
8. **Document AI/RAG** - extraction/retrieval with provenance and tenant/product namespace isolation.
9. **AI synthesis** - LLM/VLM is bounded explanation/synthesis through the shared AI HTTP boundary; it does not silently become numerical or state authority.
10. **Reporting - CURRENT AS BUILT** - deterministic persisted-data reporting uses the internal shared reporting service, SIMPA/ORDO reporting adapters and internal JSON/Markdown/HTML renderers; there is no active external document-conversion service.
11. **Runtime - CURRENT AS BUILT** - FastAPI + Streamlit + data-worker + ai-worker; data/AI jobs execute inline or through Redis/RQ; PostgreSQL and local/S3-compatible object storage hold durable state. There is no application-owned scheduler.
12. **Target production topology - TARGET, not current runtime proof** - shared central Nginx edge `central-ingress-nginx-1` (Compose project `central-ingress`, service `nginx`), PostgreSQL 17, Redis 7, MinIO/S3-compatible storage, ISI API/Streamlit/workers and bare-metal Ollama. ISI attaches through the external `isi_ingress` network using `isi-api` and `isi-streamlit`; the repository `isi-edge` service remains pre-cutover compatibility only. Any future scheduler or external document-conversion service requires an explicit named phase/ADR and cannot be inferred from this target.
13. **Deployment boundary** - current server, DNS, central Nginx route, real SMTP, production secrets/data and server Ollama remain frozen until owner-approved ISI-28. The owner-locked public endpoint is `https://isi.opus.rs:8445/`, alongside Krcuga `:8443` and OralScanXAI `:8444`; historical Caddy and `isi.rs:8443`/ISI-16 material is compatibility/history only and is not current execution authority.

Canonical data flow:

`External source -> DataSource -> connector contract -> schema mapping -> immutable DataSourceVersion/payload -> DataIngestionRun -> normalized records -> governance/dedup/quarantine -> operational freshness/quality/backfill/replay/DLQ -> immutable DataGovernedIngestionOutput -> reproducible analytical dataset/snapshot/feature + typed lineage -> deterministic statistics/ML -> SIMPA/ORDO bounded AI interpretation/reporting -> human review`

Once the reproducible analytical boundary exists, downstream statistics/ML/domain AI must consume governed reproducible analytical artifacts rather than bypassing governance and reading raw source bytes directly.

### 0.7 Canonical SYSTEM INVENTORY - complete product map

This inventory is the controlled bridge between the MasterPlan and the as-built repository. Its goal is that a new chat with only GitHub plus this MasterPlan can reconstruct the ISI product without relying on old conversation history.

**Inventory granularity rule.** One row represents a canonical architectural ownership unit: a customer-facing surface, service/boundary, model family/entity, job/worker mechanism, provider, report component, security authority, storage/deployment component, configuration family, integration, test authority, or legacy item. Individual methods/columns are owned by the canonical paths in the row and are not duplicated as separate rows unless they form an independently governed boundary. A new independently governed component requires a new inventory row in the same task that introduces it.

**Status vocabulary:** `CURRENT_AS_BUILT`, `DEVELOPMENT_ONLY`, `COMPATIBILITY`, `TARGET`, `PLANNED`, `HISTORICAL`, `SUPERSEDED`, `NOT_CONFIGURED`, `NOT_PRESENT`. `CURRENT_AS_BUILT` describes repository truth now; `TARGET`/`PLANNED` is not permission to treat the component as already deployed.

**Maintenance rule.** Every new chat/task must reconcile the relevant inventory rows against actual code and classify discrepancies as `DONE / PARTIAL / MISSING / DRIFT`. Every task that adds/removes/renames/re-owns a component updates the inventory in the same candidate. If a task has no inventory impact, its spec must state `Canonical system inventory impact: NONE` with evidence.

**Explicit cross-project exclusions.** ISI has no commercial payment/PayPal subsystem, no dedicated Vision service, no dedicated Audio service, no application-owned scheduler, and no active external document-conversion service. Entitlements are authorization, not billing. These absences are canonical until an explicit owner-approved ISI architecture change says otherwise.

**Deployment truth.** The final owner-approved shared edge is central Nginx `central-ingress-nginx-1` (Compose project `central-ingress`, service `nginx`). The owner target is `https://isi.opus.rs:8445/`, alongside Krcuga `:8443` and OralScanXAI `:8444`. ISI must integrate through `isi_ingress` using `isi-api` and `isi-streamlit`; `isi-edge` remains pre-cutover compatibility only. Older Caddy and `isi.rs:8443`/ISI-16 material is `LEGITIMATE_HISTORY`/`REQUIRED_COMPATIBILITY`, not current authority. Actual server/DNS/central-ingress mutation remains forbidden until fresh owner-approved ISI-28.

#### A. USER SURFACES

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-A01 | Public website | Web surface | CURRENT_AS_BUILT | src/public/**; src/public_content/**; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md | Public institutional content, product entry and published legal-page discovery | HTTP request; published content | HTML/assets | Public content models/service | Browser/users | PostgreSQL public content + static assets | Public-read boundary; draft preview guarded | YES | YES | tests/test_isi_04*.py; tests/test_isi_28_public_legal_links.py; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py; tests/test_isi_27a_public_help_contract.py | NONE | FOUNDATION / ISI-27 / ISI-28 | Replace only through approved public-site ADR/task; preserve content provenance; 27A Help preserved; ISI-28 candidate exposes published legal pages in localized footer/sitemap only; R2 adds owner-authorized visible-placeholder SR/EN payload and collision-safe publisher; four legal translations published under exact accepted 1bf0552; R3 header correction candidate only |
| INV-A02 | Login | Authenticated entry surface | CURRENT_AS_BUILT | src/streamlit_app/app.py; src/api/auth_routes.py; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md | Institutional account sign-in | Email; password | Session token + app context | Auth service | Authenticated shell | AuthSession in PostgreSQL | Rate-limited auth boundary; opaque bearer session | YES | YES | tests/test_isi_02b*.py; tests/test_isi_14*.py; tests/test_isi_20_auth_assurance.py; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py; tests/test_isi_27a_public_help_contract.py | NONE | ISI-20 / ISI-27 | May change only with auth/security contract and migration-safe session handling; 27A adds shared Help/presentation only, without changing runtime authority  R3 pending recovery notice/disabled send UI candidate; login and existing token confirmations preserved |
| INV-A03 | Invitation onboarding | Onboarding surface | CURRENT_AS_BUILT | src/api/auth_routes.py; src/platform/auth/service.py; src/platform/auth/delivery.py; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; src/streamlit_app/app.py; src/streamlit_app/api_client.py | Invitation-based account creation/join; no public self-registration | One-time invitation token; profile; password | User/membership/session | Administration invitation flow; SMTP/null delivery | Identity/access platform | User; Membership; Invitation; AuthSession | Single-use token; organization-scoped invitation | YES | YES | tests/test_isi_13_invitation_contract.py; tests/test_isi_15_invitation_contract.py; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py; tests/test_isi_27a_public_help_contract.py | NONE | ISI-13 / ISI-20 | Public self-signup must not be added without explicit product/security decision; 27A adds shared Help/presentation only, without changing runtime authority  R2 candidate supports explicit SMTP pending: new email-dependent requests unavailable, existing token confirmation preserved; no external delivery claim |
| INV-A04 | Email verification | Account security surface | CURRENT_AS_BUILT | src/api/auth_routes.py; src/platform/auth/delivery.py; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; src/streamlit_app/app.py; src/streamlit_app/api_client.py | Verify institutional email using one-time token | Email verification token | Verified account state | Auth service; delivery adapter | Authenticated access | AuthToken; User.email_verified_at | Enumeration-resistant request response; expiring token | YES | YES | tests/test_isi_14_auth_route_contract.py; tests/test_isi_15_delivery.py; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py; tests/test_isi_27a_public_help_contract.py | NONE | ISI-20 | Preserve one-time/expiry and anti-enumeration properties; 27A adds shared Help/presentation only, without changing runtime authority  R2 candidate supports explicit SMTP pending: new email-dependent requests unavailable, existing token confirmation preserved; no external delivery claim  R3 pending recovery notice/disabled send UI candidate; login and existing token confirmations preserved |
| INV-A05 | Password reset | Account recovery surface | CURRENT_AS_BUILT | src/api/auth_routes.py; src/platform/auth/service.py; src/platform/auth/delivery.py; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; src/streamlit_app/app.py; src/streamlit_app/api_client.py | Reset password via one-time token | Email; reset token; new password | Password update; session/security events | Auth delivery; security service | Login | AuthToken; User; SecurityEvent | Anti-enumeration; password policy; expiring token | YES | YES | tests/test_isi_02b_auth_service.py; tests/test_isi_20_auth_assurance.py; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py; tests/test_isi_27a_public_help_contract.py | NONE | ISI-20 | Must preserve password policy, revocation and audit behavior; 27A adds shared Help/presentation only, without changing runtime authority  R2 candidate supports explicit SMTP pending: new email-dependent requests unavailable, existing token confirmation preserved; no external delivery claim  R3 pending recovery notice/disabled send UI candidate; login and existing token confirmations preserved |
| INV-A06 | Authenticated app shell | Private application shell | CURRENT_AS_BUILT | src/streamlit_app/app.py; src/platform/app_shell/service.py; src/api/app_shell_routes.py; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md | Select organization/product/workspace and render authorized navigation | Session token; app context; permissions | Scoped navigation and workspace | App context + RBAC | All private workspaces | Session state only; backend data in PostgreSQL | Backend remains authorization truth; UI visibility is not authority | YES | YES | tests/test_isi_05*.py; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py; tests/test_isi_27a_public_help_contract.py | REQUIRED_COMPATIBILITY | FOUNDATION / ISI-23 / ISI-24 | Legacy integration markers may remain only while tested compatibility requires them; 27A adds shared Help/presentation only, without changing runtime authority  ISI-30A owner-authorized workflow-shell candidate, exact automation/specs/ISI-30A-WORKFLOW-SHELL.md; scope transitions/design and existing ORDO scenario reachability; no backend authority change. |
| INV-A07 | Overview workspace | Private surface | CURRENT_AS_BUILT | src/streamlit_app/app.py | Show active product/workspace foundation and access context | App shell context | Overview cards/status | Authenticated app shell | Data/AI/domain workspaces | No independent persistence | Organization/product/workspace scoped | YES | NO | tests/test_isi_05*.py | NONE | FOUNDATION | Replace only through shell UX task  ISI-30A owner-authorized workflow-shell candidate, exact automation/specs/ISI-30A-WORKFLOW-SHELL.md; scope transitions/design and existing ORDO scenario reachability; no backend authority change. |
| INV-A08 | Data workspace | Private surface | CURRENT_AS_BUILT | src/streamlit_app/data_workspace.py; src/streamlit_app/data_source_workspace.py; src/streamlit_app/data_ingestion_workspace.py; src/streamlit_app/data_ingestion_api.py; src/streamlit_app/data_analytical_workspace.py; src/streamlit_app/data_analytical_api.py; src/streamlit_app/data_operations_workspace.py; src/streamlit_app/data_operations_api.py; src/streamlit_app/data_governance_workspace.py; src/streamlit_app/data_governance_api.py; src/streamlit_app/data_privacy_workspace.py; src/streamlit_app/data_privacy_api.py; src/streamlit_app/data_api.py; src/api/data_routes.py; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md ; src/streamlit_app/extraction_workspace.py; docs/help/ISI-EXTRACTION-GUIDE.md | Source upload/registration, governance and data operations | Authorized data actions; source payloads | Data source/version/run/governance views | App shell; data platform | Analytical boundary; reports; AI eligibility | PostgreSQL + object storage | Requires data permissions and exact org/product/workspace scope | YES | YES | tests/test_isi_06*.py; tests/test_isi_21*.py; tests/test_isi_22*.py; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py; tests/test_isi_27a_public_help_contract.py ; tests/test_isi_29e_* | NONE | ISI-22 | 30B1 source/version quality and scoped ingestion inspection/retry candidate, docs/help/ISI-DATA-WORKFLOWS-GUIDE.md; Help/screens pending30E; no backend boundary change. 29E Data workspace extraction controls: src/streamlit_app/extraction_workspace.py, explicit source/create/cancel/review/retrieval and ten-item Help; exact candidate local/native/browser gates required before commit.  30D3A titled typed metrics/diagnostics/provenance/unsupported/source/SHAP evidence via src/streamlit_app/evidence_view.py; ISI-RESULT-EVIDENCE-GUIDE.md; chart/domain authority unchanged, optional technical GeoJSON retained; illustrations pending30E. |
| INV-A09 | AI workspace | Private surface | CURRENT_AS_BUILT | src/streamlit_app/ai_workspace.py; src/streamlit_app/ai_api.py; src/api/ai_routes.py | Submit/review bounded AI work | Scoped prompt/model/policy request | AI job/result/attempt/review state | App shell; AI service; eligible evidence | Human reviewer; reports/domain workflows | PostgreSQL AI registry/jobs/audit/embeddings | ai.run permission; policy and tenant/product namespace guards | YES | YES | tests/test_isi_07*.py; tests/test_isi_21c_ai_eligibility.py | NONE | ISI-25 | AI must remain bounded evidence synthesis; no silent numeric/state authority  30D2 src/streamlit_app/ai_governance_workspace.py; src/streamlit_app/evidence_view.py; ISI-AI-REVIEW-WORKFLOWS-GUIDE.md: scoped existing evaluation review/read/XAI, explicit local infrastructure diagnostic, optional reviewed-status/result precondition under lock; no promotion or invented XAI; illustrations pending30E. |
| INV-A10 | SIMPA indicators | Private domain surface | CURRENT_AS_BUILT | src/streamlit_app/simpa_workspace.py; src/api/simpa_routes.py | SIMPA indicator catalog/results with conceptual/draft/proposed/validated/retired summary state | SIMPA scoped data and methodology | Indicator views | SIMPA service; data platform | SIMPA analytics/reporting | SIMPA domain tables | SIMPA-only product/workspace permission scope | YES | YES | tests/test_isi_08*.py; tests/test_isi_23a_methodology_lifecycle.py | REQUIRED_COMPATIBILITY | ISI-23 | Historical conceptual rows remain; production methodology changes require proposed/reference-gated human approval |
| INV-A11 | SIMPA analytics | Private domain surface | CURRENT_AS_BUILT | src/streamlit_app/simpa_analytics_workspace.py; src/streamlit_app/simpa_methodology_workspace.py; src/streamlit_app/simpa_methodology_api.py; src/streamlit_app/simpa_analytics_api.py; src/api/simpa_analytics_routes.py; src/domains/simpa/statistical_xai.py | Evidence-first system analytics, methodology/reference provenance, deterministic statistical result presentation and faithful Help/XAI before bounded AI synthesis | Governed SIMPA data; validated target methodology; statistical contracts/results; methodology-owned reference suites | Analysis outputs, coefficient uncertainty/p-values where stored, fit/error diagnostics, calibration, XAI/provenance and safe human lifecycle trace | SIMPA analytics service | Reporting; later bounded AI interpretation | SIMPA analytics, reference-evidence and statistical contract/result tables | analysis.read for views; indicator.manage for methodology lifecycle; analysis.run for execution; SIMPA namespace; non-causal guard | YES | YES | tests/test_isi_09*.py; tests/test_isi_23a*.py; tests/test_isi_23b*.py; tests/test_isi_23c*.py; tests/test_isi_23d*.py | REQUIRED_COMPATIBILITY | ISI-23 | PROPOSED statistical contracts are controlled testing only; VALIDATED is human methodology approval, not champion/performance certification; unsupported XAI remains unavailable; no categorical prediction threshold or citizen-level automation;29D accepted95fec435 src/domains/simpa/attribution_service.py / src/streamlit_app/attribution_view.py, tests/test_isi_29d_*, local/native/browser and exact95fec435 CI passed  30C1 typed existing global methodology/suite/statistical authoring; indicator.manage, human approval and backend gates unchanged.  30D3A titled typed metrics/diagnostics/provenance/unsupported/source/SHAP evidence via src/streamlit_app/evidence_view.py; ISI-RESULT-EVIDENCE-GUIDE.md; chart/domain authority unchanged, optional technical GeoJSON retained; illustrations pending30E. |
| INV-A12 | ORDO indicators | Private domain surface | CURRENT_AS_BUILT | src/streamlit_app/ordo_workspace.py; src/api/ordo_routes.py; src/streamlit_app/ordo_help_workspace.py; docs/help/ORDO-USER-GUIDE.md | ORDO indicator/catalog workspace with complete ORDO-owned Help coverage | ORDO scoped data and methodology | Indicator views and faithful Help | ORDO service; data platform | ORDO analytics/scenarios/reporting | ORDO domain tables + repository Help | ORDO-only product/workspace permission scope | YES | YES | tests/test_isi_10*.py; tests/test_isi_24d_help_xai_contract.py | NONE | ISI-24 | Methodology changes require versioned human approval; Help never creates formulas or values |
| INV-A13 | ORDO analytics and scenarios | Private domain surface | CURRENT_AS_BUILT | src/streamlit_app/ordo_analytics_workspace.py; src/streamlit_app/ordo_analytics_api.py; src/api/ordo_analytics_routes.py; src/domains/ordo/analytics_xai.py; src/streamlit_app/ordo_help_workspace.py | Evidence-first analytics/scenario views plus governed time-series-spec lifecycle, explicit forecast execution, persisted forecast presentation and deterministic XAI | Governed ORDO data; scenario assumptions; validated time-series specification; discovered series identity; explicit candidate family and interval; persisted forecast/scenario truth | Analysis/scenario outputs, ESTIMATED/NOT_ESTIMATED forecast evidence, lifecycle trace and faithful interpretation | ORDO analytics service | Reporting; AI interpretation; human review | ORDO analytics tables; accepted 24B/24C persistence only | analysis.read for views/discovery; indicator.manage for spec lifecycle; analysis.run for execution; backend scope; forecast/scenario distinction | YES | YES | tests/test_isi_11*.py; tests/test_isi_24*.py | NONE | ISI-24 | Scenario must not be relabeled forecast; NOT_ESTIMATED remains nonnumeric; methodology authority is server-resolved; execution uses only validated spec + discovered identity + explicit family/interval; no automatic selection/fallback, causal claim or recommendation  ISI-30A owner-authorized workflow-shell candidate, exact automation/specs/ISI-30A-WORKFLOW-SHELL.md; scope transitions/design and existing ORDO scenario reachability; no backend authority change.  30C2A typed global ORDO method lifecycle and explicit scoped forecast authoring; contextual ORDO-METHODOLOGY-WORKFLOWS-GUIDE.md; action illustrations pending30E.  30C2B1 existing scoped identity aggregation execution and current GIS result revalidation; ORDO-SPATIAL-AGGREGATION-GUIDE.md; populated illustrations pending30E.  30C2B2 scoped metadata-only ORDO statistical specifications/lifecycle: src/streamlit_app/ordo_statistical_workspace.py; src/api/ordo_statistical_routes.py; src/domains/ordo/statistical_authoring.py; ORDO-STATISTICAL-SPECIFICATION-GUIDE.md; no fitting/results.  30D3A titled typed metrics/diagnostics/provenance/unsupported/source/SHAP evidence via src/streamlit_app/evidence_view.py; ISI-RESULT-EVIDENCE-GUIDE.md; chart/domain authority unchanged, optional technical GeoJSON retained; illustrations pending30E. |
| INV-A14 | Reporting workspace | Private surface | CURRENT_AS_BUILT | src/streamlit_app/reporting_workspace.py; src/streamlit_app/reporting_api.py; src/api/reporting_routes.py; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md ; src/platform/reporting/linked_evidence.py; src/domains/{simpa,ordo}/report_evidence.py; src/streamlit_app/linked_reporting_workspace.py; docs/help/ISI-LINKED-REPORTS-GUIDE.md | Create/review/publish/export reports | Scoped domain evidence and source manifest | Versioned report/export | Domain adapters; reporting service | Human review; download/delivery | Report/Version/Review/Export in PostgreSQL | report permissions; source-manifest scope/checksum validation | YES | YES | tests/test_isi_12*.py; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py; tests/test_isi_27a_public_help_contract.py ; tests/test_isi_29f_* | NONE | ISI-27 | 29F accepted software f587ed0: accepted claim/source/dated geometry and optional exact domain result/XAI; human contextual association; source/auth/integrity revalidated at read/lifecycle/export/download. Exact local/browser/manual/CI/signed release and scoped server gates PASS; full-production gates remain open.  30D3A titled typed metrics/diagnostics/provenance/unsupported/source/SHAP evidence via src/streamlit_app/evidence_view.py; ISI-RESULT-EVIDENCE-GUIDE.md; chart/domain authority unchanged, optional technical GeoJSON retained; illustrations pending30E.  30D3B existing report customer selections/confirmations and optional status/content/provenance preconditions serialized under scoped parent/version locks; ISI-REPORTING-WORKFLOWS-GUIDE.md; legacy caller compatibility and live linked revalidation retained. |
| INV-A15 | Administration workspace | Private admin surface | CURRENT_AS_BUILT | src/streamlit_app/administration_workspace.py; src/api/administration_routes.py; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md | Manage organization members/workspaces/entitlements/audit | Admin-authorized actions | Administrative state changes/audit | RBAC/access service | All scoped product work | PostgreSQL identity/access/admin audit | organization.manage/members.manage/workspace.manage/audit.read | YES | YES | tests/test_isi_13*.py; tests/test_isi_20_access_matrix.py; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py; tests/test_isi_27a_public_help_contract.py | NONE | ISI-20 / ISI-27 | No client-side-only admin authority; 27A adds shared Help/presentation only, without changing runtime authority  30D1 scoped snapshot/value-bound confirmations, safe204 receipts and existing member-session review/revocation GUI; src/streamlit_app/administration_api.py; ISI-ADMINISTRATION-WORKFLOWS-GUIDE.md; unchanged server RBAC/assurance/last-admin, populated illustrations pending30E. |
| INV-A16 | Account security workspace | Private security surface | CURRENT_AS_BUILT | src/streamlit_app/security_workspace.py; src/streamlit_app/security_api.py; src/api/auth_routes.py; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md | Session inventory/revocation and assurance controls | Authenticated session; password assurance | Revocation/security state | Auth/security services | Account/session security | AuthSession; SecurityEvent; MFA foundation | Self-account scope + step-up for sensitive actions | YES | YES | tests/test_isi_20_session_management.py; tests/test_isi_20_auth_assurance.py; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py; tests/test_isi_27a_public_help_contract.py | NONE | ISI-20 | Preserve self-scope and auditability; 27A adds shared Help/presentation only, without changing runtime authority  30D4 typed self-session inventory/UUID paths, fresh identity/status-bound individual/bulk confirmations and safe receipts; ISI-ACCOUNT-SECURITY-WORKFLOWS-GUIDE.md; existing password assurance/SMTP-pending/MFA boundaries retained, illustrations30E. |
| INV-A17 | Public self-registration | User surface | NOT_PRESENT | src/api/auth_routes.py; MasterPlan SYSTEM INVENTORY; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md | Make absence of public self-signup explicit; onboarding is invitation-only | Unauthenticated signup attempt | No registration surface | Public user | None | None | No public account-creation authority | YES | YES | tests/test_isi_13_invitation_contract.py; tests/test_isi_20_auth_assurance.py; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py; tests/test_isi_27a_public_help_contract.py | NONE | ISI-20 | May be introduced only by explicit owner-approved product/security architecture change; 27A adds shared Help/presentation only, without changing runtime authority |
| INV-A18 | SIMPA Help, User Guide and XAI interpretation | Help/XAI surface | CURRENT_AS_BUILT | src/streamlit_app/simpa_help_workspace.py; src/domains/simpa/statistical_xai.py; docs/help/SIMPA-USER-GUIDE.md; docs/help/ISI-HELP-COVERAGE-MATRIX.md ; src/streamlit_app/help_manual.py; docs/help/ISI-ILLUSTRATED-MANUAL.json; docs/help/screens/; docs/help/templates/ISI-MANUAL-TEMPLATE.docx; tools/docs/build_isi30f_desktop_manual.py; tools/docs/index_isi30f_manual.py | Complete SIMPA Help Coverage plus deterministic model/result interpretation for methodology, reference evidence, statistics and bounded AI provenance/review | Validated SIMPA methodology, implemented workflows and governed stored model/evidence outputs | In-app Help + User Guide + faithful XAI/provenance | ISI-23 methodology/UI; ISI-25 shared AI/XAI contracts | SIMPA users; ISI-27 acceptance | Repository Help/User Guide/matrix; no new DB persistence | Must not disclose unauthorized data or fabricate confidence/importance/causality; content matches actual model evidence | YES | YES | tests/test_isi_23d*.py | NONE | ISI-23 / ISI-25 / ISI-27 | Every material SIMPA action is VERIFIED in ISI-23D; shared AI evaluation/promotion/fallback uses accepted ISI-25  Owner-requested29F detailed illustrated Help: numbered workflow, field tables, dated truthful screen availability, local reviewed screenshots and product-scoped GIS/SHAP/extraction/linked-report guides. Public topic allowlist retained.  30C1 contextual SIMPA-METHODOLOGY-WORKFLOWS-GUIDE.md; populated action illustrations pending30E.  30D3A titled typed metrics/diagnostics/provenance/unsupported/source/SHAP evidence via src/streamlit_app/evidence_view.py; ISI-RESULT-EVIDENCE-GUIDE.md; chart/domain authority unchanged, optional technical GeoJSON retained; illustrations pending30E. |
| INV-A19 | ORDO Help, User Guide and XAI interpretation | Help/XAI surface | CURRENT_AS_BUILT | src/streamlit_app/ordo_help_workspace.py; src/domains/ordo/analytics_xai.py; docs/help/ORDO-USER-GUIDE.md; docs/help/ISI-HELP-COVERAGE-MATRIX.md ; src/streamlit_app/help_manual.py; docs/help/ISI-ILLUSTRATED-MANUAL.json; docs/help/screens/; docs/help/templates/ISI-MANUAL-TEMPLATE.docx; tools/docs/build_isi30f_desktop_manual.py; tools/docs/index_isi30f_manual.py | Complete ORDO-owned Help Coverage plus deterministic interpretation of scenario/forecast and the governed 24E specification/execution workflow, with bounded AI provenance/review | Validated ORDO methodology, implemented workflows and governed persisted model/evidence outputs | In-app Help + repository User Guide + faithful XAI/provenance | ISI-24 methodology/UI/workflow; ISI-25 shared AI/XAI contracts | ORDO users; ISI-27 acceptance | Repository Help/User Guide/matrix; no new Help persistence | Must preserve scenario-versus-forecast/NOT_ESTIMATED, authorization and non-causal/non-certainty safeguards; no fabricated values/confidence/importance | YES | YES | tests/test_isi_24d_help_xai_contract.py; tests/test_isi_24d_forecast_xai.py; tests/test_isi_24e_forecast_workflow_ui.py | NONE | ISI-24 / ISI-25 / ISI-27 | ORDO-owned Help/XAI and governed forecast-workflow coverage are VERIFIED through ISI-24E; shared AI evaluation/promotion/fallback uses accepted ISI-25 and ISI-27A supplies current shared Help/presentation authority while the 27D gate passed on its exact RC;29F exact f587ed0 software acceptance passed; fuller populated-action Help remains ISI-30E  Owner-requested29F detailed illustrated Help: numbered workflow, field tables, dated truthful screen availability, local reviewed screenshots and product-scoped GIS/SHAP/extraction/linked-report guides. Public topic allowlist retained.  30C2A typed global ORDO method lifecycle and explicit scoped forecast authoring; contextual ORDO-METHODOLOGY-WORKFLOWS-GUIDE.md; action illustrations pending30E.  30C2B1 existing scoped identity aggregation execution and current GIS result revalidation; ORDO-SPATIAL-AGGREGATION-GUIDE.md; populated illustrations pending30E.  30C2B2 scoped metadata-only ORDO statistical specifications/lifecycle: src/streamlit_app/ordo_statistical_workspace.py; src/api/ordo_statistical_routes.py; src/domains/ordo/statistical_authoring.py; ORDO-STATISTICAL-SPECIFICATION-GUIDE.md; no fitting/results.  30D3A titled typed metrics/diagnostics/provenance/unsupported/source/SHAP evidence via src/streamlit_app/evidence_view.py; ISI-RESULT-EVIDENCE-GUIDE.md; chart/domain authority unchanged, optional technical GeoJSON retained; illustrations pending30E. |
| INV-A20 | Commercial checkout/payment surface | User surface | NOT_PRESENT | MasterPlan SYSTEM INVENTORY | Make absence of checkout/subscription/payment UI explicit | Payment intent | No payment UI/output | Users | None | None | No payment authority in ISI | YES | NO | Inventory/policy guard | NONE | OUT_OF_SCOPE | Do not add by analogy with Krcuga/OralScan; requires explicit owner-approved ISI product change |
| INV-A21 | Cross-product Help Coverage Matrix | Help/XAI governance artifact | CURRENT_AS_BUILT | docs/help/ISI-HELP-COVERAGE-MATRIX.md; tests/test_isi_23d_help_xai_contract.py; tests/test_isi_24d_help_xai_contract.py; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md ; src/streamlit_app/help_manual.py; docs/help/ISI-ILLUSTRATED-MANUAL.json; docs/help/screens/; docs/help/templates/ISI-MANUAL-TEMPLATE.docx; tools/docs/build_isi30f_desktop_manual.py; tools/docs/index_isi30f_manual.py | Track Help/applicable XAI coverage for every customer-facing inventory row and material user action | Customer-facing inventory + implemented workflows + validated model/evidence contracts | MISSING/PARTIAL/COMPLETE/VERIFIED coverage state, canonical Help location and acceptance evidence | All user-facing SIMPA/ORDO/shared surfaces | ISI-23/24/25 domain completion; ISI-27 release acceptance | Repository-controlled documentation/test evidence | Must not leak unauthorized data; coverage cannot claim support absent from runtime/model evidence | YES | YES | tests/test_isi_23d_help_xai_contract.py; tests/test_isi_24d_help_xai_contract.py; tests/test_isi_25b_*; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py; tests/test_isi_27a_public_help_contract.py | NONE | ISI-23 / ISI-24 / ISI-25 / ISI-27 | Production-critical USER SURFACE Help coverage VERIFIED in the accepted ISI-27A implementation; A17 runtime NOT_PRESENT; the 27D gate passed on its exact RC;29F exact f587ed0 software acceptance passed; fuller populated-action Help remains ISI-30E  Owner-requested29F detailed illustrated Help: numbered workflow, field tables, dated truthful screen availability, local reviewed screenshots and product-scoped GIS/SHAP/extraction/linked-report guides. Public topic allowlist retained.  ISI-30A owner-authorized workflow-shell candidate, exact automation/specs/ISI-30A-WORKFLOW-SHELL.md; scope transitions/design and existing ORDO scenario reachability; no backend authority change.  30C1 contextual SIMPA-METHODOLOGY-WORKFLOWS-GUIDE.md; populated action illustrations pending30E.  30C2A typed global ORDO method lifecycle and explicit scoped forecast authoring; contextual ORDO-METHODOLOGY-WORKFLOWS-GUIDE.md; action illustrations pending30E.  30C2B1 existing scoped identity aggregation execution and current GIS result revalidation; ORDO-SPATIAL-AGGREGATION-GUIDE.md; populated illustrations pending30E.  30C2B2 scoped metadata-only ORDO statistical specifications/lifecycle: src/streamlit_app/ordo_statistical_workspace.py; src/api/ordo_statistical_routes.py; src/domains/ordo/statistical_authoring.py; ORDO-STATISTICAL-SPECIFICATION-GUIDE.md; no fitting/results.  30D1 scoped snapshot/value-bound confirmations, safe204 receipts and existing member-session review/revocation GUI; src/streamlit_app/administration_api.py; ISI-ADMINISTRATION-WORKFLOWS-GUIDE.md; unchanged server RBAC/assurance/last-admin, populated illustrations pending30E.  30D2 src/streamlit_app/ai_governance_workspace.py; src/streamlit_app/evidence_view.py; ISI-AI-REVIEW-WORKFLOWS-GUIDE.md: scoped existing evaluation review/read/XAI, explicit local infrastructure diagnostic, optional reviewed-status/result precondition under lock; no promotion or invented XAI; illustrations pending30E.  30D3A titled typed metrics/diagnostics/provenance/unsupported/source/SHAP evidence via src/streamlit_app/evidence_view.py; ISI-RESULT-EVIDENCE-GUIDE.md; chart/domain authority unchanged, optional technical GeoJSON retained; illustrations pending30E.  30D3B existing report customer selections/confirmations and optional status/content/provenance preconditions serialized under scoped parent/version locks; ISI-REPORTING-WORKFLOWS-GUIDE.md; legacy caller compatibility and live linked revalidation retained.  30D4 typed self-session inventory/UUID paths, fresh identity/status-bound individual/bulk confirmations and safe receipts; ISI-ACCOUNT-SECURITY-WORKFLOWS-GUIDE.md; existing password assurance/SMTP-pending/MFA boundaries retained, illustrations30E.  30E current illustrated workflow candidate:101 reviewed new synthetic assets,36 base topics/19 chapters; exact locked asset-plan/builders, private shared workflow selector, section-specific figures and current Word edition; public allowlist/product filtering/image identity guards preserved. Every-page Word and final acceptance pending. Owner correction 2026-10-12: authenticated SIMPA/ORDO Help and Word are desktop/laptop only; public landing retains mobile. Desktop index, bounded illustrations and replacement coverage governed by ISI-30F desktop correction; revision acceptance pending. |

#### B. DOMAIN / PLATFORM SERVICES

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-B01 | AppContextService | Platform service | CURRENT_AS_BUILT | src/platform/app_context/service.py | Resolve user organizations/products/workspaces and access context | User identity | Scoped app context | Identity/access/workspace models | App shell/API/UI | PostgreSQL | Membership/entitlement/RBAC scope | NO | YES | tests/test_isi_02c_context_service.py | NONE | FOUNDATION | Must remain backend truth for selectable context |
| INV-B02 | AppShellService | Platform service | CURRENT_AS_BUILT | src/platform/app_shell/service.py | Build permission-aware navigation/switcher | App context + selection | Shell response | AppContextService | Streamlit shell | None beyond source models | Permission-gated navigation; not authority by itself | NO | YES | tests/test_isi_05_app_shell_service.py | NONE | FOUNDATION | Update when customer-facing module inventory changes  ISI-30A owner-authorized workflow-shell candidate, exact automation/specs/ISI-30A-WORKFLOW-SHELL.md; scope transitions/design and existing ORDO scenario reachability; no backend authority change. |
| INV-B03 | AuthService | Platform service | CURRENT_AS_BUILT | src/platform/auth/service.py; src/platform/auth/security.py | Authenticate, sessions, tokens, reset, invitation acceptance | Credentials/tokens | Auth/session/account state | Identity models; security service | Auth routes/app shell | PostgreSQL auth tables | Credential/session security boundary | NO | YES | tests/test_isi_02b_auth_service.py; tests/test_isi_20_auth_assurance.py | NONE | ISI-20 | Security behavior cannot be weakened for convenience |
| INV-B04 | Access/RBAC service | Platform service | CURRENT_AS_BUILT | src/platform/access/service.py; src/platform/access/catalog.py | Resolve roles, permissions and product access | Membership/product/workspace/role data | Permission decisions | Identity/workspace/access models | All private APIs/services | PostgreSQL access tables | Central authorization boundary | NO | YES | tests/test_isi_02a_access_matrix.py; tests/test_isi_20_access_matrix.py | NONE | ISI-20 | No duplicate authorization implementation in UI/domain code |
| INV-B05 | AdministrationService | Platform service | CURRENT_AS_BUILT | src/platform/administration/service.py | Organization/member/workspace/access administration | Authorized admin actions | Managed records/audit | RBAC | Administration routes/UI | PostgreSQL | Admin permissions + org scope | NO | YES | tests/test_isi_13*.py | NONE | ISI-27 | Must remain tenant scoped and audited |
| INV-B06 | DataSourceService | Data service | CURRENT_AS_BUILT | src/platform/data/service.py | Register and manage scoped data sources/versions/uploads | Source metadata/payload | DataSource/DataSourceVersion/IngestionJob | Storage + access | Ingestion pipeline | PostgreSQL + object storage | Org/product/workspace + data permission scope | NO | YES | tests/test_isi_06*.py | NONE | ISI-22 | All external analytical data enters through governed source boundary |
| INV-B07 | ConnectorContractService | Data service | CURRENT_AS_BUILT | src/platform/data/connector_service.py | Version connector contracts and reference connector behavior | Connector definitions | Pinned connector contract versions | DataSource | Schema mapping/ingestion | PostgreSQL | Scoped source + governance authority | NO | YES | tests/test_isi_22a_connector_contracts.py | NONE | ISI-22 | Connector changes require new version; never mutate historical contract meaning |
| INV-B08 | SchemaMappingService | Data service | CURRENT_AS_BUILT | src/platform/data/schema_mapping_service.py | Version source-to-canonical schema mappings | Source schema + mapping contract | Pinned mapping version | Connector contract | Ingestion run | PostgreSQL | Scoped data governance boundary | NO | YES | tests/test_isi_22b_schema_mapping_contracts.py | NONE | ISI-22 | Mapping semantics are versioned and reproducible |
| INV-B09 | IngestionRunService | Data service | CURRENT_AS_BUILT | src/platform/data/ingestion_run_service.py | Create/idempotently resolve incremental ingestion runs | Pinned source/connector/mapping + cursor/request | DataIngestionRun + payload identity | Source/version/contracts | Worker ingestion | PostgreSQL + object storage | Scoped source; immutable request fingerprint | NO | YES | tests/test_isi_22c_ingestion_runs.py | NONE | ISI-22 | Preserve idempotency/fingerprint and forward-cursor invariants |
| INV-B10 | RecordGovernanceService | Data service | CURRENT_AS_BUILT | src/platform/data/record_governance_service.py; src/platform/data/governance.py | Entity resolution, deduplication, quarantine, reconciliation | Normalized records + governance policy | Accepted/quarantined/reconciled records | Ingestion mapping | Governed output | PostgreSQL | Scoped governance permissions; immutable evidence | NO | YES | tests/test_isi_22d_record_governance.py | NONE | ISI-22 | Do not bypass quarantine/reconciliation for downstream analytics 30B4B optional reviewed-current accepted-record ID guards adjudication under existing lock; historical omission compatibility retained. |
| INV-B11 | IngestionOperationsService | Data service | CURRENT_AS_BUILT | src/platform/data/ingestion_operations_service.py | Freshness, quality, backfill, replay, dead-letter, governed output | Technically complete ingestion run + operational policy | Evaluation/dead-letter/governed output/cursor decision | Record governance | Analytical boundary | PostgreSQL | data.governance.manage where required; scoped output | NO | YES | tests/test_isi_22e_ingestion_operations.py; tests/test_isi_22e_cursor_stability.py | NONE | ISI-22 | Replay/backfill never silently advance forward cursor |
| INV-B12 | PrivacyService | Data governance service | CURRENT_AS_BUILT | src/platform/data/privacy_service.py | Retention, purge/anonymization, privacy/export governance | Governed records/source metadata/policy | Retention/anonymization/invalidation/export manifests | Data governance | Analytics/exports | PostgreSQL + object storage metadata | Sensitivity/privacy/AI-use policy boundary | NO | YES | tests/test_isi_21b_retention_privacy.py; tests/test_isi_21b_export_governance.py | NONE | ISI-21 | Privacy policy must propagate to derivatives 30B4C bounded governance-only anonymization evidence listing/review row lock; customer retention/hold/export; physical purge remains operator-only. |
| INV-B13 | AnalyticalDataService | Data analytics foundation | CURRENT_AS_BUILT | src/platform/data/analytical_service.py | Manage versioned analytical dataset contracts, governed-output snapshots, immutable record membership, features, lineage and quality | Governed ingestion outputs and methodology versions | Reproducible analytical snapshot/feature contracts | Governed ingestion | SIMPA/ORDO deterministic analytics | PostgreSQL | Tenant/product/workspace + classification/privacy/AI policy | NO | YES | tests/test_isi_21c_analytical_governance.py; tests/test_isi_21c_lineage_feature_registry.py; tests/test_isi_22f*.py | REQUIRED_COMPATIBILITY | ISI-22 | Historical source-version lineage remains read-only; all new snapshots require governed outputs |
| INV-B14 | AIService + MLOps governance/evaluation runtime | AI service | CURRENT_AS_BUILT | src/platform/ai/service.py; src/platform/ai/governance.py; src/platform/ai/evaluation.py; src/platform/ai/promotion.py; src/platform/ai/monitoring.py; src/platform/ai/xai.py | Register runtime policies/models/prompts; preserve legacy selected-model-only jobs; execute exact-registration-bound governed fallback; persist evaluation, thresholds, promotion/rollback, circuit, drift and shared AI XAI evidence | Scoped evidence; prompt/model/policy request; governed registration/evaluation/promotion request | AIJob/attempt/output/review plus registry/dataset/run/result/review/promotion/runtime/drift evidence | AI gateway; access/data eligibility | AI workspace/domain synthesis and shared AI inspection/XAI | PostgreSQL | ai.run; platform-admin-only shared mutation after scope resolution; analysis.read/run; report.publish review write; data eligibility/product namespace/policy | NO | YES | tests/test_isi_07*.py; tests/test_isi_21c_ai_eligibility.py; tests/test_isi_25a*.py; tests/test_isi_25b*.py | NONE | ISI-25 | 25B is governance/runtime only: no numerical-authority transfer to LLM/VLM, no automatic model installation/deployment, no silent promotion/rollback and no online learning  30D2 src/streamlit_app/ai_governance_workspace.py; src/streamlit_app/evidence_view.py; ISI-AI-REVIEW-WORKFLOWS-GUIDE.md: scoped existing evaluation review/read/XAI, explicit local infrastructure diagnostic, optional reviewed-status/result precondition under lock; no promotion or invented XAI; illustrations pending30E. |
| INV-B15 | AIGateway | AI provider boundary | CURRENT_AS_BUILT | src/platform/ai/gateway.py; src/platform/ai/providers.py | Resolve allowed provider and invoke HTTP/local adapter | Model/provider config; request | Provider response/error | AIService; Settings | AI worker | Provider external runtime; attempts in PostgreSQL | Provider allowlist and production stub guard | NO | YES | tests/test_isi_07_provider_stub.py; tests/test_isi_07_policy.py | NONE | ISI-25 | New provider requires explicit adapter/policy/evaluation  R3 optional ISI request thread bound preserves default payload and provider/policy/model ownership; native deployed readiness still pending |
| INV-B16 | Knowledge registry | Knowledge/RAG foundation | CURRENT_AS_BUILT | src/knowledge/models.py; src/knowledge/seed.py | Register governed knowledge domains/sources/provenance and RAG eligibility | Knowledge metadata/source URI/content hash | KnowledgeDomain/Source/links | Institutional source curation | AI/RAG future/current consumers | PostgreSQL | Public vs organization scope; product scope; sensitivity/review state | NO | YES | tests/test_isi_04b_model_registry_bootstrap.py; tests/test_isi_07_namespaces.py | NONE | ISI-25 | Live external research retrieval is not implied by source metadata |
| INV-B17 | SIMPAService | Domain service | CURRENT_AS_BUILT | src/domains/simpa/service.py; src/domains/simpa/catalog.py | SIMPA domain entities and indicators | SIMPA scoped governed data/methodology | Domain records/indicator results | Data platform | SIMPA analytics/reporting | SIMPA tables | SIMPA product/workspace permissions | NO | YES | tests/test_isi_08*.py | NONE | ISI-23 | No citizen-level eligibility/diagnosis/punitive automation |
| INV-B18 | SIMPAAnalyticsService | Domain analytics service | CURRENT_AS_BUILT | src/domains/simpa/analytics_service.py; src/domains/simpa/methodology_contracts.py; src/domains/simpa/reference_calculations.py; src/domains/simpa/statistical_contracts.py; src/domains/simpa/statistical_models.py | Governed analytics, direct-observation methodology/reference lifecycle, global target-bound statistical methodology lifecycle and deterministic OLS/Poisson/binomial/fractional execution | Governed SIMPA snapshot/single-snapshot feature; validated target methodology; proposed/validated statistical contract | Indicator evidence plus immutable statistical coefficients, uncertainty, diagnostics/calibration and reproducibility fingerprints | AnalyticalDataService | UI/reporting; AI remains evidence-quality-only until a later bounded integration | SIMPA analytics, reference-evidence and statistical contract/result tables | SIMPA namespace + analysis permissions; indicator.manage lifecycle; analysis.run execution; every run revalidates governed binding; non-causal aggregate-only contract | NO | YES | tests/test_isi_09*.py; tests/test_isi_22g*.py; tests/test_isi_23a*.py; tests/test_isi_23b*.py; tests/test_isi_23c*.py | REQUIRED_COMPATIBILITY | ISI-22 / ISI-23 | Historical evidence/runs remain compatibility; unsupported target semantics fail closed; Accepted ISI-25 champion/eval/promotion and statistical-to-AI synthesis remain governed separately |
| INV-B19 | ORDOService | Domain service | CURRENT_AS_BUILT | src/domains/ordo/service.py; src/domains/ordo/catalog.py | ORDO domain entities and indicators | ORDO governed data/methodology | Domain records/indicator results | Data platform | ORDO analytics/reporting | ORDO tables | ORDO product/workspace permissions | NO | YES | tests/test_isi_10*.py | NONE | ISI-24 | Maintain ORDO domain isolation |
| INV-B20 | ORDOAnalyticsService | Domain analytics service | CURRENT_AS_BUILT | src/domains/ordo/analytics_service.py | Governed analytics, explicit forecast execution and evidence-only scenarios over exactly bound reproducible artifacts | Governed ORDO snapshot/single-snapshot feature; validated methodology/specification; explicit series identity/family/interval; scenario assumptions | Analyses/forecast outcomes/scenarios with normalized-record trace and stable NOT_ESTIMATED semantics | AnalyticalDataService | Reporting; AI synthesis; accepted 24D/24E presentation/Help/XAI | ORDO analytics tables | ORDO namespace + analysis.run/read permissions; governed binding revalidated downstream; scenario remains non-forecast | NO | YES | tests/test_isi_11*.py; tests/test_isi_22g*.py; tests/test_isi_24a*.py; tests/test_isi_24b*.py; tests/test_isi_24c*.py | REQUIRED_COMPATIBILITY | ISI-22 / ISI-24 | Historical observation/scenario truth remains readable; forecast requires a validated bound spec and supports only explicitly governed 24C execution families; scenario impact remains NOT_ESTIMATED without an approved response model |
| INV-B21 | SIMPA reporting adapter | Domain adapter | CURRENT_AS_BUILT | src/domains/simpa/reporting_adapter.py ; src/platform/reporting/linked_evidence.py; src/domains/{simpa,ordo}/report_evidence.py; src/streamlit_app/linked_reporting_workspace.py; docs/help/ISI-LINKED-REPORTS-GUIDE.md | Translate SIMPA evidence to shared reporting contract | SIMPA persisted outputs | Report content + source manifest | SIMPA domain/analytics | ReportingService | No independent persistence | SIMPA scope preserved in manifest | NO | YES | tests/test_isi_12*.py ; tests/test_isi_29f_* | NONE | ISI-23 / ISI-27 | 29F accepted software f587ed0: accepted claim/source/dated geometry and optional exact domain result/XAI; human contextual association; source/auth/integrity revalidated at read/lifecycle/export/download. Exact local/browser/manual/CI/signed release and scoped server gates PASS; full-production gates remain open. |
| INV-B22 | ORDO reporting adapter | Domain adapter | CURRENT_AS_BUILT | src/domains/ordo/reporting_adapter.py ; src/platform/reporting/linked_evidence.py; src/domains/{simpa,ordo}/report_evidence.py; src/streamlit_app/linked_reporting_workspace.py; docs/help/ISI-LINKED-REPORTS-GUIDE.md | Translate ORDO evidence to shared reporting contract | ORDO persisted outputs | Report content + source manifest | ORDO domain/analytics | ReportingService | No independent persistence | ORDO scope preserved in manifest | NO | YES | tests/test_isi_12*.py ; tests/test_isi_29f_* | NONE | ISI-24 / ISI-27 | 29F accepted software f587ed0: accepted claim/source/dated geometry and optional exact domain result/XAI; human contextual association; source/auth/integrity revalidated at read/lifecycle/export/download. Exact local/browser/manual/CI/signed release and scoped server gates PASS; full-production gates remain open. |
| INV-B23 | ReportingService | Platform service | CURRENT_AS_BUILT | src/platform/reporting/service.py ; src/platform/reporting/linked_evidence.py; src/domains/{simpa,ordo}/report_evidence.py; src/streamlit_app/linked_reporting_workspace.py; docs/help/ISI-LINKED-REPORTS-GUIDE.md | Version, review, publish and export deterministic reports | Content + provenance manifest | Report/version/review/export | Domain adapters | Reporting API/UI | PostgreSQL | Org/workspace/product checksums and report permissions | NO | YES | tests/test_isi_12*.py ; tests/test_isi_29f_* | NONE | ISI-27 | 29F accepted software f587ed0: accepted claim/source/dated geometry and optional exact domain result/XAI; human contextual association; source/auth/integrity revalidated at read/lifecycle/export/download. Exact local/browser/manual/CI/signed release and scoped server gates PASS; full-production gates remain open. |
| INV-B24 | SecurityService | Security service | CURRENT_AS_BUILT | src/platform/security/service.py; src/platform/security/models.py | Login throttling, security event capture and client metadata hashing | Auth/security events | Rate-limit decisions + SecurityEvent | Auth routes | Security audit/admin | PostgreSQL | Identifier/IP/UA hashing and rate-limit boundary | NO | YES | tests/test_isi_14_rate_limit_contract.py; tests/test_isi_20_security_events.py | NONE | ISI-20 | Do not log raw sensitive identifiers when hash is required |
| INV-B25 | ObservabilityService | Operations service | CURRENT_AS_BUILT | src/platform/observability/**; src/api/diagnostics_routes.py | Metrics/diagnostics/readiness instrumentation | Runtime events/queue/provider/db health | Metrics/diagnostics | All runtime services | Operators/CI | Process metrics/logs; selected persisted evidence | Diagnostics must not expose secrets/sensitive payloads | NO | YES | tests/test_isi_18_observability.py; tests/test_isi_18_readiness.py | NONE | ISI-18 / ISI-26 | Extend with new critical subsystem metrics in same task |
| INV-B26 | RecoveryService | Operations service | CURRENT_AS_BUILT | src/platform/recovery/**; tools/server/backup_restore_rehearsal.sh | Backup/restore/recovery metadata and rehearsal support | DB/object-storage backup inputs | Recovery evidence/restored state | PostgreSQL/object storage | Operators/ISI-28 | Backup artifacts/evidence | Privileged operations; server execution frozen until ISI-28 | NO | YES | tests/test_isi_19*.py | REQUIRED_COMPATIBILITY | ISI-19 / ISI-28 | Keep until replaced by tested production recovery mechanism |
| INV-B27 | PublicContentService | Public content service | CURRENT_AS_BUILT | src/public_content/**; src/public/** | Serve/manage migrated institutional public content | Published content records/assets | Public pages | Public migration/content data | Public website | PostgreSQL + assets | Public vs draft preview boundary | NO | YES | tests/test_isi_04*.py | NONE | FOUNDATION | Preserve publication/draft safety |
| INV-B28 | PublicMigrationToolset | Migration support service | COMPATIBILITY | src/public_migration/**; tools/staging/probe_legacy_migration_artifacts.py | Inventory/snapshot/import/redirect validation for legacy public content | Legacy site snapshots/manifests | Imported content/provenance/redirect evidence | Legacy source material | PublicContentService | Migration artifacts + PostgreSQL | Offline/read-only safety until explicit migration action | NO | NO | tests/test_isi_03*.py; tests/test_isi_15_legacy_migration_contract.py | LEGITIMATE_HISTORY | FOUNDATION / ISI-28 | Remove only after public-content provenance/recovery no longer depends on it and owner approves |

#### C. DATA MODEL

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-C01 | User | Identity entity | CURRENT_AS_BUILT | src/platform/identity/models.py | Institutional user identity | Invitation/admin creation | User identity | Auth/onboarding | Membership/AuthSession | PostgreSQL core_users | Global identity; authorization derived separately | NO | YES | tests/test_isi_02a_models.py; tests/test_isi_20*.py | NONE | ISI-20 | Schema change requires migration and auth/access compatibility |
| INV-C02 | Organization | Tenant entity | CURRENT_AS_BUILT | src/platform/identity/models.py | Tenant/institution boundary | Admin provisioning | Organization scope | Platform admin | Membership/workspace/entitlement | PostgreSQL core_organizations | Primary tenant isolation boundary | NO | YES | tests/test_isi_02a_models.py; tests/test_isi_20_access_matrix.py | NONE | ISI-20 | Never merge tenant data implicitly |
| INV-C03 | Membership | Tenant membership entity | CURRENT_AS_BUILT | src/platform/identity/models.py | Link user to organization with state | User + organization | Membership identity | Identity/admin | Access/workspace/domain services | PostgreSQL core_memberships | Tenant membership boundary | NO | YES | tests/test_isi_02a_access_matrix.py | NONE | ISI-20 | State/role changes must be audited and scoped |
| INV-C04 | Workspace | Scope entity | CURRENT_AS_BUILT | src/platform/workspaces/models.py | Product work context inside organization | Organization + product | Workspace scope | Administration | All domain/data operations | PostgreSQL core_workspaces | Organization/product/workspace isolation | NO | YES | tests/test_isi_05*.py; tests/test_isi_13*.py | NONE | FOUNDATION | Workspace bypass is forbidden |
| INV-C05 | Product | Access entity | CURRENT_AS_BUILT | src/platform/access/models.py; src/platform/access/catalog.py | Canonical product code catalog | Seed/config | SIMPA/ORDO product identity | Platform bootstrap | Entitlements/roles/workspaces | PostgreSQL core_products | Only SIMPA and ORDO allowed | NO | YES | tests/test_isi_02a_access_matrix.py | NONE | FOUNDATION | COSMOS/new product requires explicit owner architecture decision |
| INV-C06 | OrganizationEntitlement | Access entity | CURRENT_AS_BUILT | src/platform/access/models.py | Organization-level product entitlement | Organization + product | Allowed product access | Administration | Membership product access/app context | PostgreSQL | Organization/product boundary | NO | YES | tests/test_isi_02a_access_matrix.py | NONE | ISI-20 | This is authorization, not payment/billing |
| INV-C07 | MembershipProductAccess | Access entity | CURRENT_AS_BUILT | src/platform/access/models.py | Per-membership product activation | Membership + entitlement | Product access | Administration | Role assignments/app context | PostgreSQL | Membership/product boundary | NO | YES | tests/test_isi_02a_access_matrix.py | NONE | ISI-20 | This is authorization, not payment/billing |
| INV-C08 | Role/Permission/Assignments | RBAC entities | CURRENT_AS_BUILT | src/platform/access/models.py; src/platform/access/catalog.py | Versionless canonical RBAC mapping and scoped role assignment | Roles; permissions; membership/product/workspace | Permission decisions | Administration/access catalog | All protected operations | PostgreSQL | Central RBAC boundary | NO | YES | tests/test_isi_20_access_matrix.py | NONE | ISI-20 | No parallel permission taxonomy |
| INV-C09 | AuthSession/AuthToken/Invitation/MFA | Auth entities | CURRENT_AS_BUILT | src/platform/auth/models.py | Session, one-time token, invitation and MFA foundation state | Auth operations | Security/auth state | AuthService | Protected API | PostgreSQL | Secret/token/session lifecycle boundary | NO | YES | tests/test_isi_20_session_management.py; tests/test_isi_20_mfa_challenge_foundation.py | NONE | ISI-20 | Preserve expiry/revocation/single-use constraints |
| INV-C10 | DataSource | Data entity | CURRENT_AS_BUILT | src/platform/data/models.py | Registered scoped external/internal data source | Org/product/workspace + metadata | Source identity | DataSourceService | Connector/version/ingestion | PostgreSQL | Tenant/product/workspace + classification/privacy policy | NO | YES | tests/test_isi_06*.py; tests/test_isi_21*.py | NONE | ISI-22 | All analytical source lineage starts here |
| INV-C11 | Connector/Mapping/Governance/Operational policy versions | Versioned contract entities | CURRENT_AS_BUILT | src/platform/data/models.py | Pin ingestion semantics and policies by version | Definitions/policies | Immutable version IDs | DataSource | Ingestion/governance/ops | PostgreSQL | Scoped governance authority | NO | YES | tests/test_isi_22a*.py; tests/test_isi_22b*.py; tests/test_isi_22d*.py; tests/test_isi_22e*.py | NONE | ISI-22 | Never rewrite historical semantic version in place |
| INV-C12 | DataSourceVersion | Immutable source version entity | CURRENT_AS_BUILT | src/platform/data/models.py | Immutable payload/version/provenance identity | Source payload + metadata | Version/fingerprint/storage key | DataSourceService/storage | Ingestion/analytics lineage | PostgreSQL + object storage | Classification/privacy/AI-use policy travels with source | NO | YES | tests/test_isi_06*.py; tests/test_isi_21*.py | NONE | ISI-22 | Content identity is immutable |
| INV-C13 | IngestionJob | Job entity | CURRENT_AS_BUILT | src/platform/data/models.py | Queued/running/succeeded/failed execution record | Source version | Worker job state | Data queue | Data worker | PostgreSQL | Scoped job + backend ID | NO | YES | tests/test_isi_06_ingestion.py | NONE | ISI-22 | Do not conflate with DataIngestionRun semantic identity |
| INV-C14 | DataIngestionRun | Ingestion entity | CURRENT_AS_BUILT | src/platform/data/models.py | Idempotent incremental/backfill/replay run identity | Pinned contracts/payload/window/cursor | Run status/results/fingerprint | IngestionRunService | Governance/operations | PostgreSQL | Scoped; one live run/source; immutable request identity | NO | YES | tests/test_isi_22c_ingestion_runs.py; tests/test_isi_22e*.py | NONE | ISI-22 | Preserve request fingerprint and cursor semantics |
| INV-C15 | Normalized record / entity / quarantine / reconciliation | Governance entities | CURRENT_AS_BUILT | src/platform/data/models.py | Record-level normalized evidence, entity linking, quarantine and decisions | Mapped records/governance policy | Accepted/quarantined/reconciled record state | DataIngestionRun | Governed output | PostgreSQL | Scoped governance and reviewer identity | NO | YES | tests/test_isi_22d_record_governance.py | NONE | ISI-22 | Quarantined evidence cannot silently become accepted |
| INV-C16 | DataQualityResult/DataAuditEvent | Governance evidence entities | CURRENT_AS_BUILT | src/platform/data/models.py | Persist quality checks and data audit events | Data versions/operations | Quality/audit evidence | Data/governance services | Ops/analytics/reporting | PostgreSQL | Scoped audit; no cross-tenant leak | NO | YES | tests/test_isi_21*.py; tests/test_isi_22e*.py | NONE | ISI-22 | Retain traceability required by policy |
| INV-C17 | IngestionEvaluation/DeadLetter/GovernedOutput | Operational ingestion entities | CURRENT_AS_BUILT | src/platform/data/models.py | Persist freshness/quality decision, dead letter and immutable governed output | Completed runs + operational policy | Accepted/rejected/DLQ/governed output | IngestionOperationsService | Analytical boundary | PostgreSQL | Scoped operational governance | NO | YES | tests/test_isi_22e_ingestion_operations.py | NONE | ISI-22 | Governed output is downstream handoff; DLQ history is retained |
| INV-C18 | Retention/Anonymization/Invalidation/Export entities | Privacy governance entities | CURRENT_AS_BUILT | src/platform/data/models.py | Retention state, anonymization proof, invalidation and export manifests | Governance/privacy actions | Privacy/export evidence | PrivacyService | Exports/analytics invalidation | PostgreSQL | Sensitivity/privacy/purpose boundary | NO | YES | tests/test_isi_21b*.py | NONE | ISI-21 | Derived data must respect invalidation/privacy state |
| INV-C19 | AnalyticalDataset/AnalyticalDatasetContractVersion/AnalyticalDatasetSnapshot/AnalyticalSnapshotGovernedOutput/AnalyticalSnapshotRecordInput | Analytical contract and evidence entities | CURRENT_AS_BUILT | src/platform/data/models.py | Version canonical fields, temporal/granularity/missing semantics and pin governed-output plus exact normalized-record snapshot membership | Governed ingestion outputs + active dataset contract + methodology | Independently interpretable snapshot/fingerprint/quality/lineage | AnalyticalDataService | Features/SIMPA/ORDO analytics | PostgreSQL | Classification/privacy/AI-use + tenant/product/workspace; immutable evidence edges | NO | YES | tests/test_isi_21c_analytical_governance.py; tests/test_isi_22f*.py | REQUIRED_COMPATIBILITY | ISI-22 | Legacy source-version snapshot edges remain readable but cannot authorize new promotion; contract and membership history is immutable |
| INV-C20 | AnalyticalFeature/FeatureVersion/lineage quality | Analytical entities | CURRENT_AS_BUILT | src/platform/data/models.py | Versioned features with governed snapshot contract and quality propagation | Governed reproducible snapshot lineage + methodology | Feature versions/quality | AnalyticalDataService | Deterministic analytics/AI eligibility | PostgreSQL | Governed feature-purpose/privacy boundary | NO | YES | tests/test_isi_21c_lineage_feature_registry.py; tests/test_isi_22f_governed_lineage.py | REQUIRED_COMPATIBILITY | ISI-22 | Existing versions remain readable; new governance/freeze requires governed-output snapshot lineage |
| INV-C21 | AIModel/AIPrompt/AIPromptVersion/AIPolicyProfile | AI registry entities | CURRENT_AS_BUILT | src/platform/ai/models.py | Model/prompt/policy registry and pinned execution contract | Admin/bootstrap config | Versioned AI configuration | AIService | AI jobs/gateway | PostgreSQL | Product/policy/provider restrictions | NO | YES | tests/test_isi_07_models_contract.py; tests/test_isi_07_policy.py | NONE | ISI-25 | Promotion requires evaluation/approval and rollback identity |
| INV-C22 | AIJob/AIJobAttempt/AIAuditEvent | AI execution entities | CURRENT_AS_BUILT | src/platform/ai/models.py | Persist AI request lifecycle/provider attempts/audit/review | Scoped AI request | Job/attempt/audit state | AIService/queue | Human review/domain consumers | PostgreSQL | Tenant/product/policy + human review traceability | NO | YES | tests/test_isi_07*.py | NONE | ISI-25 | Attempts are evidence; do not erase fallback/failure history |
| INV-C23 | AIEmbedding | Embedding entity | CURRENT_AS_BUILT | src/platform/ai/models.py | Persist namespace-scoped embedding metadata/vector | Eligible text/evidence | Embedding record | AI/knowledge layer | RAG/retrieval | PostgreSQL JSON vector; optional pgvector capability | Tenant/product/private namespace isolation | NO | YES | tests/test_isi_07_namespaces.py | NONE | ISI-25 | Dedicated multilingual embedding evaluation required before production promotion |
| INV-C24 | KnowledgeDomain/KnowledgeSource/KnowledgeSourceDomain | Knowledge entities | CURRENT_AS_BUILT | src/knowledge/models.py | Govern knowledge scope, authority, review, sensitivity and provenance | Curated source metadata/content hashes | RAG-eligible governed knowledge graph | Knowledge registry | AI/RAG | PostgreSQL | PUBLIC vs ORGANIZATION; product scope; sensitivity/review | NO | YES | tests/test_isi_07_namespaces.py | NONE | ISI-25 | External URI is provenance metadata, not permission for live fetch |
| INV-C25 | SIMPA domain model family | Domain entities | CURRENT_AS_BUILT | src/domains/simpa/models.py | SIMPA indicator/methodology/monitoring persistence including five-state indicator summary | SIMPA inputs | Domain state | SIMPAService | SIMPA analytics/reporting | PostgreSQL SIMPA tables | SIMPA product/workspace isolation | NO | YES | tests/test_isi_08*.py; tests/test_isi_23a_methodology_lifecycle.py | REQUIRED_COMPATIBILITY | ISI-23 | Historical conceptual rows are not bulk rewritten; validated summary has priority over draft/proposed successors |
| INV-C26 | SIMPA analytics model family | Analytics entities | CURRENT_AS_BUILT | src/domains/simpa/analytics_models.py; src/domains/simpa/methodology_contracts.py; src/domains/simpa/reference_calculations.py; src/domains/simpa/statistical_contracts.py; src/domains/simpa/statistical_models.py | SIMPA analytical run/result metadata plus typed indicator/statistical methodology contracts, immutable evidence and deterministic numerical authority | Governed analytical data and exact methodology/reference/statistical contract identity | Reproducible indicator and statistical lifecycle/execution evidence | SIMPAAnalyticsService | UI/reporting; later explicitly bounded AI integration | PostgreSQL SIMPA analytics tables | SIMPA scope; aggregate-only/non-causal statistical authority; membership trace FKs | NO | YES | tests/test_isi_09*.py; tests/test_isi_22g*.py; tests/test_isi_23a*.py; tests/test_isi_23b*.py; tests/test_isi_23c*.py | REQUIRED_COMPATIBILITY | ISI-22 / ISI-23 | Historical methodologies/results remain readable without false backfill; statistical results never overwrite indicator results or authorize thresholds/classes |
| INV-C27 | ORDO domain model family | Domain entities | CURRENT_AS_BUILT | src/domains/ordo/models.py | ORDO indicator/methodology/scenario domain persistence | ORDO inputs | Domain state | ORDOService | ORDO analytics/reporting | PostgreSQL ORDO tables | ORDO product/workspace isolation | NO | YES | tests/test_isi_10*.py | NONE | ISI-24 | Methodology fields require explicit human validation |
| INV-C28 | ORDO analytics model family | Analytics entities | CURRENT_AS_BUILT | src/domains/ordo/analytics_models.py; src/domains/ordo/spatial_processing.py; src/domains/ordo/statistical_contracts.py; src/domains/ordo/time_series_contracts.py; migrations/versions/20260916_0030_ordo_governed_evidence_gis_contracts.py; migrations/versions/20260916_0031_ordo_spatial_statistical_temporal_contracts.py; migrations/versions/20260916_0032_ordo_forecast_backtest_uncertainty.py | ORDO analyses/scenarios with governed artifact/contract/quality binding, corrected human methodology lifecycle, persisted non-forecast scenario contract with explicit impact NOT_ESTIMATED semantics, 24B specifications and 24C forecast runtime | Governed analytical data; scenario assumptions; validated methodology-owned specifications; explicit forecast requests | Reproducible analytical/scenario evidence, descriptive spatial runs, versioned specifications and immutable forecast outcomes | ORDOAnalyticsService | Reporting/AI synthesis; accepted 24D/24E presentation/Help/XAI | PostgreSQL ORDO analytics tables | ORDO scope; deterministic numeric authority; scenario is not forecast; human review required | NO | YES | tests/test_isi_11*.py; tests/test_isi_22g*.py; tests/test_isi_24a*.py; tests/test_isi_24b*.py; tests/test_isi_24c*.py | REQUIRED_COMPATIBILITY | ISI-22 / ISI-24A / ISI-24B / ISI-24C | Legacy scenario rows remain LEGACY_NOT_EVALUATED; new scenarios persist NOT_ESTIMATED without fabricating impact; forecast execution never changes the 24B plan-only specification |
| INV-C29 | Report/ReportVersion/ReportReview/ReportExport | Reporting entities | CURRENT_AS_BUILT | src/platform/reporting/models.py | Report lifecycle/version/review/export persistence | Report service operations | Persistent report history/export | ReportingService | Reporting UI/API | PostgreSQL | Org/workspace/product scope; reviewer identity; checksums | NO | YES | tests/test_isi_12*.py | NONE | ISI-27 | Published version history must remain auditable |
| INV-C30 | SecurityRateLimit/SecurityEvent | Security entities | CURRENT_AS_BUILT | src/platform/security/models.py | Persist throttling state and security audit events | Auth/security actions | Rate-limit/event state | SecurityService | Auth/admin/operations | PostgreSQL | Hashed subjects/client metadata | NO | YES | tests/test_isi_14_rate_limit_contract.py; tests/test_isi_20_security_events.py | NONE | ISI-20 | Do not downgrade hashing/audit requirements |
| INV-C31 | SimpaMethodologyReferenceSuite/Case | SIMPA methodology evidence entities | CURRENT_AS_BUILT | src/domains/simpa/analytics_models.py; src/domains/simpa/reference_calculations.py; migrations/versions/20260915_0028_simpa_reference_calculation_suites.py | Persist methodology-owned versioned immutable multi-case reference semantics, execution results, fingerprints and creator/executor trace | Intact proposed suite_v1 methodology, explicit reference dataset version and deterministic cases | Reproducible passed/failed case and suite evidence | SIMPAAnalyticsService | Human methodology validation and API/UI provenance | PostgreSQL SIMPA-only suite/case tables | indicator.manage creates/runs; analysis.read views; membership trace; no tenant dataset binding | NO | YES | tests/test_isi_23b*.py | NONE | ISI-23B | Never fabricate historical suites; terminal evidence is immutable and validation reloads/recomputes every semantic/result fingerprint |
| INV-C32 | SimpaStatisticalModelContract/Result | SIMPA statistical methodology/execution entities | CURRENT_AS_BUILT | src/domains/simpa/analytics_models.py; src/domains/simpa/statistical_contracts.py; src/domains/simpa/statistical_models.py; migrations/versions/20260915_0029_simpa_statistical_model_contracts.py | Persist global versioned target-methodology-bound statistical specifications and immutable scoped deterministic results | Exact current validated target methodology plus governed revalidated analytics run | Contract/result fingerprints, coefficients, uncertainty, metrics, diagnostics, calibration and production-eligibility trace | SIMPAAnalyticsService; AnalyticalDataService | Evidence-first SIMPA UI/reporting | PostgreSQL SIMPA-only statistical contract/result tables | indicator.manage lifecycle; analysis.run execution; analysis.read visibility; target and governed data bindings fail closed | NO | YES | tests/test_isi_23c*.py | NONE | ISI-23C | Contract content is immutable; changed target methodology/specification requires a new version; no champion/promotion, threshold/class, causal or person-level semantics |
| INV-C33 | ORDO governed reference evidence | Domain evidence entity | CURRENT_AS_BUILT | src/domains/ordo/models.py; src/domains/ordo/schemas.py; src/domains/ordo/service.py; migrations/versions/20260916_0030_ordo_governed_evidence_gis_contracts.py | Persist pinned source/evidence identity, validity, SHA-256 provenance and human lifecycle | ORDO workspace scope; source identity/version; optional indicator/source-version binding | Draft/proposed/validated/retired governed evidence records | ORDOService; core data-source versions | ORDO methodology/scenario evidence | PostgreSQL ordo_reference_evidence | Organization/workspace scope; explicit human lifecycle actor; no automatic validation | NO | YES | tests/test_isi_24a_reference_evidence_contract.py; tests/test_isi_24a_reference_lifecycle.py | NONE | ISI-24A | Never fabricate validation or source fingerprints; changed evidence requires a new governed identity/version |
| INV-C34 | ORDO governed spatial-unit identity | GIS provenance entity | CURRENT_AS_BUILT | src/domains/ordo/models.py; src/domains/ordo/schemas.py; src/domains/ordo/service.py; migrations/versions/20260916_0030_ordo_governed_evidence_gis_contracts.py | Persist boundary source/version, geometry identity, CRS, artifact SHA-256, validity, provenance and human lifecycle without storing geometry | ORDO workspace scope; boundary identity metadata | Draft/proposed/validated/retired spatial-unit identity records | ORDOService | Future ISI-24B spatial processing | PostgreSQL ordo_spatial_units | Organization/workspace scope; explicit human lifecycle actor; no spatial-policy inference | NO | YES | tests/test_isi_24a_gis_contract.py; tests/test_isi_24a_reference_lifecycle.py | NONE | ISI-24A | 24A is identity/provenance only; geometry storage, joins and spatial statistics require the later governed spatial phase |
| INV-C35 | ORDO spatial aggregation processing/run | Deterministic descriptive analytics entity | CURRENT_AS_BUILT | src/domains/ordo/spatial_processing.py; src/domains/ordo/analytics_service.py; src/domains/ordo/analytics_models.py; migrations/versions/20260916_0031_ordo_spatial_statistical_temporal_contracts.py | Validate methodology-owned v1 identity contract and persist deterministic count/sum/mean/min/max aggregation over exact governed spatial identity | Revalidated governed ORDO run; validated methodology and spatial unit; exact boundary/version/CRS/type records | Fingerprinted descriptive aggregation run with explicit missing count and locked false join/weight/forecast/causal/policy semantics | ORDOAnalyticsService | Later evidence presentation/reporting | PostgreSQL ordo_spatial_aggregation_runs | Exact organization/workspace and spatial identity; no geometry inference or join | NO | YES | tests/test_isi_24b_spatial_processing_contract.py; tests/test_isi_24b_reference_calculations.py | NONE | ISI-24B | Remains descriptive only; geometry, interpolation, clustering, distance, weighting and policy inference require separate approved scope |
| INV-C36 | ORDO statistical model contract | Statistical specification entity | CURRENT_AS_BUILT | src/domains/ordo/statistical_contracts.py; src/domains/ordo/analytics_models.py; src/domains/ordo/analytics_service.py; migrations/versions/20260916_0031_ordo_spatial_statistical_temporal_contracts.py | Persist versioned target-compatible non-causal statistical specifications bound to exact validated methodology and governed run | Human-authored strict contract; validated methodology; revalidated analytics run | Canonical contract JSON/fingerprint and human lifecycle evidence | ORDOAnalyticsService | Future separately governed fitting/execution | PostgreSQL ordo_statistical_model_contracts | Organization/workspace scope; no fitting/result authority; no automatic policy recommendation | NO | YES | tests/test_isi_24b_statistical_contract.py | NONE | ISI-24B | Specification changes or methodology changes require a new version; no statistical result entity exists in 24B |
| INV-C37 | ORDO time-series specification | Forecast-readiness specification entity | CURRENT_AS_BUILT | src/domains/ordo/time_series_contracts.py; src/domains/ordo/analytics_models.py; src/domains/ordo/analytics_service.py; migrations/versions/20260916_0031_ordo_spatial_statistical_temporal_contracts.py | Persist versioned time-series readiness and rolling-origin plan metadata with execution and automatic selection locked off | Human-authored strict spec; validated methodology; revalidated analytics run | Canonical spec/fingerprint and human lifecycle evidence; plan only | ORDOAnalyticsService | ORDO forecast execution/runtime result authority (INV-C38) | PostgreSQL ordo_time_series_specs | Organization/workspace scope; forecast_execution=false; automatic_model_selection=false; non-causal | NO | YES | tests/test_isi_24b_time_series_contract.py; tests/test_isi_24b_governance_contract.py | NONE | ISI-24B | Validation means specification readiness only; 24C execution consumes the immutable binding separately and never mutates its plan-only truth |
| INV-C38 | ORDO forecast execution/runtime result authority | Forecast runtime entity/service | CURRENT_AS_BUILT | src/domains/ordo/analytics_models.py; src/domains/ordo/analytics_service.py; src/domains/ordo/forecasting.py; src/api/ordo_analytics_routes.py; migrations/versions/20260916_0032_ordo_forecast_backtest_uncertainty.py | Execute only explicitly requested naive/seasonal-naive families against exact revalidated governed evidence and persist deterministic ESTIMATED or NOT_ESTIMATED outcomes | Validated 24B time-series spec; exact series identity; interval level; authenticated analysis.run actor | Immutable fingerprinted forecast attempt with points/intervals or stable reason code | ORDO time-series specification; governed analytical input | ISI-24D evidence-first presentation/Help/XAI | PostgreSQL ordo_forecast_runs | Exact organization/workspace/spec/methodology/input binding; non-causal; no automatic selection or policy recommendation | NO | YES | tests/test_isi_24c_api_contract.py; tests/test_isi_24c_forecast_engine.py; tests/test_isi_24c_not_estimated_semantics.py | NONE | ISI-24C | Unsupported families and insufficient evidence persist NOT_ESTIMATED; no fallback, model promotion, scenario impact or fabricated interval |
| INV-C39 | ORDO forecast/backtest metrics + uncertainty authority | Deterministic analytical authority | CURRENT_AS_BUILT | src/domains/ordo/forecast_metrics.py; src/domains/ordo/forecasting.py; src/domains/ordo/analytics_service.py | Produce rolling-origin splits, exact metrics, leakage-safe empirical residual intervals, calibration counts and domain clipping | Chronological regular series; validated rolling-origin plan; explicit interval level | Per-origin records, aggregate metrics, availability, diagnostics and final intervals | ORDO forecast execution/runtime authority | Persisted forecast result; later ISI-24D explanation | Persisted through ordo_forecast_runs JSON evidence | Training-only metrics; strictly earlier-origin backtest intervals; no random split/future leakage | NO | YES | tests/test_isi_24c_rolling_origin.py; tests/test_isi_24c_uncertainty_diagnostics.py; tests/test_isi_24c_reference_forecasts.py | NONE | ISI-24C | Empirical intervals describe only the implemented residual method; unavailable required metrics yield NOT_ESTIMATED rather than invention |
| INV-C40 | AI capability/model registration + fallback + prompt rollback | AI governance entities | CURRENT_AS_BUILT | src/platform/ai/models.py; src/platform/ai/governance.py; migrations/versions/20260917_0033_ai_mlops_governance_evaluation_foundation.py | Persist immutable capability/model fingerprints, candidate/challenger/retired lifecycle, explicit acyclic fallback-edge evidence and checksum-bound prompt rollback targets | Statistical/ML, embedding, LLM or VLM identity; existing optional runtime AIModel; prompt versions | Governed identity/provenance and persisted fallback/rollback relations | Existing AI runtime/prompt/policy substrate | Exact-registration-bound fallback runtime and evaluation/promotion governance | PostgreSQL core_ai_model_registrations/core_ai_model_fallbacks/core_ai_prompt_rollback_targets | Product scope plus existing provider/data policy; global mutation platform-admin-only; champion mutation fails closed | NO | YES | tests/test_isi_25a_model_registry.py; tests/test_isi_25a_api_contract.py; tests/test_isi_25b_capability_runtime.py | NONE | ISI-25A / ISI-25B | No hard-coded permanent champion or heuristic registry scan; 25B enforces exact binding, semantic/provider/review/circuit gates and auditable fallback evidence |
| INV-C41 | AI evaluation dataset/run/result/review foundation | AI evaluation entities | CURRENT_AS_BUILT | src/platform/ai/models.py; src/platform/ai/evaluation.py; tests/evals/SIMPA-EVAL-v1.json; tests/evals/ORDO-EVAL-v1.json; migrations/versions/20260917_0033_ai_mlops_governance_evaluation_foundation.py | Persist frozen synthetic evaluation contracts, scoped runs, typed deterministic evidence/results, immutable terminal fingerprints and human-review traces | Frozen fixture manifest; registered capability/model; scoped provenance/config identity | Dataset/run/result/review foundation evidence | AI governance registry | 25B evaluator/promotion engines and shared AI inspection | PostgreSQL core_ai_evaluation_* plus repository CONTRACT/FIXTURE manifests | Dataset mutation platform-admin-only after scope resolution; scoped run access; reviewer membership; report.publish review writes; no production data/promotion side effect | NO | YES | tests/test_isi_25a_eval_foundation.py; tests/test_isi_25a_api_contract.py; tests/test_isi_25b_evaluation_engines.py | NONE | ISI-25A / ISI-25B | SIMPA-EVAL-v1 and ORDO-EVAL-v1 remain foundation-only non-production fixtures and cannot be reused as promotion evidence; 25B uses separate frozen promotion benchmarks |
| INV-C42 | AI promotion benchmark + capability threshold authority | AI evaluation governance entities | CURRENT_AS_BUILT | src/platform/ai/models.py; src/platform/ai/evaluation.py; migrations/versions/20260918_0034_ai_evaluation_promotion_runtime.py | Persist immutable frozen promotion benchmarks separately from 25A fixtures and versioned capability-specific thresholds/hard gates/circuit policy | Synthetic or approved benchmark manifests; explicit threshold contracts | Hash-addressed benchmark and threshold identities | AI evaluation foundation | Promotion comparison/runtime policy | PostgreSQL core_ai_evaluation_benchmarks/core_ai_capability_thresholds | Platform-admin mutation after scope resolution; no embedded secrets or fabricated gold | NO | YES | tests/test_isi_25b_evaluation_engines.py; tests/test_isi_25b_promotion.py | NONE | ISI-25B | Foundation fixtures can never become promotion evidence; changed content requires a new version; no generic weighted score |
| INV-C43 | AI promotion decision + capability runtime/circuit state | AI runtime governance entities | CURRENT_AS_BUILT | src/platform/ai/models.py; src/platform/ai/promotion.py; src/platform/ai/service.py; migrations/versions/20260918_0034_ai_evaluation_promotion_runtime.py | Persist evidence-gated decisions, sole capability champion/rollback pin and deterministic circuit state | Completed same-benchmark runs, thresholds, approved review, owner approval | Audited governance transition and request-time circuit enforcement | Evaluation/registry | Bound AI runtime/read model | PostgreSQL core_ai_promotion_decisions/core_ai_capability_runtime_states | Platform admin plus report.publish for promotion/rollback; no installation/deployment | NO | YES | tests/test_isi_25b_capability_runtime.py; tests/test_isi_25b_promotion.py | NONE | ISI-25B | No permanent winner, online learning, silent rollback or server activation |
| INV-C44 | AI drift snapshot + shared AI XAI read model | AI monitoring/interpretation entities | CURRENT_AS_BUILT | src/platform/ai/monitoring.py; src/platform/ai/xai.py; src/api/ai_routes.py; migrations/versions/20260918_0034_ai_evaluation_promotion_runtime.py | Persist explicit on-demand drift windows and present faithful lifecycle/evidence/fallback/circuit/review interpretation | Explicit observed/reference metrics and governed AI evidence | Bounded status/fingerprint and unavailable states for unsupported XAI | Capability threshold/runtime state | AI inspection/Help | PostgreSQL core_ai_drift_snapshots plus deterministic read model | Scoped analysis permissions; no scheduler or online learning | YES | YES | tests/test_isi_25b_monitoring_xai_help.py | NONE | ISI-25B / ISI-27 | Unsupported confidence/calibration/feature importance/SHAP is unavailable; global non-AI Help remains ISI-27 |

#### D. WORKER / JOB ARCHITECTURE

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-D01 | Data queue | Job dispatcher | CURRENT_AS_BUILT | src/platform/data/queue.py | Dispatch ingestion inline or to RQ isi-data | IngestionJob id; DATA_JOB_BACKEND | Worker invocation/RQ job id | Data service | Data worker | Redis when RQ + PostgreSQL rq_job_id | No direct customer authority; scoped job already persisted | NO | YES | tests/test_isi_06_ingestion.py; tests/test_isi_18_observability.py | NONE | ISI-22 / ISI-26 | Unsupported backend fails closed |
| INV-D02 | Data worker | Worker | CURRENT_AS_BUILT | src/workers/data_jobs.py; src/workers/data_worker.py | Execute ingestion job with DB row locking/status/attempt tracking | IngestionJob/DataSourceVersion | Parsed data/version/run results | Data queue | Governance/operations | PostgreSQL + object storage | DB transaction/row-lock integrity; scoped source | NO | YES | tests/test_isi_06_ingestion.py; tests/test_isi_22*.py | NONE | ISI-22 / ISI-26 | Preserve terminal state and retry/audit evidence |
| INV-D03 | AI queue | Job dispatcher | CURRENT_AS_BUILT | src/platform/ai/queue.py | Dispatch AI inline or to RQ isi-ai | AIJob id; AI_JOB_BACKEND | Worker invocation/RQ job id | AIService | AI worker | Redis when RQ + PostgreSQL rq_job_id | Policy/scoped AI job already persisted | NO | YES | tests/test_isi_07*.py | NONE | ISI-25 / ISI-26 | Unsupported backend fails closed |
| INV-D04 | AI worker | Worker | CURRENT_AS_BUILT | src/workers/ai_jobs.py; src/workers/ai_worker.py | Execute model/provider attempts and persist results | AIJob + model/policy/prompt | Attempt/result/failure/review state | AI queue | Domain/UI/report consumers | PostgreSQL + provider runtime | Policy/provider/tenant/product constraints | NO | YES | tests/test_isi_07*.py ; tests/test_isi_29e_* | NONE | ISI-25 / ISI-26 | 29E guard in existing worker before/after execution: policy/source/actor/model/prompt/hash scoped revalidation and strict nested output; invalid quotes fail closed; legacy jobs unchanged. |
| INV-D05 | Application scheduler | Scheduler | NOT_PRESENT | No current repository implementation | No application-owned scheduler exists in current as-built ISI | N/A | N/A | N/A | Potential future periodic jobs | N/A | Must not be assumed as active runtime authority | NO | NO | Repository search + SYSTEM INVENTORY contract | NONE | Future explicit ADR/phase only | Add only with named owner-approved phase, persistence/locking/recovery design and tests |
| INV-D06 | Claim/lease/heartbeat protocol | Worker coordination pattern | NOT_PRESENT | No current repository implementation | Krcuga-style application lease/heartbeat protocol is not part of ISI | N/A | N/A | N/A | N/A | RQ/DB job status and row locks are current mechanism | Do not invent cross-project coordination semantics | NO | NO | SYSTEM INVENTORY contract | NONE | Future explicit ADR/phase only | Introduce only if evidence proves current RQ/DB semantics insufficient |
| INV-D07 | Ingestion retry/backfill/replay/DLQ semantics | Job lifecycle contract | CURRENT_AS_BUILT | src/platform/data/ingestion_operations_service.py; src/platform/data/models.py | Operational retry/recovery without corrupting forward cursor | Completed/failed run; operational policy | Replay/backfill/DLQ/new governed output | Data worker/governance | Analytical boundary/operators | PostgreSQL | Governance-manage permission where action is privileged | NO | YES | tests/test_isi_22e*.py | NONE | ISI-22 | Backfill/replay never silently advance forward cursor; DLQ history retained |

#### E. AI PROVIDERS AND MODEL EXECUTION

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-E01 | AI HTTP/provider gateway | AI boundary | CURRENT_AS_BUILT | src/platform/ai/gateway.py | Single provider resolution/invocation boundary | AI model/policy request | Provider response/error | AIService | AI worker | Attempt metadata in PostgreSQL | Provider allowlist/policy | NO | YES | tests/test_isi_07_policy.py; tests/test_isi_07_provider_stub.py | NONE | ISI-25 | All new AI providers enter here |
| INV-E02 | Ollama provider | AI provider | CURRENT_AS_BUILT | src/platform/ai/providers.py; src/core/config.py | Local HTTP chat/embedding provider | Model + prompt + Ollama base URL | LLM/embedding response | AIGateway | AI jobs/RAG | Bare-metal/local Ollama runtime | Local/preferred policy; server Ollama frozen until ISI-28 | NO | YES | tests/test_isi_07*.py | NONE | ISI-25 / ISI-28 | Production model promotion requires eval registry evidence  R3 optional ISI request thread bound preserves default payload and provider/policy/model ownership; native deployed readiness still pending |
| INV-E03 | Development stub provider | AI provider | DEVELOPMENT_ONLY | src/platform/ai/providers.py; src/platform/ai/gateway.py | Deterministic development/test stub | Stub-enabled config | Synthetic response | AIGateway | Tests/development | No external persistence beyond AI attempt | Explicitly flag-gated; forbidden in production | NO | NO | tests/test_isi_07_provider_stub.py | REQUIRED_COMPATIBILITY | ISI-25 | Remove only if tests/dev no longer require; never enable in production |
| INV-E04 | External AI provider adapter | AI provider | NOT_CONFIGURED | src/platform/ai/gateway.py | Reserved provider type has no configured adapter | provider=external | Fails closed external_provider_not_configured | AI model registry | None until implemented | None | Cannot send data externally without explicit policy/privacy approval | NO | NO | tests/test_isi_07_policy.py | NONE | Future explicit ISI-25 decision | Requires adapter, secrets policy, DPA/privacy review, eval and fallback contract |
| INV-E05 | Legacy selected-only plus exact-registration-bound fallback runtime | AI orchestration contract | CURRENT_AS_BUILT | src/platform/ai/service.py; src/platform/ai/governance.py | Preserve unbound 25A selected-only jobs while executing fallback only from an exact bound source registration | Pinned policy/model and optional exact registration; persisted fallback edges | Auditable source/target registration, edge, trigger and review-required attempt evidence | AI runtime registry + governance registry + gateway | AI worker/human review | AIJob/AIJobAttempt/AIModelFallback/AIAuditEvent | Existing provider/data policy and sensitive SIMPA local-only restriction; semantic and circuit gates fail closed | NO | YES | tests/test_isi_07_policy.py; tests/test_isi_25a_model_registry.py; tests/test_isi_25b_capability_runtime.py | REQUIRED_COMPATIBILITY | ISI-25A / ISI-25B | Unbound legacy jobs never scan registrations; bound jobs never infer first registration from runtime model; ORDO forecast-family fallback remains outside MLOps |
| INV-E06 | AI runtime model/prompt/policy + capability governance registry | AI governance | CURRENT_AS_BUILT | src/platform/ai/models.py; src/platform/ai/service.py; src/platform/ai/governance.py; src/platform/ai/promotion.py | Preserve selected/default-model compatibility while governing exact-registration-bound fallback, cross-family lifecycle identity, provenance, prompt rollback and evidence-gated capability champion state | Model/prompt/policy definitions and capability/artifact identities | Pinned execution refs plus governance/promotion/runtime fingerprints | Admin/bootstrap | AI jobs, evaluation and shared AI inspection | PostgreSQL | Product/policy/provider governance; shared mutations require platform-admin authority after normal scope resolution | NO | YES | tests/test_isi_07_models_contract.py; tests/test_isi_25a_model_registry.py; tests/test_isi_25b_capability_runtime.py; tests/test_isi_25b_promotion.py | NONE | ISI-25A / ISI-25B | No heuristic registration scanning, automatic installation, silent promotion/rollback, online learning or deployment mutation |
| INV-E07 | Embedding capability | AI/RAG capability | CURRENT_AS_BUILT | src/platform/ai/service.py; src/platform/ai/models.py | Create/store scoped embeddings for retrieval | Eligible evidence text | Embedding/vector metadata | AI provider + knowledge/data eligibility | RAG/retrieval | PostgreSQL; optional pgvector capability | Tenant/product/private namespace isolation | NO | YES | tests/test_isi_07_namespaces.py; tests/test_isi_21c_ai_eligibility.py | NONE | ISI-25 | Multilingual retrieval eval required before production promotion |
| INV-E08 | Dedicated Vision provider/service | AI modality | NOT_PRESENT | No dedicated current path; VLM model candidates are only roadmap candidates | No standalone vision pipeline exists | N/A | N/A | N/A | Potential future document/VLM extraction | N/A | Do not import Krcuga vision architecture into ISI implicitly | NO | NO | SYSTEM INVENTORY contract | NONE | Future explicit ISI-25 task | Requires explicit use case, provider boundary, data policy, eval and human review |
| INV-E09 | Dedicated Audio provider/service | AI modality | NOT_PRESENT | No current repository implementation | No audio transcription/lab pipeline exists | N/A | N/A | N/A | N/A | N/A | Do not import Krcuga audio architecture into ISI implicitly | NO | NO | SYSTEM INVENTORY contract | NONE | Future explicit task only | Requires owner-approved product requirement and full privacy/eval architecture |

#### F. REPORT ARCHITECTURE

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-F01 | Shared report service | Reporting service | CURRENT_AS_BUILT | src/platform/reporting/service.py ; src/platform/reporting/linked_evidence.py; src/domains/{simpa,ordo}/report_evidence.py; src/streamlit_app/linked_reporting_workspace.py; docs/help/ISI-LINKED-REPORTS-GUIDE.md | Create/version/review/publish/export reports | Content + source manifest | Report lifecycle state | Domain adapters | API/UI/export | PostgreSQL | Manifest scope/checksum + report permissions | NO | YES | tests/test_isi_12*.py ; tests/test_isi_29f_* | NONE | ISI-27 | 29F accepted software f587ed0: accepted claim/source/dated geometry and optional exact domain result/XAI; human contextual association; source/auth/integrity revalidated at read/lifecycle/export/download. Exact local/browser/manual/CI/signed release and scoped server gates PASS; full-production gates remain open. |
| INV-F02 | SIMPA report adapter | Domain adapter | CURRENT_AS_BUILT | src/domains/simpa/reporting_adapter.py ; src/platform/reporting/linked_evidence.py; src/domains/{simpa,ordo}/report_evidence.py; src/streamlit_app/linked_reporting_workspace.py; docs/help/ISI-LINKED-REPORTS-GUIDE.md | Build SIMPA report payload/provenance | SIMPA persisted evidence | Shared report contract | SIMPA service/analytics | Shared reporting | None | SIMPA scope | NO | YES | tests/test_isi_12*.py ; tests/test_isi_29f_* | NONE | ISI-23 / ISI-27 | 29F accepted software f587ed0: accepted claim/source/dated geometry and optional exact domain result/XAI; human contextual association; source/auth/integrity revalidated at read/lifecycle/export/download. Exact local/browser/manual/CI/signed release and scoped server gates PASS; full-production gates remain open. |
| INV-F03 | ORDO report adapter | Domain adapter | CURRENT_AS_BUILT | src/domains/ordo/reporting_adapter.py ; src/platform/reporting/linked_evidence.py; src/domains/{simpa,ordo}/report_evidence.py; src/streamlit_app/linked_reporting_workspace.py; docs/help/ISI-LINKED-REPORTS-GUIDE.md | Build ORDO report payload/provenance | ORDO persisted evidence | Shared report contract | ORDO service/analytics | Shared reporting | None | ORDO scope | NO | YES | tests/test_isi_12*.py ; tests/test_isi_29f_* | NONE | ISI-24 / ISI-27 | 29F accepted software f587ed0: accepted claim/source/dated geometry and optional exact domain result/XAI; human contextual association; source/auth/integrity revalidated at read/lifecycle/export/download. Exact local/browser/manual/CI/signed release and scoped server gates PASS; full-production gates remain open. |
| INV-F04 | Internal renderer | Renderer | CURRENT_AS_BUILT | src/platform/reporting/render.py ; src/platform/reporting/linked_evidence.py; src/domains/{simpa,ordo}/report_evidence.py; src/streamlit_app/linked_reporting_workspace.py; docs/help/ISI-LINKED-REPORTS-GUIDE.md | Deterministic JSON/Markdown/HTML rendering | Report metadata/content/manifest | Text export | ReportingService | ReportExport/API | ReportExport content_text in PostgreSQL | Escaping/safe deterministic output | NO | YES | tests/test_isi_12_render_contract.py; tests/test_isi_12_safety_contract.py ; tests/test_isi_29f_* | NONE | ISI-27 | 29F accepted software f587ed0: accepted claim/source/dated geometry and optional exact domain result/XAI; human contextual association; source/auth/integrity revalidated at read/lifecycle/export/download. Exact local/browser/manual/CI/signed release and scoped server gates PASS; full-production gates remain open. |
| INV-F05 | Report persistence/lifecycle | Reporting state machine | CURRENT_AS_BUILT | src/platform/reporting/models.py; src/platform/reporting/service.py ; src/platform/reporting/linked_evidence.py; src/domains/{simpa,ordo}/report_evidence.py; src/streamlit_app/linked_reporting_workspace.py; docs/help/ISI-LINKED-REPORTS-GUIDE.md | draft -> in_review -> approved/rejected -> published/superseded | Report edits/reviews | Auditable version state | ReportingService | Export/delivery | PostgreSQL | Reviewer/publisher permissions and scope | NO | YES | tests/test_isi_12*.py ; tests/test_isi_29f_* | NONE | ISI-27 | 29F accepted software f587ed0: accepted claim/source/dated geometry and optional exact domain result/XAI; human contextual association; source/auth/integrity revalidated at read/lifecycle/export/download. Exact local/browser/manual/CI/signed release and scoped server gates PASS; full-production gates remain open. |
| INV-F06 | External document conversion service | Document service | NOT_PRESENT | No active repository implementation | No external PDF/office rendering service is active | N/A | N/A | N/A | Potential future export formats | N/A | Must not be assumed as deployed HTTP boundary | NO | NO | SYSTEM INVENTORY contract | NONE | Future explicit ISI-27 task if required | Add only with explicit format need, security isolation and acceptance tests |

#### G. SECURITY / AUTH

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-G01 | Auth API boundary | Security boundary | CURRENT_AS_BUILT | src/api/auth_routes.py | Expose login/logout/sessions/verification/reset/invitation/assurance | HTTP auth requests | Auth responses/session state | AuthService/SecurityService | App shell/users | PostgreSQL | Rate limiting; anti-enumeration; token/session rules | YES | YES | tests/test_isi_02b_api.py; tests/test_isi_14*.py; tests/test_isi_20*.py | NONE | ISI-20 | No public self-registration without explicit decision |
| INV-G02 | Session authority | Security boundary | CURRENT_AS_BUILT | src/platform/auth/service.py; src/api/dependencies.py | Resolve bearer session and authenticated user | Bearer token | AuthContext | Auth API | All protected API | AuthSession | Session expiry/idle/revocation/last_seen | NO | YES | tests/test_isi_20_session_management.py | NONE | ISI-20 | Backend session is authority; Streamlit session state is not |
| INV-G03 | Invitation authority | Security boundary | CURRENT_AS_BUILT | src/platform/auth/service.py; src/api/auth_routes.py | Organization-scoped onboarding | One-time invitation | Membership/user/session | Administration | Authenticated user | Invitation/User/Membership | Single-use token + org scope | NO | YES | tests/test_isi_13_invitation_contract.py | NONE | ISI-20 | No anonymous tenant joining |
| INV-G04 | Password assurance / MFA foundation | Security control | CURRENT_AS_BUILT | src/platform/auth/models.py; src/platform/auth/service.py | Step-up password assurance plus MFA data foundation | Current session + factor/challenge | Assurance/factor state | AuthService | Sensitive actions | PostgreSQL | Strong-auth boundary; real-provider MFA validation still future | NO | YES | tests/test_isi_20_auth_assurance.py; tests/test_isi_20_mfa_challenge_foundation.py | NONE | ISI-20 / ISI-27 | Do not claim real-provider MFA validated until evidence exists |
| INV-G05 | SMTP auth delivery | Security integration | CURRENT_AS_BUILT | src/platform/auth/delivery.py | Verification/reset/invitation email adapter | Token + recipient | Email message | AuthService | User mailbox | External SMTP; no token DB beyond AuthToken | Production requires real configured adapter; credentials secret | NO | YES | tests/test_isi_15_delivery.py | NONE | ISI-28 | Production SMTP frozen until ISI-28 |
| INV-G06 | RBAC authority | Authorization boundary | CURRENT_AS_BUILT | src/platform/access/catalog.py; src/platform/access/service.py | Role/permission evaluation | Membership/product/workspace/roles | Permission decision | Identity/access data | All private APIs | PostgreSQL | Central authorization authority | NO | YES | tests/test_isi_20_access_matrix.py | NONE | ISI-20 | UI visibility cannot replace backend permission checks |
| INV-G07 | Tenant/product/workspace isolation | Authorization boundary | CURRENT_AS_BUILT | src/platform/app_context/service.py; src/platform/access/**; src/platform/workspaces/** | Enforce organization/SIMPA-ORDO/workspace boundaries | Request context + persisted scope | Scoped query/operation | Auth/RBAC | Data/domain/AI/reporting | PostgreSQL foreign keys + scoped queries | Primary data isolation boundary | NO | YES | tests/test_isi_20_access_matrix.py; tests/test_isi_21_integrated_acceptance.py | NONE | ISI-20 / ISI-21 | Cross-tenant or cross-product access is blocker severity |
| INV-G08 | Login rate limit/security events | Security control | CURRENT_AS_BUILT | src/platform/security/service.py; src/platform/security/models.py | Throttle abuse and audit security outcomes | Login/client metadata | Allowed/throttled + hashed event | Auth routes | Security/admin diagnostics | PostgreSQL | Hash sensitive identifiers/client metadata | NO | YES | tests/test_isi_14_rate_limit_contract.py; tests/test_isi_20_security_events.py | NONE | ISI-20 | Cannot disable in production for convenience |
| INV-G09 | Security headers/host/proxy boundary | HTTP security control | CURRENT_AS_BUILT | src/api/app.py; src/core/config.py | Trusted hosts/proxy handling/security headers | HTTP request/config | Hardened response/request interpretation | Deployment config | All HTTP clients | Config only | Production hosts/proxy config must be explicit | NO | YES | tests/test_isi_14_headers_contract.py; tests/test_isi_14_production_config_contract.py | NONE | ISI-20 / ISI-28 | Server ingress settings frozen until ISI-28 |
| INV-G10 | Platform administration authority | Authorization boundary | CURRENT_AS_BUILT | src/platform/administration/**; src/api/administration_routes.py | Privileged organization/member/workspace/audit operations | Admin permission context | Administrative mutation/audit | RBAC | Identity/access/workspaces | PostgreSQL | organization.manage/members.manage/workspace.manage/audit.read | NO | YES | tests/test_isi_13*.py | NONE | ISI-20 | No hidden superuser path outside defined platform-admin/admin controls |

#### H. PAYMENTS / COMMERCIAL BILLING

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-H01 | Commercial payment/billing subsystem | Payment boundary | NOT_PRESENT | No PayPal/billing/checkout/subscription/invoice implementation in ISI repository | ISI access is entitlement/RBAC based, not payment based | N/A | N/A | N/A | OrganizationEntitlement and MembershipProductAccess are authorization only | No payment persistence | No payment callback/webhook authority exists | NO | NO | Repository search + SYSTEM INVENTORY contract | NONE | OUT OF CURRENT PRODUCT SCOPE | Do not import Krcuga/OralScan payment architecture; requires explicit owner product decision |
| INV-H02 | Payment provider adapter | Payment provider boundary | NOT_PRESENT | No payment-provider module/configuration in ISI repository | Make absence of PayPal/Stripe/other commercial provider explicit | N/A | N/A | N/A | N/A | No payment provider state | No provider credentials or payment API authority exist | NO | NO | Repository search + SYSTEM INVENTORY contract | NONE | OUT OF CURRENT PRODUCT SCOPE | Requires explicit owner-approved ISI commercial architecture before any provider code/config is added |
| INV-H03 | Payment callback/webhook boundary | External callback boundary | NOT_PRESENT | No payment callback/webhook route in src/api/** | Make absence of payment callbacks/webhooks explicit | N/A | N/A | N/A | N/A | No webhook event persistence | No signature-validation/payment-callback authority exists | NO | NO | Repository search + SYSTEM INVENTORY contract | NONE | OUT OF CURRENT PRODUCT SCOPE | Do not expose a payment webhook without explicit architecture, signature verification, idempotency and audit contracts |
| INV-H04 | Payment transaction/subscription persistence | Payment data model boundary | NOT_PRESENT | No payment/order/subscription/invoice transaction entities in src/platform/models.py | Make absence of commercial transaction persistence explicit | N/A | N/A | N/A | N/A | No payment tables | No PCI/payment-data processing boundary exists in ISI | NO | NO | Repository model registry search + SYSTEM INVENTORY contract | NONE | OUT OF CURRENT PRODUCT SCOPE | Requires explicit data/security/privacy design and migrations before introduction |
| INV-H05 | Entitlement/access boundary is not billing | Authorization boundary | CURRENT_AS_BUILT | src/platform/access/models.py; src/platform/access/service.py; src/platform/access/catalog.py | Clarify that OrganizationEntitlement and MembershipProductAccess authorize products but do not represent purchases/subscriptions | Admin-granted organization/member access | Authorization decisions | Administration/RBAC | App context/domain services | PostgreSQL access entities | Organization/product/membership authorization only | NO | YES | tests/test_isi_02a_access_matrix.py; tests/test_isi_20_access_matrix.py | NONE | ISI-20 | Must not be reinterpreted as billing/payment state without explicit owner-approved commercial architecture |

#### I. STORAGE / PERSISTENCE

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-I01 | PostgreSQL | Primary relational store | CURRENT_AS_BUILT | src/core/database.py; migrations/**; docker-compose.server.yml | Authoritative transactional persistence | Application transactions | Relational state | All services | All services/workers | PostgreSQL | DB credentials secret; tenant scope enforced in app/schema | NO | YES | native-postgres suites; migration tests | NONE | FOUNDATION / ISI-28 | Schema changes require Alembic migration + native PostgreSQL acceptance |
| INV-I02 | Content-addressed object storage abstraction | Storage service | CURRENT_AS_BUILT | src/platform/data/storage.py | Persist source payload bytes by scoped content hash | Bytes + scoped key | Immutable object | DataSourceService | Ingestion/recovery | Local filesystem or S3-compatible | Safe-key validation; org/product/workspace path | NO | YES | tests/test_isi_06_storage.py; tests/test_isi_15_storage.py | NONE | ISI-22 | No unscoped arbitrary filesystem path writes |
| INV-I03 | Local filesystem data storage | Development storage backend | DEVELOPMENT_ONLY | src/platform/data/storage.py; src/core/config.py | Local developer payload storage | DATA_STORAGE_BACKEND=local | Files under DATA_STORAGE_ROOT | Storage abstraction | Data ingestion | Local filesystem | Not production target | NO | NO | tests/test_isi_06_storage.py | REQUIRED_COMPATIBILITY | Development | Keep only while local development requires |
| INV-I04 | S3-compatible / MinIO storage | Production-shaped object backend | CURRENT_AS_BUILT | src/platform/data/storage.py; docker-compose.server.yml | Object storage implementation for production-shaped runtime | S3 config + payloads | Bucket objects | Storage abstraction | Data ingestion/recovery | MinIO/S3-compatible | Access keys are secrets; scoped keys | NO | YES | tests/test_isi_15_storage.py; tests/test_isi_server_deployment_contract.py | NONE | ISI-28 | Final production parameters determined in ISI-28 |
| INV-I05 | Redis | Queue infrastructure | CURRENT_AS_BUILT | src/platform/data/queue.py; src/platform/ai/queue.py; docker-compose.server.yml | RQ transport for data/AI workers | Job IDs | Queued RQ jobs | API/services | Workers | Redis | Internal runtime network; no business authorization state | NO | YES | tests/test_isi_15_compose_contract.py | NONE | ISI-26 / ISI-28 | Business truth must not depend solely on volatile Redis |
| INV-I06 | Report storage | Relational report persistence | CURRENT_AS_BUILT | src/platform/reporting/models.py | Persist report versions/reviews/exports | Report lifecycle | Auditable report/export rows | ReportingService | Reporting UI/API | PostgreSQL | Scoped by org/workspace/product | NO | YES | tests/test_isi_12*.py | NONE | ISI-27 | External blob report storage only if explicit future requirement |
| INV-I07 | AI execution/governance/evaluation persistence | Relational AI persistence | CURRENT_AS_BUILT | src/platform/ai/models.py | Persist runtime models/prompts/policies/jobs/attempts/audit/embeddings plus registrations/fallbacks/rollback targets/evaluation datasets/runs/results/reviews | AI lifecycle and governance/evaluation evidence | Auditable fingerprinted AI state | AIService + 25A governance/evaluation services | Human review/MLOps | PostgreSQL | Policy/product/namespace and tenant/workspace evaluation scope | NO | YES | tests/test_isi_07*.py; tests/test_isi_25a*.py | NONE | ISI-25 | Do not store disallowed request text; frozen/terminal evidence is immutable; 25A evidence cannot promote a model |
| INV-I08 | Backup/restore artifacts | Recovery storage | COMPATIBILITY | src/platform/recovery/**; tools/server/backup_restore_rehearsal.sh; docs/ops/** | Recovery evidence and backups for DB/object storage | Backup targets | Backup/rehearsal artifacts | PostgreSQL/MinIO | Recovery operator | Filesystem/server backup locations | Privileged; production execution frozen | NO | YES | tests/test_isi_19*.py | REQUIRED_COMPATIBILITY | ISI-19 / ISI-28 | Refresh exact production paths/retention during ISI-28 |
| INV-I09 | Logs/metrics | Operational evidence | CURRENT_AS_BUILT | src/platform/observability/** | Runtime diagnostic evidence | Service/queue/provider events | Logs/metrics/readiness | All runtime components | Operators/CI | Process/stdout/metrics; some DB audit entities | Must avoid secrets/sensitive payloads | NO | YES | tests/test_isi_18*.py | NONE | ISI-18 / ISI-26 | Add retention/export only via explicit observability design |

#### J. DEPLOYMENT / RUNTIME TOPOLOGY

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-J01 | server: postgres | Compose service | CURRENT_AS_BUILT | docker-compose.server.yml | Production-shaped PostgreSQL 17 service | Volume/env | DB service | Compose | api/workers/migrate | Docker volume | Internal network; credentials secret | NO | YES | tests/test_isi_server_deployment_contract.py | REQUIRED_COMPATIBILITY | ISI-28 | Final deployment reconciled from fresh server audit  Activated exact1bf0552; schema0034/new isi_production DB/isi-production private versioned bucket; four app images identical; operational closeout remains open |
| INV-J02 | server: redis | Compose service | COMPATIBILITY | docker-compose.server.yml | Production-shaped Redis 7 service | Env/network | Queue service | Compose | workers/api dispatch | Docker volume/runtime | Internal network | NO | YES | tests/test_isi_server_deployment_contract.py | REQUIRED_COMPATIBILITY | ISI-28 | Final deployment reconciled from fresh server audit |
| INV-J03 | server: minio | Compose service | CURRENT_AS_BUILT | docker-compose.server.yml | Production-shaped S3-compatible object store | Env/volume | S3 endpoint | Compose | api/workers/recovery | Docker volume | Internal network + secret credentials | NO | YES | tests/test_isi_server_deployment_contract.py | REQUIRED_COMPATIBILITY | ISI-28 | Final deployment reconciled from fresh server audit  Activated exact1bf0552; schema0034/new isi_production DB/isi-production private versioned bucket; four app images identical; operational closeout remains open |
| INV-J04 | server: minio-init | Compose init service | COMPATIBILITY | docker-compose.server.yml | Initialize required bucket/policy | MinIO readiness/config | Bucket initialization | minio | api/workers | MinIO state | Privileged init credentials | NO | YES | tests/test_isi_server_deployment_contract.py | REQUIRED_COMPATIBILITY | ISI-28 | May be replaced by deployment-time provisioning with equivalent checks |
| INV-J05 | server: migrate | Compose init service | COMPATIBILITY | docker-compose.server.yml | Apply Alembic migrations before app services | DATABASE_URL + image | Schema at head | postgres | api/workers | PostgreSQL schema | DB migration authority | NO | YES | tests/test_isi_15_compose_contract.py; migration CI | REQUIRED_COMPATIBILITY | ISI-28 | Final migration plan rehearsed in ISI-27/28 |
| INV-J06 | server: api | Compose service | CURRENT_AS_BUILT | docker-compose.server.yml | Run FastAPI backend | Config + DB/Redis/S3/AI | HTTP API | postgres/redis/minio/Ollama | streamlit/clients | External stores | No public exposure except ingress; secrets via env | YES | YES | tests/test_isi_server_deployment_contract.py | REQUIRED_COMPATIBILITY | ISI-28 | Final image/network/health config from RC  Activated exact1bf0552; schema0034/new isi_production DB/isi-production private versioned bucket; four app images identical; operational closeout remains open |
| INV-J07 | server: streamlit | Compose service | CURRENT_AS_BUILT | docker-compose.server.yml | Run authenticated Streamlit UI | API base URL/config | Private UI | api | users via ingress | Session state only | Ingress + backend auth | YES | YES | tests/test_isi_server_deployment_contract.py | REQUIRED_COMPATIBILITY | ISI-28 | Final path/URL determined by deployment plan  Activated exact1bf0552; schema0034/new isi_production DB/isi-production private versioned bucket; four app images identical; operational closeout remains open |
| INV-J08 | server: data-worker | Compose service | CURRENT_AS_BUILT | docker-compose.server.yml | Run RQ data worker | Redis/DB/S3 | Processed ingestion jobs | redis/postgres/minio | data platform | DB/object state | Internal service; no public port | NO | YES | tests/test_isi_15_compose_contract.py | REQUIRED_COMPATIBILITY | ISI-28 | Scale based on ISI-26 capacity evidence  Activated exact1bf0552; schema0034/new isi_production DB/isi-production private versioned bucket; four app images identical; operational closeout remains open |
| INV-J09 | server: ai-worker | Compose service | CURRENT_AS_BUILT | docker-compose.server.yml | Run RQ AI worker | Redis/DB/Ollama | AI results/attempts | redis/postgres/Ollama | AI service | PostgreSQL/provider runtime | Internal service; no public port | NO | YES | tests/test_isi_15_compose_contract.py | REQUIRED_COMPATIBILITY | ISI-28 | Scale based on ISI-26 and model eval evidence  Activated exact1bf0552; schema0034/new isi_production DB/isi-production private versioned bucket; four app images identical; operational closeout remains open |
| INV-J10 | server: mailpit | Precutover dev service | COMPATIBILITY | docker-compose.server.yml | Precutover SMTP test sink only | SMTP test mail | Captured test mail | api/auth delivery | Developer/operator | Mailpit runtime | precutover profile only; NOT production SMTP | NO | NO | tests/test_isi_server_deployment_contract.py | REMOVE_IN_NAMED_PHASE(ISI-28) | ISI-28 | Must not survive as production mail provider |
| INV-J11 | server: edge nginx | Precutover edge service | COMPATIBILITY | docker-compose.server.yml; docker/nginx/isi-server-precutover.conf | Loopback TLS/precutover reverse proxy for isolated acceptance only | api/streamlit | Local HTTPS 8445 when the `precutover` profile is explicitly used | Compose | local pre-cutover QA | Nginx config/certs | precutover profile; noindex; loopback bind | NO | NO | tests/test_isi_server_deployment_contract.py | REQUIRED_COMPATIBILITY | ISI-28 | Keep only as historical/precutover compatibility until final shared central-Nginx route is server-verified; it is not production ingress authority |
| INV-J12 | Dormant ISI-16 central ingress template | Historical deployment artifact | HISTORICAL | deploy/central-ingress/isi-production-server.conf.fragment | Old nginx template contains isi.rs:8443 assumptions; not current execution authority | Historical config | Audit reference | Old ISI-16 plan | None unless explicitly reconciled | File in repo | Do not execute; server frozen | NO | NO | tests/test_isi_server_deployment_contract.py | LEGITIMATE_HISTORY | ISI-28 | At ISI-28 compare to fresh server state then replace/remove as owner approves |
| INV-J13 | Shared central Nginx ingress | Target deployment component | TARGET | MasterPlan; ADR-0026; fresh ISI-28 server audit will verify final route config | Final shared TLS/reverse-proxy boundary through `central-ingress-nginx-1` / Compose project `central-ingress` / service `nginx` | Owner-approved final domain/port/cert/upstream mapping | Public HTTPS routing | Existing shared host central ingress | `isi-api:8000` and `isi-streamlit:8501` through `isi_ingress` | Server config/cert state | Only ISI-28 may mutate | YES | YES | ISI-27 acceptance + future ISI-28 server tests | NONE | ISI-28 | Edge identity is owner-locked now; route/cert/upstream details are physically verified or changed only under ISI-28  ISI public/app/API routes HTTPS verified; shared config/non-target identities preserved; no further shared ingress mutation |
| INV-J14 | Bare-metal Ollama | External runtime component | TARGET | src/core/config.py; docker-compose.server.yml extra_hosts; MasterPlan | Local model runtime outside ISI Compose | AI model requests | LLM/embedding responses | AI gateway | AI worker | Host model/runtime state | Server Ollama frozen until ISI-28 | NO | YES | tests/test_isi_server_deployment_contract.py; ISI-25 eval | REQUIRED_COMPATIBILITY | ISI-25 / ISI-28 | Promoted models only after evaluation; server mutation only ISI-28 |
| INV-J15 | Final owner target endpoint | Deployment target | TARGET | MasterPlan SYSTEM INVENTORY | Owner target for ISI alongside Krcuga 8443 and OralScan 8444 | Central ingress + DNS | https://isi.opus.rs:8445 target endpoint | Owner deployment decision | Users | DNS/TLS/ingress | Server/DNS/ingress mutation only ISI-28 | YES | YES | Future ISI-28 acceptance | NONE | ISI-28 | If server audit requires change, update MasterPlan by explicit owner approval before deployment  ISI public/app/API routes HTTPS verified; shared config/non-target identities preserved; no further shared ingress mutation |
| INV-J16 | local compose: postgres | Development Compose service | DEVELOPMENT_ONLY | docker-compose.yml | Local PostgreSQL 17 development service | Local env + volume | Development DB | Local Compose | api/worker | isi_postgres_data volume | Developer-local only; default password is not production authority | NO | NO | Compose CI/quality checks | NONE | DEVELOPMENT | May change with local developer topology; never infer production config from defaults |
| INV-J17 | local compose: redis | Development Compose service | DEVELOPMENT_ONLY | docker-compose.yml | Local Redis 7 development queue service | Local network + volume | Development Redis | Local Compose | worker/api | isi_redis_data volume | Developer-local only | NO | NO | Compose CI/quality checks | NONE | DEVELOPMENT | May change with local developer topology |
| INV-J18 | local compose: api | Development Compose service | DEVELOPMENT_ONLY | docker-compose.yml | Local FastAPI service | Local DB/Redis config | HTTP API on configurable local port | postgres/redis | streamlit/local clients | External dev stores | Developer-local exposure only | YES | NO | Compose CI/quality checks | NONE | DEVELOPMENT | Not a production deployment contract |
| INV-J19 | local compose: streamlit | Development Compose service | DEVELOPMENT_ONLY | docker-compose.yml | Local Streamlit service | Local API URL | UI on configurable local port | api | developer browser | Session state | Developer-local exposure only | YES | NO | Compose CI/quality checks | NONE | DEVELOPMENT | Not a production deployment contract |
| INV-J20 | local compose: worker | Development Compose service | DEVELOPMENT_ONLY | docker-compose.yml; src/workers/worker.py | Combined local worker entrypoint | Local DB/Redis | Background processing | postgres/redis | Data/AI jobs as wired by entrypoint | DB/queue runtime | Developer-local internal service | NO | NO | Compose CI/quality checks | REQUIRED_COMPATIBILITY | DEVELOPMENT | Can be replaced by split workers if local topology follows canonical queue ownership |
| INV-J21 | staging compose: postgres | Historical staging Compose service | HISTORICAL | docker-compose.staging.yml | Old ISI-15 PostgreSQL staging service retained as acceptance evidence | Historical staging env | Staging DB service | Historical ISI-15 compose | staging api/workers/migrate | postgres_data volume | DO NOT EXECUTE as current workflow; historical local-only contract | NO | NO | tests/test_isi_15_compose_contract.py | LEGITIMATE_HISTORY | ISI-28 | Retire or replace only after ISI-28 fresh deployment contract supersedes compatibility tests |
| INV-J22 | staging compose: redis | Historical staging Compose service | HISTORICAL | docker-compose.staging.yml | Old ISI-15 Redis staging service retained as acceptance evidence | Historical staging env | Staging queue service | Historical ISI-15 compose | staging workers | redis_data volume | DO NOT EXECUTE as current workflow | NO | NO | tests/test_isi_15_compose_contract.py | LEGITIMATE_HISTORY | ISI-28 | Retire with historical staging compatibility layer |
| INV-J23 | staging compose: minio | Historical staging Compose service | HISTORICAL | docker-compose.staging.yml | Old ISI-15 MinIO staging object store | Historical staging env | Staging S3 endpoint | Historical ISI-15 compose | staging api/data-worker | minio_data volume | DO NOT EXECUTE as current workflow; credentials historical example only | NO | NO | tests/test_isi_15_compose_contract.py | LEGITIMATE_HISTORY | ISI-28 | Retire with historical staging compatibility layer |
| INV-J24 | staging compose: minio-init | Historical staging Compose init service | HISTORICAL | docker-compose.staging.yml | Old ISI-15 staging bucket initializer | Historical MinIO readiness/config | Bucket init | staging minio | staging app services | MinIO state | DO NOT EXECUTE as current workflow | NO | NO | tests/test_isi_15_compose_contract.py | LEGITIMATE_HISTORY | ISI-28 | Retire with historical staging compatibility layer |
| INV-J25 | staging compose: mailpit | Historical staging Compose service | HISTORICAL | docker-compose.staging.yml | Old ISI-15 SMTP sink | Historical test mail | Captured staging mail | staging api | historical QA | mailpit_data volume | DO NOT EXECUTE as production SMTP | NO | NO | tests/test_isi_15_compose_contract.py; tests/test_isi_15_delivery.py | LEGITIMATE_HISTORY | ISI-28 | Must not become production mail provider |
| INV-J26 | staging compose: migrate | Historical staging Compose init service | HISTORICAL | docker-compose.staging.yml | Old ISI-15 Alembic migration gate | Historical app image + DB | Schema migration | staging postgres | staging app services | PostgreSQL schema | DO NOT EXECUTE as current deployment authority | NO | NO | tests/test_isi_15_compose_contract.py | LEGITIMATE_HISTORY | ISI-28 | Fresh ISI-28 migration plan supersedes it |
| INV-J27 | staging compose: api | Historical staging Compose service | HISTORICAL | docker-compose.staging.yml | Old ISI-15 FastAPI staging service | Historical staging env | Staging API | staging stores/migrate | staging streamlit/nginx | Historical staging state | DO NOT EXECUTE as current workflow | YES | NO | tests/test_isi_15_compose_contract.py | LEGITIMATE_HISTORY | ISI-28 | Fresh ISI-28 runtime contract supersedes it |
| INV-J28 | staging compose: streamlit | Historical staging Compose service | HISTORICAL | docker-compose.staging.yml | Old ISI-15 Streamlit staging service under /app | Historical API | Staging UI | staging api | staging nginx | Session state | DO NOT EXECUTE as current workflow | YES | NO | tests/test_isi_15_compose_contract.py | LEGITIMATE_HISTORY | ISI-28 | Fresh ISI-28 runtime contract supersedes it |
| INV-J29 | staging compose: data-worker | Historical staging Compose service | HISTORICAL | docker-compose.staging.yml | Old ISI-15 split data worker | Historical DB/Redis/S3 | Processed data jobs | staging stores/migrate | data platform | Historical DB/object state | DO NOT EXECUTE as current workflow | NO | NO | tests/test_isi_15_compose_contract.py | LEGITIMATE_HISTORY | ISI-28 | Fresh ISI-28 worker topology supersedes it |
| INV-J30 | staging compose: ai-worker | Historical staging Compose service | HISTORICAL | docker-compose.staging.yml | Old ISI-15 split AI worker | Historical DB/Redis | AI processing | staging stores/migrate | AI platform | Historical DB/provider state | DO NOT EXECUTE as current workflow | NO | NO | tests/test_isi_15_compose_contract.py | LEGITIMATE_HISTORY | ISI-28 | Fresh ISI-28 worker topology supersedes it |
| INV-J31 | staging compose: nginx | Historical staging Compose edge service | HISTORICAL | docker-compose.staging.yml; docker/nginx/isi15-staging.conf | Old local ISI-15 TLS/noindex reverse proxy on default 8443 | Historical api/streamlit | Historical local HTTPS | staging app services | historical QA | Nginx config/certs | DO NOT EXECUTE as current ingress authority | NO | NO | tests/test_isi_15_compose_contract.py | LEGITIMATE_HISTORY | ISI-28 | Retire when historical staging acceptance layer is deliberately removed |
| INV-J32 | Immutable release candidate bundle | Release artifact | DEVELOPMENT_ONLY | tools/release/build.py; tools/release/assemble.py; docs/release/ISI-RELEASE-SUPPLY-CHAIN.md; docker/runtime-base.lock.json | Preserve source, exact pinned-base image, runtime compatibility, evidence and provenance identity | Committed exact main and blocking gate evidence | Archive, manifest, dependency/image SBOMs, image scan, API/Streamlit probe, provenance, checksums | INV-M20 / INV-M21 / INV-J33 | Controlled ISI-28 deployment | Immutable ignored local directory / bounded CI artifacts | Signature verification and artifact hash/runtime compatibility checks required before deployment | NO | YES | tests/test_isi_27c_release_supply_chain.py; tests/test_isi_27c_runtime_image_contract.py | NONE | ISI-27C / ISI-28 | No deployment performed by artifact generation |
| INV-J33 | Wolfi Python runtime substrate | Image build/runtime component | DEVELOPMENT_ONLY | docker/Dockerfile; docker/runtime-base.lock.json | Pinned minimal glibc runtime base; application build uses a separate stage | Supplier image digest and pinned Python packages | Exact ISI runtime image | Chainguard Wolfi base and Python package repository | API; Streamlit; migration and workers | Release image layers and CycloneDX image SBOM | Same supplier repository; no build tools in final virtual environment; HIGH/CRITICAL image scan blocks | NO | YES | tests/test_isi_27c_runtime_image_contract.py; Trivy 0.75.0; disposable API/Streamlit checks | NONE | ISI-27C / ISI-28 | Development candidate only until exact-source acceptance; production verification and deployment are ISI-28 |
| INV-J34 | ISI release-bound host monitoring | Host operations candidate | TARGET | tools/server/isi28_operations.py; automation/specs/ISI-28-R3-OPERATIONS-AND-RESPONSIVE-CLOSEOUT.md | Read-only monitoring of fixed ISI targets during preproduction testing | Protected deployed-release lock | Sanitized local status | Exact accepted ISI image/config | GoraNova operations role | ISI runtime status only | No service mutations/backups/purge/outbound alerts; backups owner-deferred | NO | YES | tests/test_isi_28_operations.py | NONE | ISI-28 | R3 candidate; no installed monitoring timer claimed |

#### K. CONFIGURATION

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-K01 | Environment/deployment/log family | Configuration family | CURRENT_AS_BUILT | src/core/config.py; .env.example | ISI_ENV/ISI_DEPLOYMENT_PROFILE/ISI_LOG_LEVEL | Environment values | Runtime mode/logging | Process environment | All services | Environment variables | Production values are deployment-controlled | NO | YES | tests/test_isi_14_production_config_contract.py | NONE | ISI-27 / ISI-28 | No secret defaults in production |
| INV-K02 | Database family | Configuration family | CURRENT_AS_BUILT | src/core/config.py; .env.example | DATABASE_URL | Connection string | DB connection | Deployment | All persistence | Environment secret/reference | Credential secret | NO | YES | migration/native PostgreSQL tests | NONE | ISI-28 | Final URL only on server/secret store |
| INV-K03 | Redis family | Configuration family | CURRENT_AS_BUILT | src/core/config.py; .env.example | REDIS_URL | Connection string | Queue transport | Deployment | RQ queues/workers | Environment | Internal credential/network boundary | NO | YES | tests/test_isi_15_runtime_config.py | NONE | ISI-28 | Final DB number/URL from server plan |
| INV-K04 | Data storage family | Configuration family | CURRENT_AS_BUILT | src/core/config.py; .env.example | DATA_STORAGE_BACKEND/ROOT/S3_* | Backend/storage settings | Storage backend | Deployment | Data platform | Environment | S3 credentials secret | NO | YES | tests/test_isi_06_storage.py; tests/test_isi_15_storage.py | NONE | ISI-22 / ISI-28 | Production selects s3-compatible unless explicit change |
| INV-K05 | Data ingestion limits/job family | Configuration family | CURRENT_AS_BUILT | src/core/config.py | DATA_JOB_BACKEND/DATA_MAX_UPLOAD_BYTES/DATA_MAX_XLSX_UNCOMPRESSED_BYTES | Job/size settings | Queue/validation behavior | Deployment | Data service/worker | Environment | Protect resource boundary; no auth semantics | NO | YES | tests/test_isi_06*.py | NONE | ISI-22 / ISI-26 | Tune only with performance evidence |
| INV-K06 | AI job/provider family | Configuration family | CURRENT_AS_BUILT | src/core/config.py | AI_JOB_BACKEND/AI_PROVIDER_DEFAULT | Backend/provider choice | Queue/gateway behavior | Deployment | AI service/workers | Environment | Provider policy must still authorize configured choice | NO | YES | tests/test_isi_07*.py | NONE | ISI-25 / ISI-28 | Config cannot bypass policy registry |
| INV-K07 | Ollama model/runtime family | Configuration family | CURRENT_AS_BUILT | src/core/config.py | AI_OLLAMA_BASE_URL/AI_OLLAMA_CHAT_MODEL/AI_OLLAMA_EMBEDDING_MODEL/AI_REQUEST_TIMEOUT_SECONDS/AI_OLLAMA_NUM_THREAD | Runtime/model settings | Provider requests | Deployment/model registry | AI gateway | Environment + model registry | Server model mutation frozen until ISI-28 | NO | YES | tests/test_isi_07*.py | NONE | ISI-25 / ISI-28 | Model registry/eval is authority, env default alone is not promotion |
| INV-K08 | AI policy/dev-stub/request-text family | Configuration family | CURRENT_AS_BUILT | src/core/config.py | AI_DEFAULT_POLICY/AI_ALLOW_DEV_STUB/AI_STORE_REQUEST_TEXT | Policy/storage flags | AI safety behavior | Deployment | AI service | Environment + PostgreSQL | Sensitive-data policy and production stub prohibition | NO | YES | tests/test_isi_07_policy.py | NONE | ISI-25 | Stale flags audited every bootstrap; dev stub false in production |
| INV-K09 | Observability family | Configuration family | CURRENT_AS_BUILT | src/core/config.py | OBSERVABILITY_HTTP_METRICS_ENABLED | Metrics exposure flag | Diagnostics behavior | Deployment | Observability | Environment | Metrics endpoint exposure controlled | NO | NO | tests/test_isi_18*.py | NONE | ISI-18 / ISI-26 | Production exposure requires ingress/security decision |
| INV-K10 | API/UI/base URL family | Configuration family | CURRENT_AS_BUILT | src/core/config.py | API_HOST/API_PORT/STREAMLIT_PORT/PUBLIC_BASE_URL/APP_BASE_URL | Bind and link targets | HTTP runtime/link generation | Deployment | API/UI/auth email links | Environment | Public URL/host trust boundary | NO | YES | tests/test_isi_14_production_config_contract.py; tests/test_isi_15_runtime_config.py | NONE | ISI-28 | Production values must reconcile with `https://isi.opus.rs:8445/` and the shared central-Nginx route |
| INV-K11 | Public draft preview family | Configuration family | CURRENT_AS_BUILT | src/core/config.py | PUBLIC_PREVIEW_DRAFTS | Draft preview behavior | Public-content visibility | Deployment | Public site | Environment | Must never leak draft content in production | NO | YES | tests/test_isi_04c*.py; tests/test_isi_15_legacy_migration_contract.py | NONE | FOUNDATION / ISI-28 | Production default false unless explicit protected preview design |
| INV-K12 | Auth TTL/session family | Configuration family | CURRENT_AS_BUILT | src/core/config.py | AUTH_SESSION_TTL_SECONDS/AUTH_SESSION_IDLE_TTL_SECONDS/AUTH_EMAIL_VERIFICATION_TTL_SECONDS/AUTH_PASSWORD_RESET_TTL_SECONDS/AUTH_INVITATION_TTL_SECONDS | Token/session lifetimes | Expiry behavior | Security config | AuthService | Environment + AuthSession/AuthToken | Security-critical values | NO | YES | tests/test_isi_14_session_contract.py; tests/test_isi_20_session_management.py | NONE | ISI-20 | Changes require security review |
| INV-K13 | Login/security host family | Configuration family | CURRENT_AS_BUILT | src/core/config.py | SECURITY_LOGIN_WINDOW_SECONDS/MAX_FAILURES/BLOCK_SECONDS/IDENTIFIER_PEPPER/ALLOWED_HOSTS/TRUST_PROXY_HEADERS | Abuse and request-origin controls | Security decisions | Deployment | SecurityService/API | Environment | Pepper secret; proxy/host trust security-critical | NO | YES | tests/test_isi_14_rate_limit_contract.py; tests/test_isi_14_headers_contract.py | NONE | ISI-20 / ISI-28 | Production proxy/host values from final ingress |
| INV-K14 | Auth delivery/SMTP family | Configuration family | CURRENT_AS_BUILT | src/core/config.py; src/platform/auth/delivery.py | AUTH_DELIVERY_MODE/SMTP_* | Delivery settings/credentials | Null or SMTP adapter | Deployment | AuthDelivery | Environment + external SMTP | SMTP credentials secret; null forbidden for production delivery | NO | YES | tests/test_isi_15_delivery.py | NONE | ISI-28 | Real SMTP configured only in approved deployment |
| INV-K15 | Build and release-signing metadata | Configuration family | DEVELOPMENT_ONLY | docker/Dockerfile; docker/runtime-base.lock.json; tools/release/provenance.py; tools/release/allowed_signers | ISI_GIT_SHA/candidate/base-lock OCI identity and isi-release signing namespace | Exact Git commit and existing owner public keys | Image revision and signature validation | Release builder / existing SSH agent | Release verification | OCI metadata / public signer file | No private key committed or hosted; no production credentials | NO | YES | tests/test_isi_27c_release_supply_chain.py | NONE | ISI-27C | Only existing GitHub owner identities are trusted |

#### L. EXTERNAL INTEGRATIONS

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-L01 | Ollama HTTP runtime | External integration | CURRENT_AS_BUILT | src/platform/ai/providers.py; src/core/config.py | Local model inference/embedding over HTTP | AI request | Model response | AIGateway | AI worker | External host process | Policy-controlled local endpoint | NO | YES | tests/test_isi_07*.py | NONE | ISI-25 / ISI-28 | Server endpoint/models frozen until ISI-28 |
| INV-L02 | SMTP server | External integration | NOT_CONFIGURED | src/platform/auth/delivery.py; src/core/config.py | Production auth email delivery adapter exists but real server not canonicalized in repo | Email messages | Delivery outcome | AuthDelivery | User mailbox | External SMTP | Credentials/private transport; production frozen | NO | YES | tests/test_isi_15_delivery.py | NONE | ISI-28 | Configure real provider only during owner-approved deployment |
| INV-L03 | S3-compatible API / MinIO | External/internal service integration | CURRENT_AS_BUILT | src/platform/data/storage.py | Object store API | Scoped payload bytes | Object operations | Storage abstraction | Data platform/recovery | MinIO/S3 | Credentials + safe scoped keys | NO | YES | tests/test_isi_15_storage.py | NONE | ISI-28 | Final endpoint/credentials from deployment |
| INV-L04 | Redis/RQ | External/internal service integration | CURRENT_AS_BUILT | src/platform/data/queue.py; src/platform/ai/queue.py | Queue transport | Persisted job IDs | RQ jobs | Services | Workers | Redis | Internal network; not business authority | NO | YES | tests/test_isi_15_compose_contract.py | NONE | ISI-26 / ISI-28 | Scale/tune after load evidence |
| INV-L05 | GitHub Actions | Development integration | CURRENT_AS_BUILT | .github/workflows/ci.yml | Exact-main blocking repository acceptance | Committed main SHA | CI evidence | GitHub source control | Development lifecycle | GitHub run metadata/artifacts | No production secrets/deployment before ISI-28 | NO | YES | tests/test_isi_17_harness_contract.py | NONE | ISI-17 / ISI-27 | Required acceptance may not be weakened |
| INV-L06 | External AI provider | External integration | NOT_CONFIGURED | src/platform/ai/gateway.py | No active external provider configured | N/A | Fail closed | AI registry | None | None | Explicit privacy/security/provider approval required | NO | NO | tests/test_isi_07_policy.py | NONE | Future explicit ISI-25 decision | Must pass provider/privacy/eval/secret-management contract |
| INV-L07 | Live external research/knowledge provider | External integration | NOT_PRESENT | src/knowledge/models.py contains provenance/source URI only; no live retrieval adapter | No active web/research provider integration | N/A | N/A | Knowledge registry | Potential future RAG ingestion | None | No outbound fetch authority exists | NO | NO | SYSTEM INVENTORY contract | NONE | Future explicit ISI-25/data task | Requires allowlist, provenance, licensing, privacy and reproducibility design |
| INV-L08 | PayPal/payment provider | External integration | NOT_PRESENT | No current repository implementation | No payment provider integration | N/A | N/A | N/A | N/A | None | Do not import payment callbacks/webhooks from other products | NO | NO | SYSTEM INVENTORY contract | NONE | OUT OF CURRENT PRODUCT SCOPE | Owner-approved product/billing architecture required first |
| INV-L09 | Shared central Nginx ingress | External host integration | TARGET | MasterPlan; ADR-0026; server configuration outside repo until ISI-28 | Final shared ingress/TLS for `https://isi.opus.rs:8445/` using `central-ingress-nginx-1` | DNS/cert/upstream config | Public HTTPS | Host infrastructure | `isi-api` / `isi-streamlit` | Server config | Privileged deployment boundary | YES | YES | Future ISI-28 acceptance | NONE | ISI-28 | Fresh read-only server audit must verify the existing shared edge and ISI route before any mutation; Krcuga and OralScanXAI must remain unaffected  ISI public/app/API routes HTTPS verified; shared config/non-target identities preserved; no further shared ingress mutation |

#### M. TEST / QA AUTHORITY MAP

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-M01 | Architecture/health authority | Test authority | CURRENT_AS_BUILT | tests/test_architecture_contract.py; tests/test_health.py | Core architecture and health contracts | Repository/runtime contract | Pass/fail | Core code | CI | Test evidence | No production access | NO | YES | Self | NONE | ISI-17 | Update with architecture boundary changes |
| INV-M02 | Identity/access/auth/context authority | Test authority | CURRENT_AS_BUILT | tests/test_isi_02a*.py; tests/test_isi_02b*.py; tests/test_isi_02c*.py | Identity/RBAC/auth/context foundations | Core access/auth code | Pass/fail | Platform foundation | CI | Test DB/native PostgreSQL | Security-critical | NO | YES | Self | NONE | ISI-20 | Must remain blocking |
| INV-M03 | Public migration/content/site authority | Test authority | CURRENT_AS_BUILT | tests/test_isi_03*.py; tests/test_isi_04*.py | Legacy migration, public content, public web safety | Public/migration code | Pass/fail | Public stack | CI | Fixtures/test DB | Draft/public boundary | NO | YES | Self | LEGITIMATE_HISTORY | FOUNDATION | Historical fixtures may remain while provenance contracts need them |
| INV-M04 | App shell authority | Test authority | CURRENT_AS_BUILT | tests/test_isi_05*.py | Authenticated shell/navigation/selection | App shell code | Pass/fail | Access/context | CI | Test DB | Permission navigation contract | NO | YES | Self | NONE | FOUNDATION | Update with user-surface inventory changes  ISI-30A owner-authorized workflow-shell candidate, exact automation/specs/ISI-30A-WORKFLOW-SHELL.md; scope transitions/design and existing ORDO scenario reachability; no backend authority change. |
| INV-M05 | Shared data foundation authority | Test authority | CURRENT_AS_BUILT | tests/test_isi_06*.py | Data source/upload/storage/job baseline | Data platform | Pass/fail | Data code | CI | Fixtures/test DB/storage | Data scope/storage safety | NO | YES | Self | NONE | ISI-22 | Blocking for data changes |
| INV-M06 | AI foundation authority | Test authority | CURRENT_AS_BUILT | tests/test_isi_07*.py | AI registry/provider/policy/namespaces/structured output | AI platform | Pass/fail | AI code | CI | Test DB/stubs | AI policy/security | NO | YES | Self | NONE | ISI-25 | Provider/eval changes add focused tests here or named successor suite |
| INV-M07 | SIMPA domain authority | Test authority | CURRENT_AS_BUILT | tests/test_isi_08*.py; tests/test_isi_09*.py; tests/test_isi_23a*.py; tests/test_isi_23b*.py; tests/test_isi_23c*.py; tests/test_isi_23d*.py | SIMPA domain, governed analytics, methodology/reference lifecycle, deterministic model families, uncertainty/diagnostics/calibration and Help/XAI guards | SIMPA code | Pass/fail | SIMPA | CI | Test DB/reference/statistical/Help fixtures/native PostgreSQL | SIMPA-only scope, evidence immutability, non-causal aggregate-only execution, faithful unsupported-XAI states and human approval safety | NO | YES | Self | REQUIRED_COMPATIBILITY | ISI-23 | ISI-23D adds Help/XAI coverage and p-value compatibility; ISI-25 evaluation/promotion is accepted separately;29D accepted95fec435 src/domains/simpa/attribution_service.py / src/streamlit_app/attribution_view.py, tests/test_isi_29d_*, local/native/browser and exact95fec435 CI passed |
| INV-M08 | ORDO domain authority | Test authority | CURRENT_AS_BUILT | tests/test_isi_10*.py; tests/test_isi_11*.py; tests/test_isi_24a*.py; tests/test_isi_24b*.py; tests/test_isi_24c*.py; tests/test_isi_24d*.py; tests/test_isi_24e*.py | ORDO domain, governed evidence/GIS, analytics/scenarios, deterministic forecast runtime, governed customer forecast workflow and faithful Help/XAI/closeout guards | ORDO code/governance | Pass/fail | ORDO | CI | Test DB/fixtures/forecast/Help evidence/native PostgreSQL | ORDO-only scope; human evidence lifecycle; scenario/forecast/non-causal/NOT_ESTIMATED guard; permission-separated spec lifecycle/execution | NO | YES | Self | NONE | ISI-24 | Historical compatibility remains truthful; 24E closes the customer-workflow gap without automatic selection/fallback or causal/policy authority; shared AI evaluation/promotion remains ISI-25 |
| INV-M09 | Reporting authority | Test authority | CURRENT_AS_BUILT | tests/test_isi_12*.py ; src/platform/reporting/linked_evidence.py; src/domains/{simpa,ordo}/report_evidence.py; src/streamlit_app/linked_reporting_workspace.py; docs/help/ISI-LINKED-REPORTS-GUIDE.md | Report provenance/lifecycle/render/safety/UI | Reporting code | Pass/fail | Reporting | CI | Test DB | Report scope/provenance | NO | YES | Self ; tests/test_isi_29f_* | NONE | ISI-27 | 29F accepted software f587ed0: accepted claim/source/dated geometry and optional exact domain result/XAI; human contextual association; source/auth/integrity revalidated at read/lifecycle/export/download. Exact local/browser/manual/CI/signed release and scoped server gates PASS; full-production gates remain open. |
| INV-M10 | Administration/security baseline authority | Test authority | CURRENT_AS_BUILT | tests/test_isi_13*.py; tests/test_isi_14*.py | Admin/auth delivery/headers/rate/session configuration | Admin/security code | Pass/fail | Security platform | CI | Test DB/config | Security-critical | NO | YES | Self | NONE | ISI-20 | Blocking |
| INV-M11 | ISI-15 compatibility authority | Test authority | COMPATIBILITY | tests/test_isi_15*.py | Production-shaped compose/storage/delivery/legacy-migration compatibility; task status is historical | Staging/deployment compatibility artifacts | Pass/fail | Historical ISI-15 artifacts | CI/ISI-28 audit | Fixtures/config | Must not authorize server execution | NO | YES | Self | REQUIRED_COMPATIBILITY | ISI-28 | Retire/replace only in controlled ISI-28 cleanup after equivalent final deployment tests |
| INV-M12 | Autonomous governance authority | Test authority | CURRENT_AS_BUILT | tests/test_isi_17_harness_contract.py; tools/ci/policy_check.py | MasterPlan/AGENTS/task/policy/CI governance | Governance docs/config | Pass/fail | Development control plane | CI | Repository files | No server; fail-closed policy | NO | YES | Self | NONE | ISI-17 | Every governance rule added here must be tested |
| INV-M13 | Observability/recovery authority | Test authority | CURRENT_AS_BUILT | tests/test_isi_18*.py; tests/test_isi_19*.py | Diagnostics/readiness/backup/restore/rehearsal | Ops code/tools; tools/server/isi28_operations.py | Pass/fail | Runtime/recovery | CI | Test artifacts | No production execution in normal CI | NO | YES | Self | NONE | ISI-18 / ISI-19 | Extend for new critical dependencies  R3 release-bound ISI-only read-only monitoring candidate; new backups owner-deferred during preproduction testing |
| INV-M14 | Enterprise security authority | Test authority | CURRENT_AS_BUILT | tests/test_isi_20*.py | RBAC/auth assurance/session/MFA/security event controls | Security code | Pass/fail | Security platform | CI | Test/native PostgreSQL | Highest security criticality | NO | YES | Self | NONE | ISI-20 | Cannot be weakened |
| INV-M15 | Data governance/privacy/analytical authority | Test authority | CURRENT_AS_BUILT | tests/test_isi_21*.py; tests/test_isi_21b*.py; tests/test_isi_21c*.py | Governance/privacy/export/AI eligibility/analytical lineage | Data governance code | Pass/fail | Data platform | CI | Test/native PostgreSQL | Tenant/privacy/AI-use boundary | NO | YES | Self | NONE | ISI-21 / ISI-22 | Blocking for governed analytical boundary |
| INV-M16 | Industrial data-boundary authority | Test authority | CURRENT_AS_BUILT | tests/test_isi_22a*.py; tests/test_isi_22b*.py; tests/test_isi_22c*.py; tests/test_isi_22d*.py; tests/test_isi_22e*.py; tests/test_isi_22f*.py; tests/test_isi_22g*.py | Connector/mapping/idempotence/record governance/operations, reproducible analytical boundary and enforced SIMPA/ORDO governed consumption | ISI-22 code | Pass/fail | Data ingestion, analytical and domain-consumption boundaries | CI | Test/native PostgreSQL | Governed ingestion through deterministic domain analytics critical path | NO | YES | Self | NONE | ISI-22 | Remains blocking; no raw/domain-observation analytics bypass; historical suites assert their own migration/compatibility contract rather than mutable global head |
| INV-M17 | Production workflow/server compatibility authority | Test authority | COMPATIBILITY | tests/test_isi_production_workflow_lock.py; tests/test_isi_server_deployment_contract.py; tests/test_isi_server_runtime_promotion.py | Ensure old execution path fails closed while deployment assets remain inspectable | Historical/compatibility server artifacts | Pass/fail | Server/deployment artifacts | CI/ISI-28 | Files only in normal CI | Must not contact/mutate server | NO | YES | Self | REQUIRED_COMPATIBILITY | ISI-28 | Convert from historical compatibility to final ISI-28 deployment acceptance |
| INV-M18 | Aggregate exact-main CI authority | Acceptance authority | CURRENT_AS_BUILT | .github/workflows/ci.yml; tools/ci/run_isi17_acceptance.sh | Block main acceptance unless all required jobs pass | Committed exact main SHA | CI_VERIFIED evidence | All test/quality/policy jobs | Development lifecycle | GitHub run metadata | No production deployment/secrets | NO | YES | Workflow + harness tests | NONE | ISI-17 / ISI-27 | Cannot be weakened to accept a defect |

| INV-M19 | Repository performance and resilience acceptance | Test authority | DEVELOPMENT_ONLY | tools/performance/**; tests/test_isi_26_*.py; docs/ops/ISI-26-PERFORMANCE-LOAD-RESILIENCE.md | Synthetic bounded workload catalogue, concurrent harness and privacy-safe evidence | Versioned synthetic fixtures | Fingerprinted contracts/counts/latencies | Existing API/data/domain/report/AI surfaces | Local runner; ISI-27 acceptance | Ephemeral SQLite and JSON evidence | No raw identifiers/secrets/payloads; no server/network capacity authority | NO | NO | tests/test_isi_26_*.py | NONE | ISI-26 / ISI-27 | Timing remains UNCALIBRATED until accepted local evidence; live capacity only ISI-28 |
| INV-M20 | Exact-candidate release evidence | Test authority | DEVELOPMENT_ONLY | tools/release/evidence.py; tools/qa/run_isi27b.py; tools/qa/analyze_isi27b.py; docs/release/ISI-RC-GOVERNANCE-PACK.md | Consolidate domain, model, security/privacy, native recovery and performance acceptance | Exact candidate and synthetic gate reports | Fingerprinted RC governance pack | Existing accepted test authorities | ISI-27B / ISI-27C | Ignored immutable evidence directory | No production data, no model promotion, no server authority | NO | NO | tests/test_isi_27b_release_evidence.py | NONE | ISI-27 | Accepted 27B main 16a928b; local/review evidence recorded; hosted acceptance remains 27D |
| INV-M21 | Reproducible release and supply-chain assurance | Release/test authority | DEVELOPMENT_ONLY | tools/release/build.py; tools/release/sbom.py; tools/release/provenance.py; tools/release/assemble.py; tools/release/allowed_signers; .github/workflows/ci.yml | Bind exact source, reports, SBOMs, image scan and signed provenance | Clean main and real acceptance outputs | Immutable checksummed release bundle | INV-M20 and blocking CI gates | ISI-27D / ISI-28 | Ignored local bundle and controlled CI artifacts | Pinned owner public identity; private keys never in CI/Git; fail-closed image scan | NO | YES | tests/test_isi_27c_release_supply_chain.py | NONE | ISI-27C / ISI-27D | Candidate acceptance/review required; no server authority |

#### N. LEGACY LEDGER

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-N01 | ISI-15 task ledger entry | Legacy record | HISTORICAL | automation/tasks.json | Historical production-readiness milestone only | Canonical history | Status=historical | Prior phases | ISI-28 historical audit | Repository ledger | Does not authorize server work | NO | NO | tests/test_isi_15_contract.py; policy_check | LEGITIMATE_HISTORY | ISI-28 | Keep history; never transition back to ready |
| INV-N02 | ISI-16 cutover task ledger entry | Legacy record | SUPERSEDED | automation/tasks.json | Superseded old production cutover sequence | Canonical history | Status=superseded | Old ISI-15 | ISI-28 only | Repository ledger | Does not authorize server work | NO | NO | tests/test_isi_15_contract.py; policy_check | LEGITIMATE_HISTORY | ISI-28 | Keep history; never execute legacy cutover |
| INV-N03 | Old Production Workflow Lock | Historical doc | SUPERSEDED | docs/ops/ISI-PRODUCTION-WORKFLOW-LOCK.md | Historical pointer only | Git history | DO NOT EXECUTE pointer | Old ISI-15/16 | MasterPlan | Repository file | Explicitly non-executable | NO | NO | tests/test_isi_production_workflow_lock.py; policy_check | LEGITIMATE_HISTORY | ISI-28 | May be removed only after no compatibility/reference need remains |
| INV-N04 | Old server deployment runbook | Historical doc | SUPERSEDED | docs/ops/ISI-SERVER-DEPLOYMENT-RUNBOOK.md | Historical pointer only | Git history | DO NOT EXECUTE pointer | Old ISI-15/16 | MasterPlan/ISI-28 | Repository file | Explicitly non-executable | NO | NO | policy_check; SYSTEM INVENTORY contract | LEGITIMATE_HISTORY | ISI-28 | Do not reuse historical commands/ports/migration heads |
| INV-N05 | Old ISI-15 staging runbook | Historical doc | SUPERSEDED | docs/ops/ISI-15-STAGING-RUNBOOK.md | Historical pointer only | Git history | DO NOT EXECUTE pointer | Old ISI-15 | MasterPlan | Repository file | Explicitly non-executable | NO | NO | policy_check | LEGITIMATE_HISTORY | ISI-28 | Remove only after references retired |
| INV-N06 | Old ISI-15 staging spec | Historical spec | SUPERSEDED | automation/specs/ISI-15-PRODUCTION-STAGING.md | Historical readiness baseline pointer | Git history | DO NOT EXECUTE pointer | Old ISI-15 | MasterPlan | Repository file | Explicitly non-executable | NO | NO | tests/test_isi_15_contract.py; policy_check | LEGITIMATE_HISTORY | ISI-28 | Never use locked old SHA/head/sequence as live authority |
| INV-N07 | ISI-16 nginx central-ingress template | Deployment compatibility artifact | HISTORICAL | deploy/central-ingress/isi-production-server.conf.fragment | Preserve old `isi.rs:8443` template only as audit history until fresh ISI-28 reconciliation | Old server plan | Historical config | Old deployment | ISI-28 audit | Repository file | Do not execute without fresh owner approval | NO | NO | tests/test_isi_server_deployment_contract.py | REQUIRED_COMPATIBILITY | ISI-28 | Replace/remove only after the final shared central-Nginx `https://isi.opus.rs:8445/` route is server-verified |
| INV-N08 | docker-compose.staging.yml | Staging compatibility artifact | COMPATIBILITY | docker-compose.staging.yml | Production-shaped local/preproduction contract and CI fixture | Env/test config | Staging topology | Historical ISI-15 | CI/ISI-28 audit | Local containers | Local-only; no production authority | NO | NO | tests/test_isi_15_compose_contract.py | REQUIRED_COMPATIBILITY | ISI-28 | Retire only after replacement acceptance environment exists |
| INV-N09 | isi15-staging nginx config | Staging compatibility artifact | COMPATIBILITY | docker/nginx/isi15-staging.conf | TLS/websocket/noindex staging fixture | Staging topology | Staging edge config | docker-compose.staging | Tests | Repository file | No production authority | NO | NO | tests/test_isi_15_compose_contract.py | REQUIRED_COMPATIBILITY | ISI-28 | Retire with staging compatibility layer |
| INV-N10 | public_migration toolset | Migration history/support | COMPATIBILITY | src/public_migration/** | Preserve legacy content provenance/import/redirect tooling | Legacy content artifacts | Migration evidence/content | Legacy public site | PublicContentService | Files/PostgreSQL | Offline safety; no implicit network/cutover | NO | NO | tests/test_isi_03*.py; tests/test_isi_15_legacy_migration_contract.py | LEGITIMATE_HISTORY | FOUNDATION / ISI-28 | Remove only after provenance/recovery requirement is closed |
| INV-N11 | Streamlit ISI-02C compatibility markers | Compatibility shim | COMPATIBILITY | src/streamlit_app/app.py | Keep historical route/label integration markers while tests/backward compatibility require | Legacy marker constants | No runtime authority change | Old integration contract | Current shell tests | Code constants | Must not override current API/shell authority | NO | NO | tests/test_isi_05_hotfix1_legacy_streamlit_contract.py | REQUIRED_COMPATIBILITY | FOUNDATION | Remove only with explicit compatibility-test migration |
| INV-N12 | .env.server.example precutover assumptions | Deployment compatibility artifact | COMPATIBILITY | .env.server.example | Documents old preproduction/server-shaped defaults, not final production truth | Historical deployment assumptions | Example config | ISI-15/16 | ISI-28 audit | Repository file | Contains placeholders only; not real secrets | NO | NO | tests/test_isi_server_deployment_contract.py | REQUIRED_COMPATIBILITY | ISI-28 | Replace with final production example after fresh server topology approval |
| INV-N13 | Fail-closed local staging launcher | Safety sentinel | HISTORICAL | tools/staging/run_isi15_staging_qa.sh | Prevent accidental old local Docker staging execution | Operator invocation | Exit 64 / warning | Old ISI-15 | Safety | None | Safety guard; no production access | NO | NO | tests/test_isi_production_workflow_lock.py | LEGITIMATE_HISTORY | ISI-28 | Keep until old workflow references are fully retired |
| INV-N14 | Historical tests freezing mutable global state | Legacy anti-pattern | SUPERSEDED | Git history; ISI-22E R1/R2 precedent | Document forbidden test pattern | Old tests | Removed/repaired tests | Historical phases | Governance policy | Git history | No current runtime effect | NO | NO | tests/test_isi_17_harness_contract.py; policy_check | LEGITIMATE_HISTORY | ISI-17 | Never reintroduce tests that assert mutable global Alembic head or stale live status |

### 0.7A Owner-requested XAI/GIS/entity-findings target extension — 2026-10-07

These are TARGET components, not new as-built capability. Existing inventory and accepted historical scopes remain authoritative. Details: `docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md`.

| ID | NAME | TYPE | STATUS | CANONICAL PATH(S) | RESPONSIBILITY | INPUTS | OUTPUTS | UPSTREAM | DOWNSTREAM | DATA/PERSISTENCE | SECURITY BOUNDARY | CUSTOMER-FACING | PRODUCTION_CRITICAL | TEST AUTHORITY | LEGACY STATUS | ROADMAP OWNER | REMOVAL/REPLACEMENT RULE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INV-A22 | SIMPA/ORDO graphical XAI and GIS-linked findings | Customer surface | CURRENT_AS_BUILT | docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md; automation/specs/ISI-29A-GRAPHICAL-XAI.md ; src/platform/reporting/linked_evidence.py; src/domains/{simpa,ordo}/report_evidence.py; src/streamlit_app/linked_reporting_workspace.py; docs/help/ISI-LINKED-REPORTS-GUIDE.md | Linked charts/maps/evidence review; domain semantics remain separate | Governed persisted results and reviewed scoped spatial/claim evidence | Accessible charts/maps/tables and review/report trace | Existing analytics and future 29 spatial/extraction adapters | SIMPA/ORDO users and reporting | Existing results; later versioned artifacts | Existing tenant/product/workspace RBAC and privacy | YES | YES | tests/test_isi_29a_*; tests/test_isi_29b_*; tests/test_isi_29c_*; tests/test_isi_29d_*; tests/test_isi_29e_*;29F accepted f587ed0 ; tests/test_isi_29f_* | NONE | ISI-29 | 29F accepted software f587ed0: accepted claim/source/dated geometry and optional exact domain result/XAI; human contextual association; source/auth/integrity revalidated at read/lifecycle/export/download. Exact local/browser/manual/CI/signed release and scoped server gates PASS; full-production gates remain open. |
| INV-B29 | Shared spatial/extraction infrastructure with domain adapters | Service boundary | CURRENT_AS_BUILT | src/platform/spatial/**; src/domains/simpa/spatial_adapter.py; src/domains/ordo/spatial_adapter.py; src/api/spatial_routes.py ; src/platform/extraction/**; src/api/extraction_routes.py; src/domains/{simpa,ordo}/extraction_adapter.py | Generic geometry/extraction transport and job infrastructure; SIMPA/ORDO own domain intelligence | Versioned source artifacts and scoped policy | Validated artifact identities and unverified candidates | Data platform/storage/AI gateway/RQ | Separate SIMPA/ORDO adapters and reviewers | Scoped PostgreSQL metadata/content-addressed geometry;29E immutable relational extraction metadata | No cross-product private entity sharing or external geocoder by default | NO | YES | Planned ISI-29B/E migration/security/evaluation gates ; tests/test_isi_29e_* | NONE | ISI-29B / ISI-29E | 29E src/platform/extraction/** and src/api/extraction_routes.py shared transport/persistence only; separate src/domains/{simpa,ordo}/extraction_adapter.py prompts and scoped registries; no new providers/models/dependencies. |
| INV-C45 | Geometry/entity/claim/XAI artifact extensions | Evidence persistence | CURRENT_AS_BUILT | src/platform/spatial/models.py; migrations/versions/20261007_0035_spatial_geometry_versions.py ; src/platform/extraction/models.py; migrations/versions/20261008_0037_extraction.py; src/domains/simpa/attribution_service.py | Immutable geometry versions; anchored mentions/claims/reviews; model-specific attribution | Approved sources/model identities and review actors | Fingerprinted provenance and truthful unresolved/unavailable states | Existing governed output, model and spatial identity contracts | Scoped GIS/XAI/report workflows | Alembic-controlled relational metadata and scoped objects (0035 geometry,0036 attribution,0037 extraction) | Source invalidation/privacy and exact product/workspace isolation | NO | YES | Planned ISI-29B/D/E native migration, attribution and extraction gates ; tests/test_isi_29e_* | NONE | ISI-29 | 29D immutable OLS attribution accepted95fec435;29E additive0037 core_extraction_requests/artifacts/reviews with exact lineage, final attested review, human identity and polygon claim scope; no truth promotion. |
| INV-M22 | XAI/GIS/entity-findings acceptance authority | Test authority | CURRENT_AS_BUILT | automation/specs/ISI-29A-GRAPHICAL-XAI.md; docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md ; tools/qa/run_isi29e.py; tools/qa/analyze_isi29e.py ; src/platform/reporting/linked_evidence.py; src/domains/{simpa,ordo}/report_evidence.py; src/streamlit_app/linked_reporting_workspace.py; docs/help/ISI-LINKED-REPORTS-GUIDE.md | Chart parity, spatial correctness, SHAP fidelity, extraction evaluation and E2E | Exact candidates, approved fixtures and adjudicated corpus | Local evidence then approved exact-main CI | Existing domain/data/security/AI/report authority | Controlled later ISI-28 release | Ignored sanitized task evidence | No production payloads/secrets; fixtures not real-domain certification | NO | YES | Separate deterministic runners/read-only analyzers for29A-E;29F accepted f587ed0 ; tests/test_isi_29f_* | NONE | ISI-29 | 29F accepted software f587ed0: accepted claim/source/dated geometry and optional exact domain result/XAI; human contextual association; source/auth/integrity revalidated at read/lifecycle/export/download. Exact local/browser/manual/CI/signed release and scoped server gates PASS; full-production gates remain open. |

### 0.8 Accepted ISI-22E implementation checkpoint - 2026-09-13

At the accepted ISI-22E implementation SHA `44002aa0774a902bdf2d7a0ae56ff3558303571c` (tree `15578107fb21b6aae174a4bf77fc62812377949c`):

- ISI-17 through ISI-21 are complete in canonical history;
- ISI-22A `4047a1ef2ff3ac755d86947cfe666ee8507c9a0b` complete;
- ISI-22B `daeb5f2bbdb20bfed1be43f226ba13aa13e470aa` complete;
- ISI-22C `abbf6845864e5a61ff83fc7127739d9e68709077` complete;
- ISI-22D `6347ecde3cbb9a37a65ddbe7d5a6b3f35310b35d` complete;
- ISI-22E `44002aa0774a902bdf2d7a0ae56ff3558303571c` is `COMPLETE / CI_VERIFIED`;
- authoritative ISI-22E GitHub Actions is `ISI required acceptance` run #70, run ID `34774329038`, `completed / success`, with all blocking jobs and aggregate `acceptance` green;
- overall ISI-22 remains `IN_PROGRESS` until a whole-phase audit proves every MasterPlan deliverable complete;
- next action is a read-only whole-phase ISI-22 gap audit against this MasterPlan and actual code;
- any remaining ISI-22 implementation is grouped into at most two serious vertical packages rather than fragmented micro-slices;
- ISI-23 through ISI-28 remain serially pending;
- server verification/deployment remains deferred and the server remains frozen.

### 0.8.1 Accepted ISI-22F implementation checkpoint - 2026-09-14

At the accepted ISI-22F implementation SHA `cfe1574532df65589132bbdd10625172b32fb959` (tree `5afd978151a49d3f3ff897dd47481faf2438cbac`):

- ISI-22A through ISI-22E remain complete accepted predecessors;
- ISI-22F `cfe1574532df65589132bbdd10625172b32fb959` is `COMPLETE / CI_VERIFIED`;
- authoritative ISI-22F GitHub Actions is `ISI required acceptance` run #73, run ID `34787001102`, `completed / success`, with all blocking jobs and aggregate `acceptance` green;
- the mandatory whole-phase ISI-22 gap/legacy audit was completed before ISI-22F and resolved the remaining Phase 22 work into ISI-22F and ISI-22G;
- overall ISI-22 remains `IN_PROGRESS` until ISI-22G enforces governed domain consumption, proves no downstream raw-source bypass, completes synthetic SIMPA/ORDO E2E acceptance and closes the phase;
- current/next implementation slice is ISI-22G - Domain Consumption Enforcement + ISI-22 Closeout;
- ISI-23 through ISI-28 remain serially pending;
- server verification/deployment remains deferred and the server remains frozen.

### 0.8.2 Accepted ISI-22G implementation checkpoint and Phase-22 closeout - 2026-09-14

At the accepted ISI-22G implementation SHA `fd0e46631b5047c64b731d041645e528292f3664` (tree `1a405a65a6fa67f2845ee0a10f2a6f44b11e355e`):

- ISI-22G - Domain Consumption Enforcement + ISI-22 Closeout implementation is `COMPLETE / CI_VERIFIED`;
- authoritative ISI-22G GitHub Actions is `ISI required acceptance` run #75, run ID `34856573722`, `completed / success`, with policy, quality, tests, architecture-security, migration, native-postgres, compose, supply-chain, build and aggregate `acceptance` green;
- SIMPA and ORDO deterministic analytics now consume explicitly bound governed reproducible analytical artifacts rather than direct observation reads for new work;
- downstream compute, bounded AI synthesis, human review, scenario/reporting paths revalidate the governed analytical binding and fail closed for legacy, invalidated, tampered or cross-product inputs;
- synthetic SIMPA and ORDO acceptance proves the governed pipeline through deterministic analytics, AI provenance, human review and report-manifest provenance;
- historical pre-22G observation-derived runs remain `REQUIRED_COMPATIBILITY`: readable/listable but ineligible to authorize new compute/AI/scenario/report work;
- the mandatory Phase-22 gap/legacy findings are either resolved or retained only as classified `LEGITIMATE_HISTORY` / `REQUIRED_COMPATIBILITY`; there is no open `REMOVE_BEFORE_NEXT_SLICE` item from Phase 22;
- overall ISI-22 - Industrial Data Platform is `COMPLETE / CI_VERIFIED`;
- current/next work is ISI-23 - SIMPA Production Methodology + Help/User Guide;
- server verification/deployment remains deferred and the server remains frozen through ISI-27.

This governance-only synchronization records the accepted 22G implementation and Phase-22 closeout; it does not change production code or authorize server work.

### 0.9 Phase/task closeout synchronization gate

A task or phase cannot be closed while any of these are true:

- MasterPlan, AGENTS, tasks or STATUS are stale or mutually contradictory;
- known legacy/drift remains unclassified;
- a `REMOVE_BEFORE_NEXT_SLICE` finding remains unresolved;
- an assistant human-review blocker remains open;
- exact-main required CI has not passed;
- server/production mutation occurred outside an explicitly approved boundary;
- required Help/User Guide deliverables for ISI-23/24 are missing.

At closeout, update canonical planning/status records in the same controlled bookkeeping step so the next chat does not bootstrap from stale state.


## 1. Purpose

Industrialize the existing ISI platform and its two domain applications, SIMPA and ORDO, through specification-driven development while preserving the current server and deployment setup until a separately approved release/deployment phase.

The immediate objective is not a new infrastructure platform and not a new server. The objective is to make the codebase, data lifecycle, analytical methodology, AI lifecycle, security, quality assurance, observability, release engineering, and deployment automation sufficiently mature that a final release can later be pushed to the current server in one controlled upgrade.

## 2. Locked product model

- ISI is the institutional platform of the Institute for Social Inclusion.
- SIMPA and ORDO are the only domain applications in the current product architecture.
- SIMPA and ORDO remain domain-isolated while reusing shared infrastructure.
- COSMOS is not introduced as a software layer, product, domain, route, tenant, namespace, or menu item.
- Existing FastAPI + Streamlit + PostgreSQL + Redis/RQ + S3-compatible storage + shared AI gateway architecture is preserved unless a later accepted ADR explicitly changes it.
- Existing server topology remains the target deployment topology during this industrialization program.

## 3. Owner-driven direct-main development model

Normal development uses one canonical local repository, one worktree, and the local `main` branch only.

The binding execution chain is:

`specification -> direct implementation on canonical main -> deterministic local validation -> human review -> owner approval -> exact-file staging -> direct commit/push to main -> exact-main GitHub Actions verification -> next task`

Rules:

- Do not create feature, implementation, review, automation, or temporary branches unless the owner explicitly authorizes an exception.
- Do not create extra worktrees, clones, or alternate checkout workspaces for task isolation unless the owner explicitly authorizes an exception.
- Codex or another implementation agent may modify the canonical `main` worktree only within the task scope.
- Task changes remain unstaged and uncommitted until deterministic validation and human review are complete and the owner approves the exact candidate.
- No task is complete because an agent says it is complete. Completion is evidence-based.

### Verification labels

- `IMPLEMENTED`: an unstaged/uncommitted reviewed candidate exists on canonical `main` and required local/task gates pass as available.
- `REVIEW_VERIFIED`: review of the exact candidate or final main SHA has no unresolved technical blocker.
- `OWNER_APPROVED_MAIN_COMMIT`: the owner explicitly approved exact-file staging and commit/push to `main`.
- `CI_VERIFIED`: all blocking GitHub Actions jobs pass on the exact committed `main` SHA.
- `COMPLETE`: implementation, review, owner-approved main commit/push, and exact-main blocking CI are complete.
- `SERVER_VERIFIED`: explicitly approved server acceptance has passed.
- `DEFERRED_SERVER_VERIFICATION`: implementation is complete but the current task intentionally did not touch the server.

A failed required gate returns the active task to implementation/fix state. Required gates must not be weakened merely to obtain green status.

## 4. Server freeze during industrialization

Until the owner explicitly authorizes deployment:

- no SSH-based implementation work;
- no production DNS changes;
- no central-ingress changes;
- no production SMTP changes;
- no production credential changes;
- no server Ollama model mutation;
- no production data migrations;
- no automatic deployment;
- no use of production secrets in GitHub/Codex development context.

The current server is a deployment target only.

## 5. Canonical analytical AI architecture

The owner approved the analytical AI direction on 2026-09-12. ADR-0025 is the authoritative architecture decision for this layer.

The central invariant is:

**Numerical intelligence is computed by deterministic statistical/ML systems; documentary intelligence is extracted/retrieved with provenance; LLM/VLM systems synthesize and explain bounded evidence; humans approve institutional methodology and decisions.**

### 5.1 Three-engine architecture

Production analytical workflows are decomposed into three explicit layers:

1. deterministic statistical/ML engine - indicators, regression, classification, clustering, forecasting, scenario mathematics, uncertainty, calibration, diagnostics;
2. document AI/RAG engine - OCR/VLM extraction, embeddings, retrieval, evidence packaging and provenance;
3. LLM/VLM synthesis engine - bounded explanation, summarization, evidence synthesis, structured narrative and user-facing interpretation.

LLMs/VLMs must not silently calculate authoritative regressions, classifications, scores, forecasts, scenario impacts, eligibility, risk bands, or causal conclusions.

### 5.2 Shared technology, separate domain intelligence

SIMPA and ORDO share infrastructure services including data platform, AI gateway, job execution, model registry, audit, observability and deployment substrate.

They do not implicitly share:

- domain prompts;
- indicator definitions;
- methodology versions;
- feature contracts;
- trained domain models;
- private RAG namespaces;
- scoring semantics;
- forecast/scenario semantics;
- policy conclusions.

### 5.3 Evidence-first user experience

Every analytical view follows:

`Evidence -> Analytics -> Model outputs -> AI interpretation -> Human review`

Minimum presentation requirements where applicable:

- methodology/version;
- source/provenance;
- sample/time coverage;
- missing evidence;
- uncertainty/confidence intervals;
- model diagnostics/quality;
- explainability appropriate to model family;
- limitations;
- explicit human-review state.

### 5.4 SIMPA analytical boundary

SIMPA is a local social-protection intelligence and monitoring system operating at aggregate/system level.

Preferred unit of analysis:

`local system x indicator x period x monitoring cycle x source/provenance`

SIMPA must not become a citizen-level eligibility, benefit, diagnosis, automated-risk, or punitive decision engine.

Permitted analytical families, once their methodology is explicitly versioned and approved, include descriptive analysis, validated indicator computation, regression, system-level classification, trend analysis and unsupervised analytical profiling.

Ordinary regression/correlation must not be presented as causality.

### 5.5 ORDO analytical boundary

ORDO is a destination-intelligence, planning, forecasting and scenario-support system.

Forecast and scenario are distinct:

- forecast = model-based probabilistic estimate from validated historical data;
- scenario = user-authored assumptions combined with deterministic or validated transformations;
- scenario output must not be presented as forecast unless an approved response model exists.

If no validated impact model exists, the system reports `impact = NOT_ESTIMATED` rather than fabricating an effect.

Forecasts require temporal backtesting and uncertainty intervals.

### 5.6 Model selection and champion/challenger governance

No local model is permanently selected by name in this master plan.

Current owner-supplied MacBook models are evaluation candidates:

- `qwen3:1.7b-q4_K_M` - lightweight routing/tagging/extraction candidate;
- `qwen3:4b-instruct-2507-q4_K_M` - primary text-LLM candidate;
- `qwen3-vl:4b-instruct-q4_K_M` - primary VLM/document candidate;
- `qwen2.5vl:3b` - VLM challenger/fallback candidate;
- `qwen2.5:7b-instruct` - stronger/slower text challenger and existing QA baseline;
- `gemma3:4b` - independent cross-family challenger.

A dedicated multilingual embedding model is required for RAG. Initial candidates may include `qwen3-embedding:0.6b`, with larger or alternate multilingual challengers such as `qwen3-embedding:4b` or `bge-m3` if retrieval quality requires them. These are evaluation candidates, not an installation or production lock.

Each promoted model capability must have a stable key, version/checksum, dataset/eval-set version, methodology/feature/prompt version, validation metrics, approval state, rollback target and code SHA where applicable.

A challenger replaces a champion only after evidence-backed improvement on the relevant acceptance protocol.

### 5.7 Canonical evaluation sets

Create and version separate evaluation sets:

- `SIMPA-EVAL-v1`
- `ORDO-EVAL-v1`

LLM/VLM evaluation prioritizes grounded factuality, hallucination rate, structured-output validity, source/provenance compliance, Serbian-language quality, instruction compliance, reasoning quality, latency and resource footprint.

Statistical/ML evaluation uses problem-appropriate metrics, calibration where relevant, explicit baseline comparison and temporal validation for forecasts.

### 5.8 Human methodology approval boundary

No formula, weight, threshold, class definition, risk band, causal claim, forecast methodology, recommendation policy or production model may be represented as validated merely because it is implemented or AI-generated.

Methodology lifecycle is explicit, at minimum:

`DRAFT -> PROPOSED -> VALIDATED -> RETIRED`

Human approval and supporting evidence are mandatory for transition to `VALIDATED`.

## 6. Industrialization workstream

### ISI-17 - Autonomous Development Harness + CI

Goal: make the repository capable of governing autonomous development.

Status: completed in the canonical history.

Core deliverables include binding agent instructions, deterministic dependencies, blocking GitHub Actions gates, isolated migration/native PostgreSQL validation, supply-chain checks, policy guards and evidence conventions.

### ISI-18 - Observability & Operational Diagnostics

Goal: instrument the application so failures and degradation can be diagnosed before and after deployment.

Status: completed in the canonical history.

### ISI-19 - Backup, Restore & Disaster-Recovery Automation

Goal: make recovery deterministic and testable.

Status: completed in the canonical history.

### ISI-20 - Enterprise Security Completion

Goal: close the gap between baseline hardening and institutional-grade repository-side security controls.

Status: **COMPLETE / CI_VERIFIED**.

Completion record:

- implementation commit: `f4b3a3c2486a2d3a051a70d582245e199d1b36ba`;
- final canonical main SHA after the documentation-only wording adjustment is `61df1aa7622cb59ee60e2781fee98f8885324d55`;
- authoritative GitHub Actions: `ISI required acceptance` run #58, run ID `34655017377`;
- workflow conclusion: `success`;
- policy, quality, tests, architecture-security, migration, native-postgres, compose, supply-chain, build and aggregate acceptance all passed;
- server verification remains `DEFERRED_SERVER_VERIFICATION`;
- real-provider MFA and external penetration testing remain explicitly not performed.

### ISI-21 - Data Governance & Privacy Controls

Goal: make data ownership, provenance, sensitivity, retention, isolation and analytical-purpose governance explicit and enforceable.

Required deliverables now include:

- data classification model;
- dataset/source ownership metadata;
- lineage/provenance contracts;
- retention/purge/anonymization hooks;
- tenant/product boundary tests;
- auditability of sensitive data access;
- export controls;
- privacy-impact documentation pack;
- explicit rule that client/institution data never becomes cross-tenant/cross-product shared knowledge automatically;
- analytical-data purpose tags and sensitivity classes;
- feature provenance and feature-purpose governance hooks;
- dataset version identity sufficient for later reproducible SIMPA/ORDO model evaluation;
- rules for derived/aggregated data and de-identification state;
- explicit distinction between raw source, normalized record, analytical feature, indicator result, model output and AI narrative.

### ISI-22 - Industrial Data Platform

Goal: evolve ingestion from framework capability to robust production-grade data engineering and reproducible analytical datasets.

Status: **COMPLETE / CI_VERIFIED**. ISI-22A through ISI-22G are complete. The final ISI-22G domain-consumption slice is accepted on `fd0e46631b5047c64b731d041645e528292f3664` (tree `1a405a65a6fa67f2845ee0a10f2a6f44b11e355e`) with exact-main `ISI required acceptance` run #75 / `34856573722` completed `success`, including aggregate `acceptance`. ISI-23 - SIMPA Production Methodology is current/next.

Accepted checkpoints: 22A `4047a1ef2ff3ac755d86947cfe666ee8507c9a0b`; 22B `daeb5f2bbdb20bfed1be43f226ba13aa13e470aa`; 22C `abbf6845864e5a61ff83fc7127739d9e68709077`; 22D `6347ecde3cbb9a37a65ddbe7d5a6b3f35310b35d`; 22E `44002aa0774a902bdf2d7a0ae56ff3558303571c`; 22F `cfe1574532df65589132bbdd10625172b32fb959` with exact-main acceptance run #73 / `34787001102` success; 22G `fd0e46631b5047c64b731d041645e528292f3664` with exact-main acceptance run #75 / `34856573722` success.

Required deliverables include:

- versioned source connector contracts;
- schema mapping/versioning;
- incremental/idempotent imports;
- deduplication/reconciliation;
- quarantine/error queues;
- source freshness and quality checks;
- backfill support;
- ingestion lineage;
- standardized canonical ingestion boundary for SIMPA and ORDO;
- reference connector acceptance fixtures;
- canonical analytical dataset contracts;
- stable temporal/granularity keys;
- explicit missing-value semantics (`missing` is not silently converted to zero);
- feature contracts and reproducible dataset versions;
- source-to-feature lineage and quality state;
- analytical snapshot contracts consumed by deterministic statistical/ML engines and domain AI synthesis.

### ISI-23 - SIMPA Production Methodology

Goal: convert SIMPA methodology infrastructure into a validated, versioned, reproducible analytical product.

The canonical design baseline is `docs/roadmap/ISI-SIMPA-METHODOLOGY-v1.md` and ADR-0025.

Status: **COMPLETE / CI_VERIFIED**. ISI-23A through ISI-23D retain their accepted checkpoints. ISI-23E final closeout is COMPLETE / CI_VERIFIED on `3894f5d4ce9b78abc39f9a565fecf83bc2ce7a73` (tree `29c84c2bac1251af6e18c0a9dbccc6c52e69a97a`) with exact-main run #84 / `35084716444` success. The whole SIMPA production-methodology phase is closed and serial implementation has moved to ISI-24.

Accepted ISI-23B as-built boundary: methodology-owned `SIMPA-REFERENCE-SUITE-v1` suites/cases provide versioned immutable semantic and execution fingerprints for the existing direct-observation methodology only. Every case deterministically passes before human validation, using the same calculator as governed production computation. Historical `legacy_unknown` and `legacy_inline` evidence is preserved without fabricated suite backfill. This accepted boundary does not validate LISI/formulas/weights/thresholds, complete the detailed SIMPA Help/User Guide, or introduce ISI-25 evaluation-set/model-promotion scope; the whole ISI-23 phase remains in progress.

ISI-23C R1 implementation boundary: global immutable statistical methodology contracts bind an exact target indicator to its exact current validated indicator-methodology fingerprint; deterministic governed execution supports only continuous/OLS, count/Poisson GLM, binary-system-state/binomial logit and proportion-rate/fractional logit. Results persist coefficient uncertainty, fit/error metrics, diagnostics, applicable calibration, numerical controls and exact reproducibility fingerprints. PROPOSED execution requires explicit controlled-testing acknowledgement; VALIDATED records human methodology approval only. No prediction threshold/class, causal claim, LISI semantics, statistical-to-AI synthesis, champion/evaluation/promotion registry or ORDO change is introduced. At the accepted ISI-23C checkpoint, detailed SIMPA Help/User Guide remained open; ISI-23D below closes that Help/XAI slice while the whole ISI-23 phase remains in progress.

ISI-23D implementation boundary: establish the canonical cross-product Help Coverage Matrix while making the SIMPA domain rows/actions VERIFIED; add SIMPA-only in-app Help/User Guide and repository User Guide; add deterministic model-appropriate XAI for the four accepted ISI-23C families; persist model-produced p-values only for newly generated results and show p-value unavailable for historical immutable results that lack it; explain diagnostics/calibration/complete-case missingness/provenance/production_eligible/non-causal boundaries without inventing thresholds, confidence, feature importance, causality or policy conclusions. Shared AI champion/evaluation/promotion/fallback contracts remain ISI-25; ORDO Help/XAI remains ISI-24; no server/deployment mutation is authorized.

ISI-23E closeout boundary: no new production feature. Close the whole SIMPA phase with a final gap/legacy audit, Help/XAI acceptance proving SIMPA-owned INV-A10/INV-A11/INV-A18 remain VERIFIED while global cross-product coverage honestly remains PARTIAL, synthetic end-to-end execution of all four accepted statistical families through deterministic XAI, compatibility regression over ISI-23A-D, and governance/evidence synchronization. Historical immutable results, deferred LISI semantics, ISI-24 ORDO scope, ISI-25 shared AI/MLOps, ISI-27 release gating and ISI-28 server work retain their explicit boundaries.

Required deliverables include:

- formal indicator registry contract;
- methodology lifecycle;
- calculation tests with reference datasets;
- LISI methodology specification and implementation only when owner-approved;
- sub-indices/weights/normalization/missing-data rules/versioning/provenance where the approved methodology requires them;
- evidence-quality/confidence representation;
- social-map/GIS-ready data model and interfaces;
- policy-monitoring/evaluation workflow;
- deterministic statistical model contracts by target semantics;
- uncertainty, diagnostics and calibration rules;
- system-level classification only where classes are explicitly defined and validated;
- non-causal wording for ordinary association models;
- explainability and reporting contracts;
- complete SIMPA Help Coverage Matrix covering every material user-facing screen/function/action under the mandatory 0.5A checklist;
- detailed in-app SIMPA Help and User Guide, including lifecycle/status semantics, permissions, workflows, examples, errors/recovery and methodological/security limitations;
- SIMPA XAI/model-interpretation coverage for deterministic statistical/ML and bounded AI outputs, including faithful provenance, uncertainty/diagnostics/calibration interpretation, non-causal boundaries and explicit unsupported/not-calibrated states.

Critical rule: no Codex/LLM may invent indicator formulas, LISI weights, thresholds, citizen risk labels, causal claims, eligibility logic or policy conclusions.

### ISI-24 - ORDO Production Methodology

#### ISI-24A accepted checkpoint

`ISI-24A - ORDO Governed Reference Evidence + Scenario/GIS Contracts` is COMPLETE / CI_VERIFIED on `04b0738933030f1d69de52f9260c7b2f11042d0e` (tree `6c688c698fb5bf9520e0a4437c5f372a9790df2c`) with exact-main `ISI required acceptance` run #85 / `35138374174` completed `success`. It introduced versioned reference-evidence identity and human lifecycle, GIS-ready boundary/version/geometry/CRS provenance contracts, and a versioned evidence-only scenario contract with deterministic canonical input fingerprinting. Historical scenario assessments remain explicitly legacy rather than being falsely backfilled as v1-created records.

#### ISI-24B accepted checkpoint

`ISI-24B - Spatial Processing + Statistical/Time-Series Contracts` is COMPLETE / CI_VERIFIED on `0ad913db23cea44033e8adf693eb179edfa8fb5d` (tree `1008022ebe4cf95b4d45a12ff746188e6c8efa11`) with exact-main `ISI required acceptance` run #86 / `35147730914` completed `success`. It adds deterministic identity-based descriptive spatial aggregation; corrects the indicator-methodology lifecycle to `DRAFT -> PROPOSED -> VALIDATED -> RETIRED` while preserving truthful historical validated rows; and adds exact-methodology/governed-run-bound statistical-model and time-series readiness specifications. Its time-series object remains plan-only with forecast execution and automatic model selection locked off.

#### ISI-24C accepted checkpoint

`ISI-24C - Forecast Engine + Rolling-Origin Backtesting + Uncertainty/Diagnostics + NOT_ESTIMATED Runtime Semantics` is COMPLETE / CI_VERIFIED on `76e4ca5265f48a096d2253c88898e1aaedbff991` (tree `0a6ec7b7ab4db5d43c570c714c065f8fef7093f4`) with exact-main `ISI required acceptance` run #87 / `35153774409` completed `success`. It adds a separate immutable forecast runtime authority for explicitly requested naive and seasonal-naive execution, chronological rolling-origin backtesting, exact forecast metrics, leakage-safe empirical residual intervals, target-domain clipping, stable NOT_ESTIMATED outcomes, and first-class scenario-impact NOT_ESTIMATED semantics. It does not alter 24B specification truth, perform automatic selection/fallback, execute ETS/SARIMA/SARIMAX/count families, estimate causal scenario impacts, recommend policy, add UI/Help/XAI, or touch deployment.

#### ISI-24D accepted checkpoint

`ISI-24D - ORDO Help Coverage + In-App User Guide + Forecast/Scenario XAI Presentation` is COMPLETE / CI_VERIFIED on `49377e808845fc8746f0484ea7b452954c9e83b4` (tree `c8ea52299d80551ee303dbeef95d343b59448892`) with exact-main `ISI required acceptance` run #88 / `35220908672` completed `success`. It realizes `INV-A19=CURRENT_AS_BUILT` with in-app/repository Help, faithful deterministic forecast/scenario interpretation, bounded AI provenance/review visibility and read-only presentation of persisted accepted 24C forecast results. It preserves scenario-versus-forecast and `NOT_ESTIMATED` boundaries and does not introduce automatic model selection, causal impact, generic confidence, feature importance or policy recommendation.

#### ISI-24E accepted checkpoint and Phase-24 closeout

`ISI-24E - ORDO Final Whole-Phase Gap/Legacy Audit + Closeout` is COMPLETE / CI_VERIFIED at the accepted remediation/closeout implementation checkpoint `5937daa2ea7ff9c476bd6a05a04841d1534aefe2` (tree `6e75bf1cd13b95e23f9189b9e94453dd130eaa19`) with `ISI required acceptance` run #90 / `35238623960` attempt 2 completed `success`. The whole-phase audit found F01 stale user-facing wording and F02 incomplete forecast customer reachability as the only `REMOVE_BEFORE_NEXT_SLICE` blockers; both are resolved. No Phase-24 `REMOVE_BEFORE_NEXT_SLICE` item remains. ISI-25 and ISI-26 subsequently completed implementation acceptance on main; ISI-27 is CI_VERIFIED and ISI-28 is current. Server/DNS/central-ingress/production mutation remains forbidden until owner-approved ISI-28.

Goal: convert ORDO evidence/scenario infrastructure into a production destination-intelligence methodology without fabricating predictive capability.

The canonical design baseline is `docs/roadmap/ISI-ORDO-METHODOLOGY-v1.md` and ADR-0025.

Status: **COMPLETE / CI_VERIFIED**. ISI-24A through ISI-24D retain their accepted checkpoints; the final ISI-24E remediation/closeout implementation is accepted on `5937daa2ea7ff9c476bd6a05a04841d1534aefe2` (tree `6e75bf1cd13b95e23f9189b9e94453dd130eaa19`) with exact-main run #90 / `35238623960` attempt 2 success. ISI-25 and ISI-26 have since completed implementation acceptance; ISI-27 is current/next.

Required deliverables include:

- validated ORDO indicator-methodology registry;
- reference datasets and calculation tests;
- spatial/GIS-ready contracts;
- scenario evidence model;
- development-goal evaluation framework;
- methodology provenance/versioning;
- regression/model-family contracts by target semantics;
- time-series forecasting protocol using rolling-origin/backtesting;
- forecast intervals and uncertainty diagnostics;
- explicit scenario-versus-forecast boundary;
- deterministic scenario engine with `NOT_ESTIMATED` when no approved impact model exists;
- optional uncertainty propagation/Monte Carlo only after methodology validation;
- explainability and presentation contracts;
- complete ORDO Help Coverage Matrix covering every material user-facing screen/function/action under the mandatory 0.5A checklist;
- detailed in-app ORDO Help and User Guide, including permissions, workflows, examples, errors/recovery, scenario/forecast/NOT_ESTIMATED semantics and methodological/security limitations;
- ORDO XAI/model-interpretation coverage for deterministic statistical/forecast and bounded AI outputs, including faithful evidence provenance, intervals/uncertainty/backtesting interpretation where applicable and explicit unsupported/not-calibrated states.

Forecasting or causal claims are production-valid only when separate evidence-backed methodology/model specifications are approved.

### ISI-25 - Industrial AI / MLOps

Goal: make statistical/ML, embedding, LLM and VLM behavior measurable, versioned, reversible and auditable.

The canonical evaluation baseline is `docs/roadmap/ISI-AI-MODEL-EVALUATION-PROTOCOL-v1.md` and ADR-0025.

Status: **IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED**. ISI-25A is accepted on main SHA `f0047321ee4410522697144ecfa464087f1b83bc` (tree `06e419ec656ee2fb0bfb74b4a6b10d42ef275f25`) after local deterministic acceptance and assistant human review. ISI-25B is implemented and accepted on main SHA `7e11ee2a6f7546eacc3207e15cacfc35f6d04f3e`; it provides exact-registration-bound fallback, separate frozen promotion benchmarks, deterministic evaluators, capability thresholds, evidence-gated promotion/rollback governance, deterministic circuit state, on-demand drift and shared AI XAI. No hosted full acceptance was run for 25A/25B under the owner cost/acceptance policy, so `CI_VERIFIED` is not claimed. ISI-26 has now also completed repository implementation acceptance on main; ISI-27 is CI_VERIFIED and ISI-28 is current. Hosted full acceptance remains reserved for the controlled 27D checkpoint. Server verification and all deployment mutation remain deferred to ISI-28.

Required deliverables include:

- model registry/version contract across statistical/ML, embedding, LLM and VLM capabilities;
- champion/challenger lifecycle;
- prompt registry/version enforcement;
- `SIMPA-EVAL-v1` and `ORDO-EVAL-v1` dataset contracts;
- structured-output validation;
- evidence/RAG provenance contracts;
- shared product-specific XAI interpretation contracts for SIMPA and ORDO covering model/prompt/policy identity, governed evidence/retrieval provenance, faithful uncertainty/confidence semantics, structured-output status, fallback/failure state, human-review boundaries and the separation between deterministic numerical authority and generative explanation;
- model-appropriate explanation/attribution evaluation; unsupported attribution, feature importance, confidence or calibration must be surfaced as unavailable rather than fabricated;
- multilingual embedding evaluation;
- retrieval evaluation and namespace isolation;
- prompt-injection and unsafe-context tests;
- PII/sensitivity guards;
- retry/timeout/circuit-breaker behavior;
- provider/model fallback policies;
- human-review traceability;
- model/prompt rollback;
- inference quality/latency/resource accounting;
- deterministic promotion criteria that require challenger improvement over the registered baseline.

Human-in-the-loop remains a permanent decision-support requirement.

### ISI-26 - Performance, Load & Resilience Engineering

Goal: establish measurable capacity and failure behavior across API, data, statistical/ML and AI flows without conflating repository measurements with live production capacity.

Status: **IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED**. The accepted repository implementation is `ISI-26-R1 - Full Performance, Load & Resilience Implementation` on main SHA `e4b5b7f5927bc553fd616800d37beb5d115bb46e` (tree `9a30b280ba44798b987167c155f0be6ccc13776e`), from human-reviewed candidate fingerprint `98653d20a5223d4f6be66f3ee2017f998865b00ecb08a0950c07123d60dc2e24`. Focused/regression checks, synthetic performance evidence, native PostgreSQL acceptance, full local regression, assistant human review, independent analysis, exact staging, normal push and remote equality are PASS. Hosted full CI was deliberately not dispatched under the owner acceptance-cost policy, so `CI_VERIFIED` is not claimed.

The formal ISI-26A performance contract/harness, 26B API/auth/readiness resilience, 26C data/statistics/forecast/report scale and 26D AI queue/concurrency/timeout/circuit/fallback gates are accepted through the single grouped R1 implementation. R1 superseded only the micro-task-per-Codex execution cadence, not those formal gates. `ISI-26E - Performance & Resilience Whole-Phase Closeout` closes the phase-level gap/legacy/evidence audit; no `REMOVE_BEFORE_NEXT_SLICE` finding remains open.

R1 provides immutable performance/evidence contracts, ten versioned workloads, bounded standard-library concurrent execution and synthetic local service/renderer/worker exercises. Correctness/security/resilience remain non-compensable hard gates. Nearest-rank latency and completed-operation throughput remain `UNCALIBRATED` where the locked calibration policy does not justify a stable threshold; host-specific resource evidence remains `UNAVAILABLE`. Those are truthful accepted states, not missing production SLO claims. Local SQLite lanes do not prove shared PostgreSQL/Redis contention capacity; queue transport uses doubles and AI execution uses development stubs only.

Inventory impact remains INV-M19 repository acceptance tooling only; runtime ownership stays with INV-B25, INV-D01 through INV-D04, INV-C38/C39, INV-E05 and INV-F04. No customer-facing/API/schema/dependency/deployment boundary changed. `PRODUCTION_CAPACITY_VERIFIED=false` and `SERVER_VERIFIED=false` remain explicit. Live capacity/server verification belongs exclusively to ISI-28. Current server, DNS, certificates, central Nginx, production SMTP/data/secrets, server Ollama, Krcuga and OralScanXAI remain outside ISI-26 execution.

ISI-27 B0-R1A bootstrap is CLOSED/PASS; ISI-27A Shared Help & Release UX Completeness is accepted on main and `ISI-27D - Exact-Main RC Acceptance & Phase Closeout` is the current checkpoint. ISI-27 owns the Industrial Release Candidate & Acceptance Pack, while the explicitly approved hosted full acceptance checkpoint remains 27D. See `automation/specs/ISI-26E-PERFORMANCE-RESILIENCE-CLOSEOUT.md` and `docs/ops/ISI-26-PERFORMANCE-LOAD-RESILIENCE.md` for exact predecessor closeout evidence and retained limitations.

### ISI-27 - Industrial Release Candidate & Acceptance Pack

Goal: produce one release candidate technically ready for controlled deployment.

Status: **COMPLETE / CI_VERIFIED / REVIEW_VERIFIED** for exact RC `2b1f2ef20a2310df23947f2ac2128d16f81a98ea` only. All 12 jobs passed in owner-approved checkpoint #93 (run 37277358285); source/image/SBOM/report/provenance checks and owner SSH signature verification passed. Actions pre/post checks and whole-phase legacy audit are recorded in `automation/specs/ISI-27D-ACCEPTANCE-CLOSEOUT.md`. Legal publication and live operational/provider/methodology state remain separate ISI-28 gates. Current checkpoint: `ISI-28 - Current Server Controlled Upgrade`.

Release acceptance must include explicit SIMPA and ORDO methodology states, model/eval provenance, security/privacy acceptance, migration/recovery rehearsals and performance acceptance. Help/XAI remains a hard release gate. The canonical Help Coverage Matrix must show `VERIFIED` for every applicable production-critical action, with checklist-level `NOT_APPLICABLE` only where explicitly justified. `INV-A17` public self-registration remains NOT_PRESENT; ISI-27 must not create public signup merely to satisfy Help coverage.

Formal ISI-27 execution gates are intentionally large and serial:

1. **ISI-27A - Shared Help & Release UX Completeness** — close the twelve corrected shared Help/XAI blockers while preserving already VERIFIED SIMPA/ORDO/shared-AI authority.
2. **ISI-27B - RC Evidence & Governance Pack** — consolidate methodology state, model/eval provenance, security/privacy, exact-RC migration/native-PostgreSQL/recovery evidence, inherited ISI-26 limits, release notes, compatibility, known limitations and rollback/handoff.
3. **ISI-27C - Reproducible Release & Supply-Chain Assurance** — portable immutable release builder, exact artifact/checksum identity, real SBOM, provenance/attestation and blocking image vulnerability enforcement; automatic CI triggers remain forbidden.
4. **ISI-27D - Exact-Main RC Acceptance & Phase Closeout** — owner-controlled Actions usage precheck, explicit approval, manual `workflow_dispatch` checkpoint `release-candidate` on exact main, all blocking jobs success, run/artifact binding, usage postcheck and final whole-phase audit before exact-RC `CI_VERIFIED`.

No ISI-27 gate may contact or mutate the current server, DNS, certificates, central Nginx, real SMTP, production secrets/data or server Ollama. Those remain ISI-28-only. Krcuga and OralScanXAI remain strict non-targets.

### ISI-28 - Current Server Controlled Upgrade

Status: **IN_PROGRESS — 29F f587ed0 DEPLOYED / PREPRODUCTION_TESTING**. Exact `374dda3db89f6fb87dde7f5b761642440da17bef` passed all 12 required jobs (#96 / 37515814577). Recorded scoped deployment/live probes passed; evidence `automation/evidence/ISI-28/checkpoint-96/closeout.json`. SERVER_VERIFIED applies only to that bounded test release, not full production. SMTP pending; new backups owner-deferred; operational/capacity/domain-quality gates remain open. No fresh server probe performed by the 2026-10-07 planning task.

This is the only phase allowed to touch the current server, DNS, ingress, real SMTP, production secrets or production data.

### ISI-29 — Graphical XAI, GIS and geographically anchored entities/findings

Status: **COMPLETE / CI_VERIFIED / REVIEW_VERIFIED for 29A–F software at f587ed0; recorded scoped SERVER_VERIFIED PREPRODUCTION_TESTING, not full production**. Owner explicitly requested this expansion on 2026-10-07. The implementation roadmap and legacy classifications are in `docs/roadmap/ISI-29-XAI-GIS-ENTITY-FINDINGS-PLAN.md`; first exact slice is `automation/specs/ISI-29A-GRAPHICAL-XAI.md`. Packages: 29A persisted-result charts, 29B governed geometry/contracts, 29C GIS workflows, 29D model-appropriate SHAP, 29E entity/claim extraction/review, 29F grounded linked evidence/report/Help/release. Unsupported SHAP remains unavailable until its exact model/data contract is validated. No model-family, formula, risk threshold or dependency is automatically approved by the roadmap.

Local 29 development may proceed from the accepted preproduction #96 baseline while full-production 28 gates remain open. This owner-requested extension does not close/reopen the accepted scope of phases 23/24/25. Server work stays exclusively in a later explicitly approved ISI-28 release task.

## 7. Task dependency model

Default serial dependency:

`ISI-17 -> ISI-18 -> ISI-19 -> ISI-20 -> ISI-21 -> ISI-22 -> ISI-23 -> ISI-24 -> ISI-25 -> ISI-26 -> ISI-27 -> ISI-28`

The canonical AI decision does not authorize out-of-order production implementation. It strengthens the requirements of ISI-21 through ISI-25 while preserving the serial dependency model.

## 8. Implementation-agent contract

For each implementation task, the agent must receive:

- exact baseline/ref;
- objective;
- locked architecture and relevant ADRs;
- required behavior;
- DB/API/UI/worker/configuration impact;
- Help Coverage Matrix impact for every customer-facing change, including the mandatory 0.5A checklist and required in-app/User Guide updates;
- XAI/model-interpretation impact for every user-facing statistical/ML/RAG/LLM/VLM output in SIMPA or ORDO;
- security/privacy constraints;
- methodology constraints;
- required tests;
- exact acceptance commands;
- required evidence;
- explicit non-goals;
- forbidden changes;
- completion definition.

Normal owner-driven execution occurs directly on the canonical local `main` worktree. The agent must not stage, commit or push without explicit owner authorization.

A reviewer may inspect the exact diff against the specification, but deterministic acceptance and exact-main GitHub Actions remain authoritative.

Every task status must expose task ID, baseline/head SHA, current evidence-backed state, required gates, evidence path, known warnings and server-verification status.

## 9. Human gates

Human approval remains required at minimum for:

- architecture changes;
- new external dependencies with material operational impact;
- security-policy changes;
- SIMPA/ORDO methodology validation;
- formula/weight/threshold/class-definition approval;
- claims of predictive or causal capability;
- production champion model promotion where methodology or institutional output changes materially;
- major industrialization milestone completion;
- any server/deployment action;
- any production secret or production data mutation.

## 10. Final deployment concept

The final server action is release-based rather than a casual `git pull`.

Expected deployment sequence:

1. verify currently deployed release and clean operational state;
2. backup DB/object storage/configuration;
3. fetch exact approved release/tag;
4. build/pull exact application artifacts;
5. run migration preflight;
6. apply migrations;
7. start/update services;
8. readiness/health checks;
9. API/UI/worker/AI smoke tests;
10. data-integrity checks;
11. record deployed version and evidence;
12. rollback automatically or procedurally if a hard acceptance gate fails.

## 11. Owner approval record

Owner approvals now binding in this master plan include:

### 2026-09-09 industrialization baseline

- locked ISI -> {SIMPA, ORDO} product architecture;
- exclusion of COSMOS from the current runtime/application architecture;
- server freeze through ISI-27;
- serial ISI-17 through ISI-28 industrialization sequence;
- human approval boundaries;
- repository-audit findings as implementation input.

### 2026-09-12 workflow and analytical AI canonicalization

- one canonical local repository, one worktree and owner-driven direct-main development model;
- no normal feature/implementation/review branch or PR requirement;
- ISI-20 completion on canonical main after successful run #58;
- deterministic statistical/ML engine for authoritative numerical analytics;
- document AI/RAG with provenance for extraction/retrieval;
- LLM/VLM as bounded synthesis/explanation rather than silent numerical authority;
- separate SIMPA and ORDO domain intelligence over shared infrastructure;
- SIMPA aggregate/system-level boundary and prohibition on citizen-level automated institutional decisions;
- ORDO forecast-versus-scenario separation and `NOT_ESTIMATED` when an impact model is not validated;
- champion/challenger model governance;
- dedicated embedding-model evaluation for RAG;
- `SIMPA-EVAL-v1` and `ORDO-EVAL-v1`;
- evidence-first presentation order;
- methodology lifecycle requiring human approval before `VALIDATED`.

### 2026-09-13 canonical architecture/governance bootstrap

- MasterPlan becomes the mandatory first-read/bootstrap authority for every new chat, feature, task, recovery and phase closeout;
- every bootstrap must verify Git/repository state, exact-main CI evidence, accepted architecture/decisions and actual as-built code before implementation;
- every bootstrap and phase closeout must perform a mandatory legacy/drift audit with explicit classification and cleanup ownership;
- `codex-isi` is the only permitted Codex entrypoint for ISI; generic `codex` is forbidden;
- normal implementation remains locked-contract + runner + independent analyzer + human review + owner-approved exact staging + direct-main commit/push + exact-main CI;
- historical branch/PR workflow remains legitimate history but is not current execution authority;
- stale ISI-15/ISI-16 deployment workflow documents are superseded as active instructions; only ISI-28 may authorize server mutation;
- ISI-22E is COMPLETE / CI_VERIFIED on `44002aa0774a902bdf2d7a0ae56ff3558303571c`, and the next work is a whole-phase ISI-22 gap audit.

### 2026-09-14 ISI-22F completion and ISI-22G transition

- ISI-22F is COMPLETE / CI_VERIFIED on `cfe1574532df65589132bbdd10625172b32fb959` with exact-main acceptance run #73 / `34787001102`, and the current/next work is ISI-22G - Domain Consumption Enforcement + ISI-22 Closeout.

### 2026-09-14 ISI-22G completion and ISI-23 transition

- ISI-22G implementation is COMPLETE / CI_VERIFIED on `fd0e46631b5047c64b731d041645e528292f3664` (tree `1a405a65a6fa67f2845ee0a10f2a6f44b11e355e`) with exact-main `ISI required acceptance` run #75 / `34856573722` completed `success` and aggregate `acceptance` green;
- overall ISI-22 - Industrial Data Platform is COMPLETE / CI_VERIFIED;
- current/next work is ISI-23 - SIMPA Production Methodology + Help/User Guide;
- the serial dependency model remains `ISI-22 -> ISI-23 -> ISI-24 -> ISI-25 -> ISI-26 -> ISI-27 -> ISI-28`;
- server/DNS/ingress/real SMTP/production secrets/data/server Ollama remain frozen until fresh owner-approved ISI-28.


### 2026-09-14 ISI-23A completion and ISI-23B transition

- ISI-23A - SIMPA Methodology Lifecycle + Production Contract Authority is COMPLETE / CI_VERIFIED on `238a881ef39906a2adebbb03fabe80a043017697` (tree `3778f29627100fb48ba369f0618250534870d0a8`);
- authoritative exact-main `ISI required acceptance` run #77 / `34900812947` completed `success` with all blocking jobs and aggregate `acceptance` green;
- accepted 23A scope provides `DRAFT -> PROPOSED -> VALIDATED -> RETIRED`, strict `SIMPA-METHODOLOGY-CONTRACT-v1`, deterministic direct-observation reference gate, contract/reference fingerprints, human approval trace and legacy compatibility;
- the read-only ISI-23B bootstrap/audit found reference calculation evidence PARTIAL: `reference_dataset` is text identity and the current reference gate is one inline case; versioned methodology-owned reference-suite/case evidence is MISSING;
- current/next work is ISI-23B - versioned SIMPA reference-calculation evidence;
- ISI-25 MLOps/champion-challenger/eval-set promotion remains out of ISI-23B scope; LISI formulas, weights, thresholds, citizen risk/eligibility logic and causal claims remain forbidden without separate owner-approved methodology;
- server/DNS/ingress/real SMTP/production secrets/data/server Ollama remain frozen until fresh owner-approved ISI-28.

### 2026-09-15 ISI-23B completion and ISI-23C transition

- ISI-23B - Versioned SIMPA Reference-Calculation Evidence is COMPLETE / CI_VERIFIED on `088fe79904bd0cc85c4d52d5442218884501b538` (tree `5f8530f6fc7ca82afe7050f39a9f787b048fd8db`);
- authoritative exact-main `ISI required acceptance` run #79 / `35018144968` completed `success` with policy, quality, tests, architecture-security, migration, native-postgres, compose, supply-chain, build and aggregate `acceptance` green;
- accepted 23B scope provides methodology-owned `SIMPA-REFERENCE-SUITE-v1` suite/case persistence, deterministic semantic/result fingerprints, shared direct-observation calculation between reference evidence and governed production computation, failed-terminal/new-version recovery, historical `legacy_unknown`/`legacy_inline` compatibility and the human-validation boundary;
- current/next work is ISI-23C - deterministic statistical model contracts by target semantics + uncertainty/diagnostics/calibration;
- ISI-23C must remain non-causal for ordinary association analysis and may introduce system-level classes only where explicitly defined and validated;
- LISI formulas/weights/thresholds remain forbidden without separate explicit owner-approved methodology; detailed SIMPA Help/User Guide remains open for later ISI-23 work;
- ISI-25 champion/challenger, evaluation-set, prompt/model promotion and rollback governance remain out of ISI-23C scope;
- the whole ISI-23 phase remains IN PROGRESS and is not complete;
- server/DNS/ingress/real SMTP/production secrets/data/server Ollama remain frozen until fresh owner-approved ISI-28.

### 2026-09-16 ISI-24A completion and ISI-24B transition

- ISI-24A is COMPLETE / CI_VERIFIED on `04b0738933030f1d69de52f9260c7b2f11042d0e` (tree `6c688c698fb5bf9520e0a4437c5f372a9790df2c`) with exact-main acceptance run #85 / `35138374174` success;
- ISI-24B - Spatial Processing + Statistical/Time-Series Contracts is the current owner-scope-frozen slice;
- overall ISI-24 remains IN PROGRESS, forecasting execution remains owned by 24C, and server mutation remains deferred to owner-approved ISI-28.

### 2026-09-16 ISI-24B completion and ISI-24C transition

- ISI-24B is COMPLETE / CI_VERIFIED on `0ad913db23cea44033e8adf693eb179edfa8fb5d` (tree `1008022ebe4cf95b4d45a12ff746188e6c8efa11`) with exact-main acceptance run #86 / `35147730914` success;
- ISI-24C - Forecast Engine + Rolling-Origin Backtesting + Uncertainty/Diagnostics + NOT_ESTIMATED Runtime Semantics was the owner-scope-frozen forecast-engine slice through its accepted checkpoint; it is no longer the current implementation slice after accepted ISI-24D/ISI-24E closeout, while its accepted runtime semantics remain authoritative;
- At the accepted ISI-24C checkpoint, the 24B time-series specification was plan-only and only naive and seasonal-naive were executable forecast families; accepted ISI-24E later exposed the governed specification lifecycle without changing the accepted 24C forecast-family boundary or authorizing automatic model selection or scenario impact estimation;
- ISI-24 remained IN PROGRESS through the accepted ISI-24D checkpoint while ORDO Help/XAI remained owned by 24D; that historical phase-status constraint is superseded by the accepted ISI-24E closeout recorded below, while server mutation remains deferred to owner-approved ISI-28.

### 2026-09-17 ISI-24E completion and ISI-25 transition

- ISI-24E F01/F02 remediation/closeout implementation is COMPLETE / CI_VERIFIED on `5937daa2ea7ff9c476bd6a05a04841d1534aefe2` (tree `6e75bf1cd13b95e23f9189b9e94453dd130eaa19`);
- authoritative exact-main `ISI required acceptance` run #90 / `35238623960` attempt 2 completed `success`; policy, quality, tests, architecture-security, migration, native-postgres including ISI-19 recovery rehearsal, compose, supply-chain, build and aggregate `acceptance` are green;
- F01 stale user-facing ORDO wording and F02 incomplete governed forecast customer workflow are resolved; there is no open Phase-24 `REMOVE_BEFORE_NEXT_SLICE` finding;
- F08 global cross-product Help remains `REMOVE_IN_NAMED_PHASE(ISI-25/ISI-27)` and does not misrepresent ORDO-owned Help/XAI coverage, which remains VERIFIED;
- the canonical ORDO customer workflow uses permission-separated specification lifecycle (`indicator.manage`), discovery/read (`analysis.read`) and explicit forecast execution (`analysis.run`) over server-resolved validated methodology authority;
- scenario-versus-forecast, `NOT_ESTIMATED`, `NO_APPROVED_RESPONSE_MODEL`, legacy compatibility, non-causal wording, no automatic model selection/fallback and human-review boundaries remain authoritative;
- overall ISI-24 - ORDO Production Methodology is COMPLETE / CI_VERIFIED;
- current/next work is ISI-25 - Industrial AI / MLOps bootstrap/audit; implementation is not yet scope-locked and no model is promoted by this transition;
- the serial dependency remains `ISI-24 -> ISI-25 -> ISI-26 -> ISI-27 -> ISI-28`;
- server/DNS/ingress/real SMTP/production secrets/data/server Ollama remain frozen until fresh owner-approved ISI-28.

This governance-only synchronization records accepted Phase-24 truth; it changes no production runtime behavior and authorizes no deployment.

Material changes to these points require a new explicit owner approval and, where architectural, a new or superseding ADR.


### 2026-09-19 unified Codex and dual-Mac governance

- Branislav explicitly superseded the previous multi-account/project-specific Codex execution policy as active authority.
- Krcuga, OralScanXAI and ISI now use the standard `codex` CLI authenticated with the single canonical Outlook account `branislav.radomirovic@outlook.com`.
- `codex-isi`, project-specific wrappers and project-specific `CODEX_HOME` profiles are legacy and are not required by active ISI development; historical evidence remains legitimate history.
- MacBook Air and iMac use GitHub `origin/main` as the only source handoff mechanism and only from a clean synchronized source state.
- The same project is never actively developed on both Macs simultaneously.
- New workstation/system dependencies must be documented in this Master Plan and workstation requirements before installation.


### 2026-10-01 ISI-25B closure and shared-ingress governance reconciliation

- ISI-25B implementation is accepted on main SHA `7e11ee2a6f7546eacc3207e15cacfc35f6d04f3e`; the later `ff573b3d76cf29581cb19c255821e9b4c4841108` governance commit changes no product/runtime feature code.
- Overall ISI-25 is `IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED`; full hosted acceptance was deliberately not run and remains reserved for the controlled ISI-27 acceptance/release checkpoint.
- ISI-26 repository implementation is accepted on main SHA `e4b5b7f5927bc553fd616800d37beb5d115bb46e` with whole-phase 26E closeout complete; ISI-27 B0-R1A bootstrap is closed, scope is locked, and 27A is current.
- The final owner-approved shared edge for ISI is central Nginx `central-ingress-nginx-1`, Compose project `central-ingress`, service `nginx`; Caddy is not current ISI target authority.
- The owner-locked public ISI endpoint is `https://isi.opus.rs:8445/`, alongside Krcuga `:8443` and OralScanXAI `:8444` on the same shared host boundary.
- ISI retains its independent Compose project and stateful/runtime services. `api` and `streamlit` attach to external `isi_ingress` with aliases `isi-api` and `isi-streamlit`; those are the intended shared-Nginx upstream identities.
- Repository `isi-edge` remains pre-cutover/historical compatibility only and must not become a parallel production ingress.
- No server, DNS, certificate, central-ingress, SMTP, production-secret/data or server-Ollama mutation is authorized by this reconciliation. ISI-28 remains the only phase allowed to physically verify and, if necessary, change those production resources.
- Krcuga and OralScanXAI are strict non-target systems for ISI work; ISI-28 must prove they remain healthy before and after any shared-ingress mutation.
- `TECHNICAL_DOCUMENTATION.md` is established as the controlled living technical reference synchronized with this MasterPlan and as-built code.

### 2026-10-02 ISI-26 R1 acceptance and 26E whole-phase closeout

- ISI-26 R1 is accepted on main SHA `e4b5b7f5927bc553fd616800d37beb5d115bb46e` (tree `9a30b280ba44798b987167c155f0be6ccc13776e`), candidate fingerprint `98653d20a5223d4f6be66f3ee2017f998865b00ecb08a0950c07123d60dc2e24`.
- Local synthetic performance evidence, native PostgreSQL acceptance, full local regression, assistant human review, independent analysis, exact staging, normal push and remote equality are PASS.
- ISI-26A through ISI-26D formal gates are accepted through R1; ISI-26E closes the whole-phase audit with no open `REMOVE_BEFORE_NEXT_SLICE` finding.
- Timing remains `UNCALIBRATED` where calibration conditions are not met; portable resource evidence remains `UNAVAILABLE`. No production SLO or live capacity is fabricated.
- `CI_VERIFIED` is not claimed because hosted full acceptance was deliberately not dispatched. ISI-27 is current/next and owns the controlled release-candidate acceptance checkpoint.
- `PRODUCTION_CAPACITY_VERIFIED=false` and `SERVER_VERIFIED=false` remain binding; live-server capacity and mutation remain ISI-28-only.


### 2026-10-02 ISI-27 corrected bootstrap and scope lock

- B0-R1A is the corrected read-only bootstrap authority on main `e46128752e29f46dc6d9b8510198739f88da50e9`, tree `bc73ca23303d3f3353d440203f96dd698bf42b35`.
- Corrected classification: DONE=6, PARTIAL=8, MISSING=5, DRIFT=0; thirteen release blockers not DONE; twelve real shared Help/XAI blockers; SBOM/signed provenance/attestation MISSING.
- ISI-27 is locked into 27A Help/UX completeness, 27B RC evidence/governance, 27C reproducible release/supply-chain assurance and 27D owner-controlled exact-main hosted RC acceptance/closeout.
- No hosted CI dispatch, stage/commit/push or server action is authorized by scope lock.
- ISI-28 remains the exclusive live-server mutation/capacity-verification phase.


## Historical pre-acceptance record — ISI-27A R1 implementation candidate

Baseline: `39dc1d59a74a03c86f68df093cc07e32d41d028c`, tree
`3c7027b375b041043f7305cdab008aee35f16ef7`. Contract:
`automation/specs/ISI-27A-R1-SHARED-HELP-RELEASE-UX-COMPLETENESS.md`.
This subsection is retained only as pre-acceptance history and is superseded for live status by the accepted-main closeout below.
At that checkpoint, 27A was `in_progress`, an unstaged/uncommitted implementation-candidate, NOT CI_VERIFIED.
At that checkpoint, parent ISI-27 remained in_progress; the active checkpoint was
`ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS`; 27B/27C/27D were planned.

Shared Help authority: `src/streamlit_app/shared_help_workspace.py`, twelve topics
ISI-H01..H12, mirrored in `docs/help/ISI-SHARED-USER-GUIDE.md`.
Public header/footer target `help=public`; public-safe guidance needs no session.
Authenticated `isi_help` and contextual Data/Reporting/Admin/Account Security Help
use that authority. Invitation/verification/reset presentation consumes existing
APIs and clears sensitive queries on success; active sessions cannot be replaced
by one-time links. Public self-registration remains NOT_PRESENT/invitation-only.
The twelve corrected matrix rows have focused 27A Help/test authority; A07/A20
are not promoted. Protected SIMPA/ORDO/AI Help content is unchanged.

Bootstrap classification: accepted auth/domain/service authorities DONE;
shared Help/auth presentation PARTIAL/MISSING at baseline, addressed in this
candidate. Protected auth/domain authorities and shell markers are
REQUIRED_COMPATIBILITY. Earlier phase/global Help statements are LEGITIMATE_HISTORY;
the current top-level matrix supersedes their global status only, not methodology.
The R0 parser over-read is LEGITIMATE_HISTORY; corrected R0-R1 hashes match.
Historical tests freezing global PARTIAL are REMOVE_BEFORE_NEXT_SLICE.
ISI-27A-R1A authorizes only four inherited predecessor Help assertions to converge
with the current top-level matrix authority; no domain/runtime semantics, predecessor
acceptance facts, methodology, XAI or authorization behavior are changed. At that checkpoint, full local
acceptance and independent review were still required; no test bypass was permitted.

Local HEAD and origin/main match baseline; direct remote verification is unavailable
in this sandbox because GitHub DNS resolution failed. The latest recorded hosted
acceptance is predecessor run #90 / 35238623960 on 5937daa2ea7ff9c476bd6a05a04841d1534aefe2,
not this candidate; 25/26 hosted acceptance was deliberately deferred. Runner
fingerprint, complete deterministic acceptance and independent review remain gates.

STAGE_COMMIT_PUSH=NO; GITHUB_ACTIONS_DISPATCH=NO; SERVER_MUTATION=NO;
CI_VERIFIED=NO; SERVER_VERIFIED=NO. Real-provider MFA is not verified; production
SMTP and live deployment/capacity remain ISI-28-only, DEFERRED_SERVER_VERIFICATION.


### ISI-27A-R1A no-Codex inherited Help convergence

R1A continues the existing unstaged R1 candidate after workspace-credit exhaustion. It authorizes only four predecessor test assertions that froze the historical global `INV-A21=PARTIAL` state. Runtime/auth/domain code is frozen to the R1 prestate. The current top-level Help matrix may be `VERIFIED` for the corrected production-critical 27A scope while predecessor phase facts remain historical. `INV-A17` remains `NOT_PRESENT` and onboarding remains invitation-only. Full local regression, independent analysis and human review remain open; `CI_VERIFIED=NO`, `SERVER_VERIFIED=NO`, `STAGE_COMMIT_PUSH=NO`, `GITHUB_ACTIONS_DISPATCH=NO`, `SERVER_MUTATION=NO`.


## ISI-27A accepted-main closeout and ISI-27B promotion — 2026-10-03

ISI-27A Shared Help & Release UX Completeness is **ACCEPTED ON MAIN / NOT CI_VERIFIED** on SHA `74acd5d9a890733347554633f44a6d5319717ba3`, tree `a69b8582a77555611b64a5527548e67a5b0c45cb`, accepted candidate fingerprint `01ed26dd8e1193606f17c097f88ba0fd68b4f3ce2127de0845468998d3dc8d64`. Deterministic local acceptance is `1030 passed / 43 skipped / 0 failed`; independent analysis and human review are PASS / REVIEW_VERIFIED.

This closeout is governance-only. It changes no runtime/auth/domain/Help semantics. `INV-A17` remains `NOT_PRESENT` and invitation-only. Hosted GitHub Actions were not dispatched and `CI_VERIFIED=NO`; no live server, DNS, ingress, SMTP, production secret/data or server Ollama mutation occurred and `SERVER_VERIFIED=NO`.

Parent ISI-27 remains `IN PROGRESS`; the active checkpoint is now **ISI-27B — RC Evidence & Governance Pack** (`spec_ready`). ISI-27C and ISI-27D remain planned; ISI-28 remains deferred and is still the only server-mutable phase.

## Historical pre-acceptance record — ISI-27B R1 candidate (2026-10-04)

Public portal remediation is accepted on main `c177f9d705efd6f68d95ef7d13847b03a8e19229`.
Owner approved reviewed-candidate finalization and final deployment; release order
remains 27B -> 27C -> 27D -> ISI-28. The locked 27B implementation contract is
`automation/specs/ISI-27B-R1-RC-EVIDENCE-GOVERNANCE-PACK.md`. INV-M20 owns exact
candidate/report consolidation. Local full/native/recovery/performance acceptance
and independent review remain required before promotion. CI_VERIFIED=NO;
SERVER_VERIFIED=NO. Public operator information is ISI with GoraNova as confirmed
by the owner; the Gmail privacy contact is approved. Provider/legal processing
facts must remain grounded in public records and the ISI-28 runtime audit.

## ISI-27B accepted-main closeout and ISI-27C promotion — 2026-10-04

ISI-27B is ACCEPTED ON MAIN / REVIEW_VERIFIED / NOT CI_VERIFIED on
`16a928b20907d570df2cf05101a969e1f0cda736` (tree
`2513af18b6d3a7b338f3a11b63444e7181f95a63`). Local acceptance: 1071 regression
passes, 43 runner-gated native skips, 45 native PostgreSQL passes with zero skips,
PostgreSQL 17/object restore PASS, ten accepted performance scenarios. Pack hash
`9da45b26e811b6320c951e4285f83353aa306413c96052d5a75112b5ec67c8c1`;
candidate `d97b16ce6f3cd179d8fca5b05e838d6644a6eda1bdff61c2399c4b0952e22a86`.
Independent analysis, review, committed-file comparison and remote equality PASS.
At that 27B handoff, the next checkpoint was `ISI-27C - Reproducible Release & Supply-Chain Assurance`.
27D and ISI-28 had not started. No hosted/server acceptance was claimed at that checkpoint.

27C contract: `automation/specs/ISI-27C-R1-REPRODUCIBLE-RELEASE-SUPPLY-CHAIN.md`.
Its candidate introduces portable immutable release packaging, real image SBOM
and blocking scan, existing-owner SSH-signed provenance and strict serial release
state validation. GitHub Free/private signing uses local owner identity and makes
no Enterprise/SLSA certification claim. INV-M21 owns release assurance; INV-K15
owns build/signing metadata; INV-J32 maps the immutable release bundle. Python 3.11
stdlib, existing OpenSSH 8.2+ and Docker suffice; Trivy runs as an official pinned
CI action or disposable scanner container. No host package installation is required.

## 27C R1 partial verification and R2 accepted-main closeout — 2026-10-04

At the earlier R1 checkpoint, 27C was IN_PROGRESS with an unstaged candidate.
An earlier frozen candidate (`17d0801a8fcfe073055e959e52006c429d008a072befc3649a4c1158e2c99d1d`)
passed 1105 regression tests (43 intentional native skips), 45 native PostgreSQL
tests (zero skips), PostgreSQL/object restore, all 10 performance scenarios,
quality, policy, Compose and changed-line checks. Later review/contract changes
require final rerun; this is not final-candidate acceptance. Evidence:
`automation/evidence/ISI-27C/local-r1/partial-verification.json`.

Actual image scanning discovered new security drift: urllib3 2.7.0 and build-only
tooling findings were corrected in the candidate; Python dependency audit and
real runtime imports pass. The corrected Debian image still has 45 HIGH OS
findings. Image acceptance FAIL; classified REMOVE_BEFORE_NEXT_SLICE. No finding
is ignored and no release/server gate is bypassed. The owner approved bounded R2
implementation using the pinned Wolfi/Python 3.11 supplier in
`automation/specs/ISI-27C-R2-MINIMAL-RUNTIME-BASE-PROPOSAL.md`. The multistage
Docker candidate has passed the exact-image runtime probe and Trivy 0.75.0 scan:
117 CycloneDX components, zero HIGH/CRITICAL findings, API and Streamlit health
200, and unauthenticated account access 401. The full local gate set passed on
the recorded candidate: 1,159 regression tests (43 existing skips), 45 native
PostgreSQL tests (zero skips), recovery, all 10 performance scenarios, policy,
quality, Compose and diff. The independent analyzer passed. Exact reports are
retained by candidate fingerprint under `automation/evidence/ISI-27C/`. The
reviewed implementation is accepted on main `b6f0bfaf453360da72f866d4bbd1d47b51655bf4`
(tree `8d52631012121c078d077a39d75e201d4ffadcbd`, candidate fingerprint
`7dc381dd31d94e6ada447c7cffc945399bddbe4a7ec138ec88ae69e77e9be8ea`). It is
not CI_VERIFIED or SERVER_VERIFIED. 27D is specification-ready and awaits its
separate usage precheck and explicit owner approval; ISI-28 remains deferred.

## ISI-27D checkpoint #92 — 2026-10-05

Owner-approved run [#92](https://github.com/branislavradomirovic/isi/actions/runs/37274367540)
on exact main `587b8e1e92a4a8a2550cccf4a732a3798f0c312e` completed with
failure. All ten upstream jobs passed, including regression, native PostgreSQL,
recovery, runtime/image scans and the owner-approved full-history Gitleaks
baseline. `release-bundle` failed because the build artifact was named
`image-runtime-check.json` while the bundle/signer require `runtime-check.json`;
aggregate acceptance failed. No signed bundle, CI_VERIFIED or SERVER_VERIFIED
is claimed. The bounded unstaged recovery normalizes the producer filename and
adds producer/preserve/upload/consumer contract coverage. Validation passed:
88 targeted tests; full local regression 1,118 passed, 43 existing skips, zero
failures/errors; policy, Compose, syntax, JSON and diff checks. The first local
regression invocation lacked Alembic on PATH; the unchanged suite passed after
activating the existing project environment. No application behavior changed.
Evidence is local/ignored under `automation/evidence/ISI-27D/checkpoint-92/`.
Actions postcheck: GitHub Free, 158/2000 minutes, displayed 0/0.5 GB storage;
reporting may lag. Next gate: validate/review the exact recovery candidate, then
owner-approved commit/push and a separate exact-SHA hosted checkpoint. Terms/
Privacy publication and live operational policies remain pending; only ISI-28
may perform controlled server deployment after release prerequisites pass.

## ISI-27D accepted RC and owner-approved ISI-28 start — 2026-10-05

Exact RC `2b1f2ef20a2310df23947f2ac2128d16f81a98ea` is CI_VERIFIED / REVIEW_VERIFIED:
manual checkpoint #93 (run 37277358285), all 12 required jobs success; signed
source/image/SBOM/evidence bundle verified against pinned owner trust. Actions
pre/post observations: 158/191 of 2000 minutes; displayed storage 0/0.5 GB
(rounded/lagged). Exact identities and whole-phase classification are in
`automation/specs/ISI-27D-ACCEPTANCE-CLOSEOUT.md`; immutable artifacts/evidence
remain local under `automation/evidence/ISI-27D/checkpoint-93/`. Earlier #91/#92
failures and predecessor NOT CI_VERIFIED labels are historical states only.

The owner explicitly instructed continuation to full production. Current
checkpoint: **ISI-28 - Current Server Controlled Upgrade**, starting with the
fresh read-only audit in `automation/specs/ISI-28-R1-CONTROLLED-PRODUCTION-UPGRADE.md`.
Terms/Privacy and live provider/retention/operational facts remain preproduction
gates. No server mutation or SERVER_VERIFIED is claimed. A later source commit
does not inherit this exact RC's CI verification.

Accepted predecessor states: **27A ACCEPTED ON MAIN / 27B ACCEPTED ON MAIN / 27C ACCEPTED ON MAIN**; the consolidated exact RC is CI_VERIFIED through #93.

Current execution state: **ISI-28 IN_PROGRESS**; exact ISI-27 RC is CI_VERIFIED, production remains unverified.

`ISI-28 - Current Server Controlled Upgrade` is the current checkpoint.
SSH reconciliation now succeeds after the owner authorized the existing key
on the server. Server main is `bf4a648b1e118a0b087b437579d2f3f12ef2db94`;
API/UI and workers have different older image identities. Fresh protected
database backup/isolated restore and logical object byte recovery passed.
Accepted-image migration rehearsal passed from `20260828_0013` to
`20260918_0034`, preserving original table counts. Production database/services
remain unchanged. Details: `docs/ops/ISI-28-CONTROLLED-DEPLOYMENT-PLAN.md`.
The live `robots.txt` disallow and noindex header originate in central Nginx's
ISI block; remove only at the final public release gate. Legal entity/address
facts remain pending. The owner explicitly deferred real SMTP as
**To Be Defined**; external email-dependent workflows remain unverified and
cannot be represented as fully operational. No SERVER_VERIFIED claim yet.

## ISI-28 R2 activation candidate — 2026-10-06

Baseline 3986a03182eed04ba8055a6156d6722bca1504f5 passed exact required
acceptance #94 (37436821260), all 12 jobs. Signed image was verified and loaded
on the server without replacing live services. Exact-image isolated migration
passed 0013 to 0034, 90 to 140 tables; original counts not decreased.
Owner-approved ISI Nginx candidate is active: public robots/sitemap reachable,
public global noindex removed; app/API noindex retained. Non-ISI config bytes
were preserved and Krcuga/OralScanXAI HTTP baselines remained 200.

Owner now authorizes legal publication with visible placeholders and operational
policy targets, while SMTP remains pending. R2 adds an explicit pending email
mode with no silent delivery and account-independent unavailable request routes;
login and token-confirmation semantics remain unchanged. SR/EN versioned legal
payload and digest-bound collision-safe publisher are source candidates only.
These new changes do not inherit checkpoint #94 acceptance. No final cutover,
legal publication, operational enforcement or SERVER_VERIFIED is asserted.
Exact contract: `automation/specs/ISI-28-R2-PRODUCTION-ACTIVATION.md`.

## ISI-28 checkpoint95 activation and R3 closeout — 2026-10-06

Exact accepted main **1bf0552d702c0e6cefc659b38184f505118f11d1**, tree
514052fa0b0ddc7778068ccb2a94bfc6e0f444ef: all 12 jobs completed success in
manual checkpoint #95 / 37503549452; owner signature and every bundle/image
digest passed verification. Actions usage pre/post239/261 of2000 minutes.
Server source fast-forwarded cleanly to this exact SHA without resetting files.
Four ISI application runtimes now use the signed accepted image (config digest
3295bac2a9c36fca204536e3fc146a7051f9be13a571cf98899aa51b9fec94cb;
loaded OCI manifest6cdbbe13fa49c26d3a862c79fed3f324c93c41ba0148d5e8dca25feb658e848f).
New database isi_production restored with exact original counts then migrated
0013 to0034/140tables; old DB remains. New isi-production bucket copied one
42-byte object with exact key/hash/metadata/tags, private policy and versioning
enabled; old bucket remains. Fresh coordinated pre-cutover dump/object checkpoint
and protected config/prior images are retained server-only. First activation
helper failed by inspecting removed old ISI IDs and safely rolled back; corrected
activation passed and preserved non-ISI container identities. This history is
LEGITIMATE_HISTORY, not a waived acceptance failure.

SR/EN Terms/Privacy published from payload9f79b1d2b90825079be6cfb6aae24237fb24f5928b1395c5d9095e55d00fd426.
Live login/me/context/logout for SIMPA-only/ORDO-only/dual users, database/Redis/S3
readiness, both real RQ workers and existing storage readback passed. External
HTTPS (normal TLS validation) returned200 for public/legal/robots/sitemap/favicon/
manifest/app/API/diagnostics routes; public indexing and private noindex correct.
Krcuga8443 and OralScanXAI8444 returned200; no additional Nginx mutation.

Whole ISI-28 remains **IN_PROGRESS**, not full SERVER_VERIFIED: default embedding
execution timed out; a two-thread synthetic probe passed768dimensions in0.33s,
not domain retrieval quality or champion promotion. R3 adds optional per-ISI
thread configuration and desktop navigation correction after1280px live drift.
R3 adds bounded ops code but scheduling/restore/offsite/alerts are not verified.
Offsite destination and monitored duty-holder/channel require actual owner input.
SMTP explicitly pending; email-dependent workflows unavailable by design.
Operational retention periods remain targets until scoped enforcement/hold/recovery
evidence passes; no blanket institutional purge. Capacity and final operational
recovery acceptance remain open. Evidence: automation/evidence/ISI-28/r3/.

## Owner-narrowed preproduction test scope — 2026-10-06

Owner explicitly deferred all new backup creation and requested application/server
testing in pre-production mode. No new backup/cron-backup/offsite/purge is to be
activated. Preserve existing rollback and recovery media. R3 now contains only
read-only release-bound monitoring, responsive header repair and optional per-ISI
provider resource bounds plus tests. Existing data target names isi_production
and isi-production record where the test candidate runs, not a claim of full
production acceptance. Keep the production security profile and SMTP pending;
operational mode is **PREPRODUCTION_TESTING**. Whole ISI-28 stays IN_PROGRESS.
Offsite recovery/real alerts/duty holders/capacity remain full-production gates
for later, not prerequisites that block the owner-requested test scope.
Earlier backup-plan paragraphs are superseded for current execution.


## Current owner extension and reconciliation — 2026-10-07

Latest verified repository baseline: exact main `374dda3db89f6fb87dde7f5b761642440da17bef`, tree `13051743a26f78a50f3a664518c643ff540bd9f9`; GitHub remote equality and completed/success #96/all 12 jobs directly checked. Local checkpoint96 closeout records signed deployment and bounded live checks in PREPRODUCTION_TESTING; no new server verification in this task. This current record supersedes earlier mutable candidate/current-next wording; earlier checkpoint narratives remain LEGITIMATE_HISTORY.

Owner authorizes planning and local development of graphical XAI/SHAP, GIS and geographically anchored entity/findings extraction for existing SIMPA/ORDO. New target inventory rows and ISI-29 sequence are recorded above; first runtime slice 29A is IMPLEMENTED / REVIEW_VERIFIED as an unstaged local candidate, NOT CI_VERIFIED. Planning permission does not approve new institutional methodology, external data providers or a production champion. Exact candidate staging/commit/push, hosted checkpoint and later deployment retain their existing approval gates. Full production is not claimed; SMTP and owner-deferred backups remain unchanged.


## ISI-29A candidate — 2026-10-07

Owner explicitly authorized sequential 29A–29F execution. 29A graphical read model, two analytics integrations, Help and deterministic runner/read-only analyzer now exist locally. Focused tests and synthetic 1440/1280/768/390 visual/keyboard checks pass; local gates PASS; exact-candidate evidence is under `automation/evidence/ISI-29A/`. INV-A22/M22 are PARTIAL because charts are implemented as a candidate while GIS/SHAP/extraction remain TARGET. No as-built geometry/entity pipeline, schema/API/dependency/model change, hosted CI or server mutation is claimed. Candidate remains unstaged; exact owner commit gate remains.


29A local verification record: IMPLEMENTED / REVIEW_VERIFIED candidate; 23 focused and 1203 regression passes, 43 existing native-lane skips, zero failures/errors. Four responsive widths and keyboard backtest selection verified on synthetic local preview. Exact report/fingerprint: `automation/evidence/ISI-29A/human-review.json`. No CI_VERIFIED or server deployment of 29A. 29B–F remain unimplemented; 29B read-only preparation recorded separately.


## ISI-29B GIS dependency decision — 2026-10-07

Local feature contract permits pinned Shapely 2.1.2 for bounded geometry topology validation. Existing NumPy retained; binary wheel only, no host GEOS/GDAL/PROJ install. Official requirements Python>=3.10 and platform wheels support canonical Python3.11/macOS and musllinux x86_64 runtime; actual compatibility is an acceptance gate. Shapely BSD3 and bundled GEOS LGPL2.1 notices remain supply-chain obligations. No CRS reprojection, geocoder, tiles or PostGIS. Source: https://shapely.readthedocs.io/en/2.1.2/installation.html . No installation or deployment verified by this planning record.


## ISI-29A approved main checkpoint and 29B continuation — 2026-10-07

Owner approved exact 29A candidate f220dd3dce9b172c05dc6982167f73b2cd848924b0060d48b1da4143970e492a; committed/pushed main `cad6892fd2d710b8263b936c06bb3d8137cdeddc` and direct remote equality verified with clean worktree. This supersedes mutable 29A unstaged/approval-pending wording; predecessor candidate/CI records remain LEGITIMATE_HISTORY. 29A NOT CI_VERIFIED; latest hosted acceptance #96 remains exact predecessor 374dda3. No CI/server action.

29B scoped geometry/storage/API/domain-adapter candidate is IN_PROGRESS. Contract automation/specs/ISI-29B-GIS-CONTRACTS.md; core_spatial_geometry_versions / migration0035; generic immutable geometry provenance and shared storage, separate SIMPA/ORDO adapters. WGS84 explicit lon/lat only; unknown/projected CRS and invalid topology rejected; no reprojection/provider/geocoder/tiles/PostGIS/indicator or AI changes. One geometry per version, human lifecycle, scoped permissions, immutable fingerprint and content hash. Actual approved boundary dataset absent; synthetic software tests only. Shapely2.1.2 added with existing NumPy preserved; no other lock versions upgraded. Help docs/help/ISI-SPATIAL-DATA-GUIDE.md covers source import/review, with GIS user interface still 29C. Native upgrade/downgrade, regression/dependency/independent review are gates, not yet claimed PASS in this record. 29C–F remain unimplemented. No new staging/commit/push or server mutation authorized by prior29A approval.


## ISI-29B final candidate reconciliation

29A owner-approved main checkpoint cad6892 is locally reviewed/verified, not CI_VERIFIED. INV-B29/C45/M22 now describe the 29B local geometry infrastructure candidate; source licence/location are declared until human attestation, domain identity revalidated, generic registry scoped by product/workspace. Initial package gates passed; final synchronized candidate requires complete repeated local/native gates and independent/human review before exact commit approval. No real boundary dataset, projected CRS support, map UI, SHAP/extraction, hosted checkpoint or server acceptance is claimed. First unfinished runtime package29C. Earlier 29A candidate wording is LEGITIMATE_HISTORY; top-level ledgers/inventory are current.


29B local verification closeout: IMPLEMENTED / REVIEW_VERIFIED unstaged candidate; 42 focused and 1 native PostgreSQL test passed in the pre-final-review cycle (full migration upgrade/downgrade/reupgrade, constraints and stale concurrent write rejection), 1246 regression passes / 43 existing native-lane skips, zero failures/errors. Independent analyzer repeat PASS; runtime dependency audit and fixed musllinux wheel/local import checks PASS. Exact final candidate identity is automation/evidence/ISI-29B/human-review.json, with complete repeated gates on this documentation-synchronized candidate required. This supersedes mutable 29B IN_PROGRESS/verification-pending notes above; previous candidate narratives are LEGITIMATE_HISTORY. No CI/server acceptance or staging/commit/push; institutional geometry dataset/licence and projected CRS remain explicit missing/unsupported states. 29C–F still not implemented.

Final bounded review correction: reject non-string geometry type as a controlled validation failure; require native fixture loopback host before any DB access. Full exact-candidate gates must pass again; final counts/identity in automation/evidence/ISI-29B/human-review.json supersede prior cycle counts. No test gate bypass.


## ISI-29B approved main and ISI-29C implementation — 2026-10-07

29B approved exact candidate1c5a531c6ba7e206a1d822e295d70b2e3377257fc06873872d6c07210331f418 committed/pushed main0d59f40aa03ab7115041f1c58052d4610aac3a54; all28 committed file hashes match approval, clean single main worktree/direct remote equality. Final29B43 focused/native1/regression1247 passes,43 predecessor native skips; NOT CI_VERIFIED, no new server verification. Latest hosted acceptance#96 remains predecessor374dda3. This supersedes mutable29B approval-pending notes; earlier candidate gates/history remain LEGITIMATE_HISTORY.

Owner now explicitly approves all planned verified29A-F commits/pushes; repeated per-candidate commit approval is no longer required. Exact deterministic gates, independent readonly analysis and assistant review remain mandatory.29F acceptance/deployment authorization is subject to usage pre/post, exact committed main CI, signed image/bundle and approved ISI-28 server contract. Shared edge non-target protection remains mandatory. SMTP pending/new backups owner-deferred.

29C locked candidate: automation/specs/ISI-29C-GIS-WORKFLOWS.md. Existing Data surface now includes shared GIS catalogue/import/review/date/layer/version/map/table/selected provenance and explicit geometry export. Existing ORDO spatial-unit identity lifecycle exposed; actual ORDO overview permission source fixed, stable resource code input added. Separate domain selectors; no new navigation/schema/formula/provider/model. Geometry date is not observation period. ORDO exact identity-only stored result viewer revalidates source/methodology/boundary/trace/arithmetic; no result-to-geography association exists for SIMPA, displayed unavailable. No institutional boundary source/licence auto-created.

Actual browser WebGL limitation rejected the Pydeck draft renderer (REMOVE_BEFORE_NEXT_SLICE). Final renderer uses existing Streamlit1.63 components.v2 with fixed code/data-only SVG DOM; no new dependencies/lock/install. Bounded25features/50000coordinates/1MB; render-only Mercator with exact source coordinates retained; safe textContent labels, selection/pan/zoom/keyboard controls and table fallback, no tiles/provider keys/user markup. Local focused/full/browser/independent gates required before IMPLEMENTED/REVIEW_VERIFIED closeout; evidence automation/evidence/ISI-29C.29D-F remain unimplemented. DEFERRED_SERVER_VERIFICATION.

29C dependency metadata: require Streamlit>=1.63 (existing locked1.63.0) for components.v2; previous declared>=1.41 is stale for this new surface, REMOVE_BEFORE_NEXT_SLICE. No lock/package version change/install.


## ISI-29C local verification closeout — 2026-10-07

IMPLEMENTED local candidate:37 focused tests and1283 regression tests pass,44 existing native-lane skips, zero failures/errors; lint/policy/mypy/pip/diff gates PASS. Synthetic desktop1280/mobile390 browser checks PASS: map click/Enter/Space, linked selected table/provenance, ORDO result table/chart, zoom/reset, no page overflow or external assets. Exact synchronized candidate requires matching acceptance/browser/independent-analysis/human-review reports under automation/evidence/ISI-29C before approved staging. First unfinished runtime package29D;29E/F planned. Standing owner approval covers verified commit/push. No new CI/server acceptance; DEFERRED_SERVER_VERIFICATION, no full-production claim. Historical pending notes above are LEGITIMATE_HISTORY superseded by this closeout.


## ISI-29C approved main / ISI-29D attribution candidate — 2026-10-08

29C accepted main a77f9f0b4e43038554ee203a0c5ad22cd0b9e981, exact26-file candidate025263734c8ff82ef85c01f01a229e8724ea22ed6b13cfffb312426bacf7f82d; repeated local7gate/independent twice/assistant review PASS.37 focused/1283 regression passes,44 existing native-lane skips; main/origin/direct equality and clean one-worktree checkpoint recorded. No hosted/server verification inherited. Mutable prior29C candidate/current-next text superseded (LEGITIMATE_HISTORY).

29D IN_PROGRESS locked automation/specs/ISI-29D-MODEL-ATTRIBUTION.md: additive0036 simpa_attribution_artifacts, exact interventional continuous OLS explanation from stored coefficients and revalidated complete-case training cohort. No refitting/dependency/provider/model-family change. Domain-owned source/result/contract/background/artifact hashes and immutable metadata; read revalidates source/methodology and stored metric/prediction parity. Scoped analysis.read, explicit analysis.run creation, fingerprint-only audit. Existing SIMPA result expander gains matrix/heatmap/global mean-absolute/local waterfall and ten-item Help docs/help/ISI-SHAP-GUIDE.md. Technical1e-8 tolerance is not institutional threshold.512 selected rows/24features bounded; original training cohort only, correlated features limitations visible. ORDO naive/seasonal SHAP remains unsupported; conditional new model execution not automatically selected. NOT CI_VERIFIED; server deferred to29F. Local/native/full/browser/independent/human exact gates required before phase closeout. Browser access restored on 2026-10-08; synthetic desktop1280/mobile390 visual/keyboard/viewer/unsupported/tamper gates passed, with screenshots under automation/evidence/ISI-29D/. Contradictory legacy non-SHAP caption corrected only in the new attribution panel. Native0036 test participates in the existing hosted native lane without skips. Final local gates/independent review are rerun on the exact updated candidate before authorized commit/push.29E/F unimplemented; current owner explicitly requests checkpoint/deployment of verified current source in preproduction-testing mode, separate from29F whole-plan completion.


## ISI-29E entity/claim extraction candidate — 2026-10-08

29A–29D are CI_VERIFIED / REVIEW_VERIFIED at exact main 95fec43590e9b1d3eb44d55867666581118ec650 (ISI required acceptance run37746165918, all12 completed/success). Recorded signed deployment and scoped server acceptance passed in PREPRODUCTION_TESTING, schema0036; automation/evidence/ISI-29D/release/closeout.json. No fresh server probe in29E. SMTP pending, new backups owner-deferred, institutional/capacity/operational full-production gates remain open.

29E IN_PROGRESS on canonical main; locked automation/specs/ISI-29E-ENTITY-CLAIM-EXTRACTION.md. Additive0037 core_extraction_requests/artifacts/reviews; shared transport/persistence with separate SIMPA/ORDO prompts and scoped gazetteers. Governed aggregate nonpersonal UTF-8 TXT or validated/frozen snapshot cells only; exact Unicode spans/cells and version/hash/record lineage. Local registered AI queue/model/policy; source/actor/prompt/model/request pinned and checked before/after worker execution and at read. Historical code hash remains provenance; pending execution requires current code parity. No parser/OCR/VLM/geocoder/dependency/model install or new numerical authority. Exact-name suggestions remain unresolved until final attested data.validate review; entity registry identity and separately dated polygon claim scope revalidated. Accepted/rejected reviews append once; only accepted findings participate in scoped exact period/geometry retrieval. Invalidated/purged/reclassified input blocks current quotation/retrieval. No raw-content audit, cross-product retrieval, report promotion or fabricated coordinates/truth/causality. Real-domain extraction quality UNCALIBRATED; separate SR Latin/Cyrillic/EN annotated synthetic fixtures are software tests only. Data workspace gains explicit load/create/cancel/source/review/filter controls and ten-item Help.

Local deterministic focused/native/regression/browser/independent gates required on exact candidate before IMPLEMENTED / REVIEW_VERIFIED and standing approved commit/push. 29E is NOT CI_VERIFIED; DEFERRED_SERVER_VERIFICATION. 29F remains first planned package after verified29E: linked reports/Help/Word and whole-plan acceptance/controlled deployment. Historical candidate/CI notes above are LEGITIMATE_HISTORY; this snapshot supersedes current status statements.


### ISI-29E local closeout authority

IMPLEMENTED / REVIEW_VERIFIED applies only to the exact30-file candidate with matching PASS acceptance.json, browser-verification.json, independent-analysis.json and human-review.json under automation/evidence/ISI-29E. Final synchronized candidate must pass all8 gates again before staging; test counts and file hashes are recorded in those reports. Native0037 upgrade/downgrade/reupgrade uses a disposable loopback PostgreSQL schema. Synthetic desktop1280/mobile390 source/identity/territory review, accepted-only period retrieval, ORDO rejection, Help and no page overflow are exercised; no real model quality certification. Earlier51-focused/1375-regression cycle passed and is retained under verified-cycle-51; a final controlled storage-I/O failure case is included in the synchronized candidate.

Standing owner approval covers verified29A-F commit/push. First unfinished package after verified29E is29F (linked evidence/report/Help/Word/final acceptance and controlled deployment). NOT CI_VERIFIED / DEFERRED_SERVER_VERIFICATION for29E; recorded server remains95fec435/schema0036. No new Actions dispatch, server/Nginx/model mutation or SMTP/backups action occurs here. Real adjudicated extraction quality remains UNCALIBRATED; full-production operational gates remain open.

29E final governance review: general AI jobs retain metadata only for extraction; successful raw input/output/structured copies are cleared in the worker transaction. Quotations remain solely in source-revalidated extraction artifacts, preventing general AI/report reads from bypassing source withdrawal (REMOVE_BEFORE_NEXT_SLICE, resolved in this candidate; legacy non-extraction jobs REQUIRED_COMPATIBILITY). Code fingerprint pins service/contracts/models and the selected product extraction/spatial adapter. Empty pending request text and runtime-policy/model parameter drift fail before provider execution. Signed/decimal/date fragments cannot silently become partial numeric value/period tokens; spelling stays verbatim without numerical interpretation or domain formula. Exact final gates required after these bounded corrections.

## ISI 29F bootstrap and locked implementation 2026-10-08

Canonical main/origin/direct GitHub33e86e6 clean one worktree/empty stash.
29E committed IMPLEMENTED / REVIEW_VERIFIED:60 focused/native1/regression1384
PASS, final30-file exact evidence under automation/evidence/ISI-29E. Last exact
hosted/server authority95fec435/run37746165918/schema0036, no inherited CI29E.
29F contract automation/specs/ISI-29F-EVIDENCE-RELEASE.md is IN_PROGRESS:
linked reports/source invalidation guard, contextual map/XAI and10-item Help,
updated screenshot Word manual, final exact-main acceptance/signed controlled
ISI28 deployment. No new schema/dependency/provider/formula/model or inference.
Inventory affected A14/A22 B21/B22/B23 F01–F05 M09/M22 synchronized here.
Stale live candidate/future24D/25/27 wording REMOVE_BEFORE_NEXT_SLICE resolved
in inventory/technical/ledgers; dated historical records LEGITIMATE_HISTORY,
compatibility reports/staging/legacy read paths REQUIRED_COMPATIBILITY.
Owner standing verified29A-F commit/push approval and current explicit29F
acceptance/deployment apply; usage pre/post/exact12CI/signed bundle mandatory.
Dual-product test account authorized; email owner input pending, password owner
handoff only. SMTP pending/new backups owner-deferred/PREPRODUCTION_TESTING;
real extraction quality UNCALIBRATED/full institutional production not certified.

## Current reconciliation and ISI-30 owner extension — 2026-10-10

29A–29F software is CI_VERIFIED / REVIEW_VERIFIED at exact main f587ed0a194043cadf7190ceae9f6f29c1d76c55, required acceptance37914718258 completed/success (all12 jobs). Recorded signed ISI-only deployment passed in PREPRODUCTION_TESTING, schema20261008_0037; automation/evidence/ISI-29F/release/closeout.json. No fresh server probe in30A. Full institutional production remains unverified; SMTP pending, new backups owner-deferred, extraction quality UNCALIBRATED.

This record supersedes earlier mutable current/candidate statements; dated predecessor checkpoints remain LEGITIMATE_HISTORY. Stale active ledgers/inventory are REMOVE_BEFORE_NEXT_SLICE, resolved in this candidate. Existing route markers/staging/read-only histories REQUIRED_COMPATIBILITY. ISI-30 sequence: docs/roadmap/ISI-30-WORKFLOWS-AND-GUI-PLAN.md; exact first contract automation/specs/ISI-30A-WORKFLOW-SHELL.md. 30A is IN_PROGRESS, not IMPLEMENTED or CI_VERIFIED. Owner authorizes customer workflows and GUI improvement, not new domain formulas/model families/framework/dependencies. GoraNova dual-product account email supplied; owner-entered password onboarding belongs30D. Prior standing commit/push/checkpoint approvals cover29A-F only. No new server action, SMTP configuration, backup creation or non-target mutation.


## ISI-30 continued owner authorization2026-10-10

30A IMPLEMENTED / REVIEW_VERIFIED exact360e841e committed/pushed c92bacc.15 focused/1432 regression passes and1280/390 browser review. Owner now explicitly requests30B–F completion without further confirmations; verified commit/push, final hosted checkpoint and controlled ISI-only deployment authorized within existing plan. Usage, exact acceptance and supply-chain gates preserved. Last CI/server authority remains f587ed0/schema0037.30B1 IN_PROGRESS: scoped source history/quality/version addition, job/run/evaluation/governed-output read and confirmed fresh FAILED retry, exact contract automation/specs/ISI-30B-DATA-WORKFLOWS.md.30B2/B3 and30C–F remain pending. Earlier mutable30A pending statements LEGITIMATE_HISTORY superseded here. No new backend/schema/dependency/domain authority. SMTP pending/new backups owner-deferred; institutional validation not fabricated.


ISI-30B1 local IMPLEMENTED/REVIEW_VERIFIED committed/pushed be2ae69:24focused/1456regression PASS,46 inherited skips,1280/390 synthetic version/upload/evaluation/output/retry/readonly review.30B2 IN_PROGRESS typed existing inbound/batch connector, schema mapping, identity policy, author-entered operational thresholds, activation and idempotent governed upload. Exact contract automation/specs/ISI-30B2-GOVERNED-INGESTION.md; scoped backend remains authority. No formula/schema/dependency/secrets/remote connector added.30B operator/privacy/analytical authoring,30C/D,30E illustrated HelpWord,30F remain pending. Latest CI/server f587ed0 unchanged.


ISI-30B2 IMPLEMENTED/REVIEW_VERIFIED committed/pushed daa1c6e:31focused/1487regression PASS/46 inherited skips,1280/390 synthetic authoring/activation/upload review.30B3 IN_PROGRESS typed analytical dataset/feature registry, field contracts/activation, governed-output snapshot creation, eligible snapshot feature versions and revision-pinned confirmed lifecycles. Exact automation/specs/ISI-30B3-ANALYTICAL-AUTHORING.md. No raw-source promotion, new methodology/formula/schema/dependency.30B4 operator/privacy,30C/D,30E HelpWord and30F still pending; CI/server f587ed0 unchanged.


ISI-30B3 IMPLEMENTED/REVIEW_VERIFIED committed/pushed6a70f46:23focused/1510regression PASS/46 inherited skips,1280/390 synthetic registry/contract/snapshot/feature/lifecycle/read-only checks.30B4A IN_PROGRESS existing backfill/replay/dead-letter operator forms and explicit offset-aware observation time; exact automation/specs/ISI-30B4A-INGESTION-RECOVERY.md.30B4B privacy/record governance,30C/D,30E HelpWord and30F remain pending. No new CI/server claim; f587ed0 remains last proof. Legacy stale30A task registry status REMOVE_BEFORE_NEXT_SLICE corrected to local reviewed completion; task done labels do not confer hosted/server verification.


ISI-30B4A IMPLEMENTED/REVIEW_VERIFIED committed/pushed15204d7:33focused/1543regression PASS/46 inherited skips,1280/390 synthetic backfill/replay/dead-letter/read-only checks.30B4B IN_PROGRESS typed source governance profile and explicit quarantine review/resolution. Record review audit found current accepted record may change after read; additive optional expected_current_accepted_record_id now checked under existing server lock, new UI always supplies reviewed ID or explicit null. Historical omitted-field callers REQUIRED_COMPATIBILITY, no database migration/permission expansion/formula. Inventory INV-A08/A21/B10 reviewed-current resolution contract updated. Retention/anonymization/export/purge30B4C,30C/D,30E and30F remain pending; last CI/server f587ed0 unchanged.


ISI-30B4B IMPLEMENTED/REVIEW_VERIFIED committed/pushed444238e:17focused/1560regression PASS/46 inherited skips,1280/390 synthetic governance/quarantine/review/readonly checks.30B4C IN_PROGRESS existing retention policy/hold/metadata purge request, external anonymization evidence/proposal/review, scoped allowed export. Governance-only paginated anonymization GET added for retrievable review; final review now uses row lock. No database migration, AI method/provider/formula or permission expansion. Physical purge classified OPERATOR_ONLY: no customer execute button or unverified archive claim; existing operator step-up/retention APIs retained. Sensitive export remains fail-closed with real MFA requirement.30C/D,30E HelpWord,30F remain pending; last CI/server f587ed0 unchanged.


## 2026-10-10 — 30B privacy closeout / 30C1 scope lock
ISI-30B4C IMPLEMENTED/REVIEW_VERIFIED committed/pushed606fc92:21focused/1581regression PASS/46 inherited skips,1280/390 synthetic privacy controls/read-only/ORDO checks.30B customer data workflows locally reviewed; physical purge OPERATOR_ONLY, real sensitive-export MFA remains fail-closed.30C1 IN_PROGRESS typed existing global SIMPA methodology/reference-suite/statistical lifecycle; global registry/supersession disclosed, no formula or automatic approval. Contract automation/specs/ISI-30C1-SIMPA-METHODOLOGY-WORKFLOWS.md.30C2 ORDO,30D,30E illustrated HelpWord,30F pending. Last CI/server f587ed0 unchanged.


## 2026-10-10 — 30C1 reviewed closeout / 30C2A scope lock
30C1 IMPLEMENTED/REVIEW_VERIFIED committed/pushed ef2b1c0:29focused/1610regression PASS/46 inherited skips,1280/390 synthetic SIMPA methodology/reference/statistical lifecycle. No CI/server inheritance.30C2A IN_PROGRESS existing ORDO global methodology lifecycle, explicit authored time-series parameters and confirmed forecast execution. Contract automation/specs/ISI-30C2A-ORDO-METHODOLOGY-WORKFLOWS.md. Global registry/supersession disclosed; existing source_requirements now returned for review.29 historical route E702 findings resolved by statement-only splitting with identical AST; no transaction change.30C2B internal statistical/spatial customer reachability remains named pending, no fitting service invented.30D,30E HelpWord and final30F remain pending. Latest hosted/server f587ed0 unchanged.


## 2026-10-11 — 30C2A reviewed closeout / 30C2B1 scope lock
30C2A IMPLEMENTED/REVIEW_VERIFIED committed/pushed90b01b9:32focused/1642regression PASS/46 inherited skips,1280/390 synthetic method/authoring/forecast/keyboard.30C2B1 IN_PROGRESS existing identity-based ORDO spatial aggregation customer endpoint/form. Reviewed current methodology ID checked under row lock; current numerical truth remains existing GIS revalidation. Exact automation/specs/ISI-30C2B1-ORDO-SPATIAL-WORKFLOW.md. No schema/migration/geometry join/weights/new formula/dependency.30C2B2 statistical metadata reachability,30D,30E HelpWord/final30F pending. Last hosted/server f587ed0 unchanged.


## 2026-10-11 — 30C2B1 reviewed closeout / 30C2B2 scope lock
30C2B1 IMPLEMENTED/REVIEW_VERIFIED committed/pushed5c90be1:21focused/1663regression PASS/46 inherited skips,1280/390/native keyboard synthetic spatial QA.30C2B2 IN_PROGRESS customer-scoped existing statistical specification authoring/list/review/lifecycle. Exact automation/specs/ISI-30C2B2-ORDO-STATISTICAL-WORKFLOW.md. Current method reviewed-ID lock, scoped transition row/status/hash precondition, existing backend input revalidation. Fitting NOT_IMPLEMENTED/numerical_results NOT_PRESENT explicitly shown; no schema/migration/model-family/formula/dependency expansion.30D,30E HelpWord and final30F pending. Hosted/server f587ed0 unchanged.

## 2026-10-11 — 30C reviewed closeout / 30D1 scope lock
30C2B2 IMPLEMENTED/REVIEW_VERIFIED committed/pushed53d29bd:23focused/1686regression PASS/46 inherited skips,1280/390/native synthetic QA. Existing30C SIMPA/ORDO analytical reachability locally reviewed; statistical metadata does not imply fitting.30D1 IN_PROGRESS scoped administrative confirmations, safe receipts, typed transports and existing member-session reachability. Exact automation/specs/ISI-30D1-ADMINISTRATION-WORKFLOWS.md. Backend RBAC/last-admin/MFA/multi-org session restrictions unchanged.30D2 AI/results/onboarding,30E illustrated HelpWord and30F acceptance/deployment pending. Last hosted/server f587ed0 unchanged.

## 2026-10-11 — 30D1 reviewed closeout / 30D2 scope lock
30D1 IMPLEMENTED/REVIEW_VERIFIED committed/pushed174b57b:18focused/1704regression PASS/46 inherited skips,1280/390/native admin QA.30D2 IN_PROGRESS AI scoped evidence/job/evaluation XAI and existing report.publish human review; optional locked reviewed-status/result-hash precondition preserves legacy callers. Explicit local diagnostic selection/confirmation, bounded typed evidence and safe errors. Exact automation/specs/ISI-30D2-AI-REVIEW-WORKFLOWS.md. No provider/model/dependency/schema persistence expansion.30D3 result/auth/onboarding,30E HelpWord and30F pending. Hosted/server f587ed0 unchanged.

## 2026-10-11 — 30D2 reviewed closeout / 30D3A scope lock
30D2 IMPLEMENTED/REVIEW_VERIFIED committed/pushed48e452d:20focused/1724regression PASS/46 inherited skips,1280/390/native AI review QA.30D3A IN_PROGRESS faithful typed domain evidence views replacing default raw JSON, bounded failures. Exact automation/specs/ISI-30D3A-TYPED-RESULT-VIEWS.md. Existing charts/domain contracts/SHAP/GIS/source revalidation unchanged; optional technical GeoJSON REQUIRED_COMPATIBILITY. Three inherited presentation assertions explicitly updated with stronger semantic coverage; no weakened domain gate.30D3B report/account workflows,30E HelpWord,30F pending. Hosted/server f587ed0 unchanged.

## 2026-10-11 — 30D3A reviewed closeout and30D3B scope lock
30D3A IMPLEMENTED/REVIEW_VERIFIED eabdc3f:17focused/1741regression PASS/46 inherited skips, seven gates and1280/390/native typed-evidence QA.30D3B IN_PROGRESS explicit report source/version/lifecycle confirmations and optional reviewed-evidence preconditions under scoped report/version locks; exact automation/specs/ISI-30D3B-REPORTING-WORKFLOWS.md. Legacy callers/linked revalidation/permissions retained; no schema migration/formula/provider expansion.30D4 account/security/onboarding,30E illustrated HelpWord,30F checkpoint/deployment pending; hosted/server f587ed0 unchanged.


## 2026-10-11 — 30D3B reviewed closeout and30D4 scope lock
30D3B IMPLEMENTED/REVIEW_VERIFIED b6812a4:40focused/1781regression PASS/46 inherited skips, seven gates and1280/390/native reporting QA.30D4 IN_PROGRESS typed self-session inventory, fresh identity/status-bound revoke confirmations and safe receipts; existing invitation/recovery/pending SMTP preserved. Exact automation/specs/ISI-30D4-ACCOUNT-SECURITY-WORKFLOWS.md. No auth backend/schema/provider/role expansion; GoraNova real onboarding remains controlled30F, owner credential entry. Illustrated HelpWord30E and final30F pending; hosted/server f587ed0 unchanged.


## 2026-10-11 — 30D4 reviewed closeout and30E scope lock
30D4 IMPLEMENTED/REVIEW_VERIFIED e3ac9c7:24focused/1805regression PASS/46 inherited skips, seven gates and1280/390/native self-session QA.30E IN_PROGRESS governed101 new reviewed screenshot assets,36 basic topics/19 detailed Help chapters, current source/lifecycle/security directions and Word parity. Exact automation/specs/ISI-30E-ILLUSTRATED-HELP-MANUAL.md; asset paths/source hashes enumerated in automation/contracts/ISI-30E-ASSET-PLAN.json. Public six-topic allowlist and product-only SHAP preserved; old artifacts legitimate dated history. Word layout/every-page review and final gates pending; no CI/server inheritance. Real GoraNova onboarding and final checkpoint/ISI-only deployment30F remain pending; last hosted/server f587ed0 unchanged.

## 2026-10-11 — 30E local illustrated Help and Word closeout

30E locally IMPLEMENTED/REVIEW_VERIFIED: seven local gates PASS,6 focused/1812 regression passes/46 inherited skips, native1280/390 keyboard/public/product Help checks,197/197 individually reviewed Word pages and152 figures.36 basic topics/19 chapters/138 dated assets include101 new30 workflow images. Five stale Help regression assertions reconciled with delivered SHAP/product boundaries; no skipped or weakened domain gate. No backend/schema/provider/dependency change. Word hash089cbc886486c7a1be13a5c888c4ab839a44db03ad7295e1892b3464eeffefce. Final exact-main hosted checkpoint, signed ISI-only deployment and real GoraNova onboarding remain30F; last CI/server f587ed0/37914718258 unchanged. SMTP pending, new backups owner-deferred, institutional/MFA/calibration/legal facts remain separately unverified.

## 2026-10-11 — 30F final release execution lock

30E reviewed/pushed main29a75eafec93af92cb5a7c4302c089f6bf053d86: seven local gates,
1812 regression passes /46 environment-dependent skips, six focused passes,
independent analysis/exact review, native desktop/mobile Help and all197 Word
pages reviewed. 30F is ACTIVE under automation/specs/ISI-30F-FINAL-ACCEPTANCE-DEPLOYMENT.md.
The final exact-main hosted checkpoint and ISI-only server activation are pending;
last confirmed hosted/server remains f587ed0a194043cadf7190ceae9f6f29c1d76c55.
SMTPpending, owner-deferred new backups and PREPRODUCTION_TESTING remain in force.
Canonical system inventory impact: NONE (existing components/boundaries unchanged).

## 2026-10-12 — 30F verified release and account closeout

Software phases30A–30F are implemented and reviewed. Exact source
0e8bf51382e776818959f68bffa608df3105f4af passed required acceptance38177682021
(all12 jobs success;1858 regression tests/46 environment skips,48 native PostgreSQL
tests without skips). Owner-signed bundle/image/SBOM/scan/source and every payload
hash verified; ISI-only server activation and live application/RQ/S3 acceptance PASS.
Localmain,GitHubmain,servermain and runtime lock matched that exact source with
clean trees. Schema0037 unchanged; existing table counts, ISI stores, non-target
container identities and central Nginx digest preserved. All15 public ISI routes
and Krcuga8443/OralScanXAI8444 return200 under normal TLS; live Help1280/390 PASS.
197-page/152-figure Word manual individually visually reviewed.

contact@goranova.org personally activated through protected local credential entry;
existing auth/invitation/RBAC verified both SIMPA and ORDO workspace selections,
analyst role, no platform-admin grant, separate GoraNova test organization. Owner
subsequently logged into the public application; authenticated ORDO test workspace
and both product choices were observed. No password/token exposed to evidence.

This documentation closeout has no runtime/schema/dependency or inventory impact.
It is subject to its own final exact-main acceptance and signed ISI-only activation;
source-specific0e8bf51 evidence is not inherited as CI for a later SHA. Execution
evidence is under automation/evidence/ISI-30F. SMTPpending, no new backups per owner,
PREPRODUCTION_TESTING retained. Full institutional-production certification,
real-data methodology/extraction calibration, alert delivery/offsite recovery and
remaining legal identity facts are not claimed by this technical release.

30F live GUI recovery: active historical SIMPA ISI08/09 and ORDO ISI10 copy is
REMOVE_BEFORE_NEXT_SLICE, resolved by bounded current Serbian overview/indicator
descriptions and separate analytics/AI navigation. Dead ORDO placeholders remain
REQUIRED_COMPATIBILITY; dated manual examples LEGITIMATE_HISTORY. No runtime
behavior/schema/permission/model/provider/dependency/inventory change. New copy
tests/full regression and exact final acceptance required before activation.

## 2026-10-18 — Help illustration parity candidate

Owner-prioritized Help review found that multi-screen workflow content was hard to
find: the shared selector followed the full short-topic content, while SIMPA/ORDO
combined short topics and detailed workflows in one selector. The local candidate
places separate short-topic and detailed-workflow selectors at the top of the
authenticated Help pages and shows desktop screenshot counts on each option. Related
shared topics state the detailed-image count and names. Public Help remains
six-topic allowlisted, product-specific Help remains isolated, and SIMPA SHAP stays
SIMPA-only. Exact ordered identity/hash comparison confirms that all Word
illustrations are included in Help:122 placements across96 unique desktop captures.
No synthetic replacement or new product capability was added. The desktop Word
manual was rebuilt and rendered:182 pages,250 indexed entries,500 internal links;
all pages passed visual review. Focused Help tests pass:27 passed; the full suite
passes with1823 passed and46 inherited skips. All seven deterministic local gates
and the independent exact-candidate analyzer pass. This establishes local
IMPLEMENTED/REVIEW_VERIFIED only. On 2026-10-18 the owner explicitly requested
publication to the existing ISI endpoint for colleague review, superseding the
prior planned owner walkthrough before commit/deployment. Exact-main hosted
acceptance and controlled ISI-only deployment remain required before
CI_VERIFIED/SERVER_VERIFIED. Canonical system inventory impact: INV-A21
presentation/discoverability only.
