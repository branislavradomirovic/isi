# ISI Autonomous Industrialization Status

## Current reconciliation and owner-requested ISI-29 — 2026-10-07

Authoritative development baseline: main/origin/main/direct GitHub main `a77f9f0b4e43038554ee203a0c5ad22cd0b9e981`,29A/B/C approved commits. Latest hosted acceptance #96 /37515814577 completed/success applies only to predecessor374dda3; all12 jobs green. Local checkpoint96 closeout records signed scoped test deployment PREPRODUCTION_TESTING, SMTP pending, new backups owner-deferred, full_production_claim=false. No new server probe in29C. Earlier mutable current/next and R3 candidate text below is checkpoint history, superseded by current records.

ISI-28 remains IN_PROGRESS for full production under owner-narrowed PREPRODUCTION_TESTING. ISI-29A is owner-approved on main cad6892, locally verified, NOT CI_VERIFIED. ISI-29B is owner-approved on main0d59f40; 29C approved main a77f9f0;29D attribution candidate IN_PROGRESS,29E/F planned. Standing owner approval covers verified29A-F commits/pushes. SMTP and new backups remain owner-deferred. Latest hosted acceptance #96 applies only to predecessor374dda3; no hosted/server action in29. Current record at end supersedes earlier candidate wording.


This is the human-facing live execution ledger. The MasterPlan is the canonical roadmap/architecture/governance authority; `automation/tasks.json`, accepted code, exact-main GitHub Actions and recorded evidence provide synchronized execution proof.

Last status update: 2026-10-05.

## Current execution

Last accepted implementation slice: `ISI-27D - Exact-Main RC Acceptance & Phase Closeout`. Accepted release candidate: `2b1f2ef20a2310df23947f2ac2128d16f81a98ea` — **CI_VERIFIED / REVIEW_VERIFIED**, checkpoint #93, all 12 jobs success. Signed release bundle verified. Current checkpoint: `ISI-28 - Current Server Controlled Upgrade`.

Separate owner-approved public portal audit remediation `ISI-PUBLIC-PORTAL-AUDIT-REMEDIATION-R1` is accepted on main `c177f9d705efd6f68d95ef7d13847b03a8e19229`, with local acceptance and review PASS, NOT CI_VERIFIED and NOT SERVER_VERIFIED. It fixes the icon-only document catalog, English knowledge routes/visible Serbian fallback and the mobile Documents hero. Existing favicon, robots, sitemap, manifest, metadata, 404, accessibility and responsive contracts were checked; desktop and 390px mobile preview passed. No production deployment of this remediation has occurred. Earlier unstaged/no-push wording is superseded accepted history. Evidence: `automation/evidence/ISI-PUBLIC-PORTAL-AUDIT-REMEDIATION-R1/acceptance.json`.

`ISI-PUBLIC-LEGAL-NOTICES-DRAFT-R1` produced internal SR-Latn Terms and Privacy drafts with EN working translations and an owner/legal publication checklist. They are explicitly not publishable until the legal entity, controller/processor roles, processing purposes and bases, cookies, providers/transfers, retention, rights contacts, content licensing, and legal terms are confirmed. The public portal currently has no Terms/Privacy page or footer links. No live page, database, deployment, or production configuration changed. The exact current public site was read-only checked on 2026-10-04; it still shows the document-index claim and existing public content.

ISI-27 is **COMPLETE / CI_VERIFIED** for exact RC `2b1f2ef20a2310df23947f2ac2128d16f81a98ea`. Owner-approved checkpoint #93 and signed artifact verification passed; usage pre/post 158/191 of 2000 minutes. The owner approved continuation to full production. **ISI-28 is IN_PROGRESS**, beginning with read-only server reconciliation under `automation/specs/ISI-28-R1-CONTROLLED-PRODUCTION-UPGRADE.md`. Terms/Privacy factual publication and live operational/provider/backup/capacity gates remain open. SERVER_VERIFIED=false.

Current checkpoint: `ISI-28 - Current Server Controlled Upgrade`.

Accepted checkpoint: `ISI-25A - AI/MLOps Governance + Evaluation Foundation` is accepted on main SHA `f0047321ee4410522697144ecfa464087f1b83bc`, tree `06e419ec656ee2fb0bfb74b4a6b10d42ef275f25`, after local deterministic acceptance and assistant human review.

Accepted checkpoint: `ISI-25B - Evaluation + Promotion Runtime` is implemented and accepted on main SHA `7e11ee2a6f7546eacc3207e15cacfc35f6d04f3e`. It preserves unbound 25A selected-model-only compatibility, binds governed jobs to exact registrations, enforces registered fallback/circuit/provider/review gates, separates frozen promotion benchmarks from foundation fixtures, adds deterministic evaluators and capability thresholds, and implements evidence-gated promotion/rollback, on-demand drift and faithful shared AI XAI.

Accepted checkpoint: `ISI-26-R1 - Full Performance, Load & Resilience Implementation` is implemented and accepted on main SHA `e4b5b7f5927bc553fd616800d37beb5d115bb46e`, tree `9a30b280ba44798b987167c155f0be6ccc13776e`, from human-reviewed candidate fingerprint `98653d20a5223d4f6be66f3ee2017f998865b00ecb08a0950c07123d60dc2e24`. Focused/regression checks, synthetic performance evidence, native PostgreSQL acceptance, full local regression, assistant human review, independent analysis, exact staging, normal push and remote equality all passed. Hosted GitHub Actions were not dispatched; production capacity and live server verification remain unverified by design.

No GitHub-hosted full acceptance ran for ISI-25A/25B or ISI-26 R1 under the current owner cost/acceptance policy, so `CI_VERIFIED` is not claimed for ISI-25 or ISI-26. Overall ISI-25 and ISI-26 are `IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED`. Hosted full acceptance remains reserved for the controlled ISI-27 release-candidate checkpoint.

Shared deployment target authority is central Nginx `central-ingress-nginx-1` (Compose project `central-ingress`, service `nginx`). Caddy is not current ISI target authority. The owner-locked public endpoint is `https://isi.opus.rs:8445/`; Krcuga `:8443` and OralScanXAI `:8444` are strict non-target shared-host services. ISI `api` and `streamlit` retain external `isi_ingress` aliases `isi-api` and `isi-streamlit`; repository `isi-edge` is pre-cutover compatibility only.

Server/live-host verification remains `DEFERRED_SERVER_VERIFICATION`. No server, DNS, certificate, central-ingress, real SMTP, production-secret/data or server-Ollama mutation is authorized before owner-approved ISI-28.

ISI-24E remediation/closeout implementation state: `COMPLETE / CI_VERIFIED`.

Accepted ISI-23D implementation SHA: `a39caa8160f01dee4e30ab7912a732f0aa68c0d6`.

Accepted ISI-23D implementation tree: `05384a755462790484794714e741f74762d6da0d`.

Authoritative ISI-23D GitHub Actions: `ISI required acceptance` run #83, run ID `35081472982`, exact SHA `a39caa8160f01dee4e30ab7912a732f0aa68c0d6`, conclusion `success`; policy, quality, tests, architecture-security, migration, native-postgres, compose, supply-chain, build and aggregate `acceptance` all passed.

Accepted ISI-23E closeout SHA: `3894f5d4ce9b78abc39f9a565fecf83bc2ce7a73`.

Accepted ISI-23E closeout tree: `29c84c2bac1251af6e18c0a9dbccc6c52e69a97a`.

Authoritative ISI-23E GitHub Actions: `ISI required acceptance` run #84, run ID `35084716444`, exact SHA `3894f5d4ce9b78abc39f9a565fecf83bc2ce7a73`, conclusion `success`; the exact-main closeout is accepted.

Overall `ISI-23-SIMPA-PRODUCTION-METHODOLOGY` is `COMPLETE / CI_VERIFIED`.

Historical ISI-23C checkpoint retained for canonical traceability:

Accepted final ISI-23C canonical main SHA: `a49b3faf171dfdbcf9306cfbe50fdc6ad1aabbff`.

Accepted final ISI-23C tree: `1a48b09d0712fdee65dbb349ffc6f71ad46b99dd`.

Authoritative ISI-23C GitHub Actions: `ISI required acceptance` run #82, run ID `35075352285`, exact SHA `a49b3faf171dfdbcf9306cfbe50fdc6ad1aabbff`, conclusion `success`; aggregate `acceptance` passed after the narrow runtime dependency-lock recovery.

Historical ISI-23B checkpoint retained for canonical traceability:

Accepted ISI-23B implementation SHA: `088fe79904bd0cc85c4d52d5442218884501b538`.

Accepted ISI-23B implementation tree: `5f8530f6fc7ca82afe7050f39a9f787b048fd8db`.

Authoritative ISI-23B GitHub Actions: `ISI required acceptance` run #79, run ID `35018144968`, exact SHA `088fe79904bd0cc85c4d52d5442218884501b538`, conclusion `success`; aggregate `acceptance` passed.

Historical ISI-23A checkpoint retained for canonical traceability:

Accepted ISI-23A implementation SHA: `238a881ef39906a2adebbb03fabe80a043017697`.

Accepted ISI-23A implementation tree: `3778f29627100fb48ba369f0618250534870d0a8`.

Authoritative ISI-23A GitHub Actions: `ISI required acceptance` run #77, run ID `34900812947`, exact SHA `238a881ef39906a2adebbb03fabe80a043017697`, conclusion `success`; aggregate `acceptance` passed.


Historical ISI-22G closeout checkpoint retained for canonical traceability:

Accepted ISI-22G implementation SHA: `fd0e46631b5047c64b731d041645e528292f3664`.

Accepted ISI-22G implementation tree: `1a405a65a6fa67f2845ee0a10f2a6f44b11e355e`.

Authoritative ISI-22G GitHub Actions: `ISI required acceptance` run #75, run ID `34856573722`, exact SHA `fd0e46631b5047c64b731d041645e528292f3664`, conclusion `success`; aggregate `acceptance` passed.

Historical predecessor checkpoint retained for canonical traceability:

Accepted ISI-22F implementation SHA: `cfe1574532df65589132bbdd10625172b32fb959`.

Accepted ISI-22F implementation tree: `5afd978151a49d3f3ff897dd47481faf2438cbac`.

Authoritative predecessor GitHub Actions: `ISI required acceptance` run #73, run ID `34787001102`, exact SHA `cfe1574532df65589132bbdd10625172b32fb959`, conclusion `success`.

Earlier historical checkpoint retained for canonical policy/test traceability:

Accepted ISI-22E implementation SHA: `44002aa0774a902bdf2d7a0ae56ff3558303571c`.

Accepted ISI-22E implementation tree: `15578107fb21b6aae174a4bf77fc62812377949c`.

Authoritative earlier predecessor GitHub Actions: `ISI required acceptance` run #70, run ID `34774329038`, exact SHA `44002aa0774a902bdf2d7a0ae56ff3558303571c`, conclusion `success`.

Server/live-host verification: `DEFERRED_SERVER_VERIFICATION`. No production deployment or production-data mutation is implied.

Overall `ISI-22-INDUSTRIAL-DATA-PLATFORM` is `COMPLETE / CI_VERIFIED`. The mandatory whole-phase gap/legacy audit and ISI-22G closeout are complete; no Phase-22 `REMOVE_BEFORE_NEXT_SLICE` finding remains open.

Accepted ISI-24A implementation SHA: `04b0738933030f1d69de52f9260c7b2f11042d0e`.

Accepted ISI-24A implementation tree: `6c688c698fb5bf9520e0a4437c5f372a9790df2c`.

Authoritative ISI-24A GitHub Actions: `ISI required acceptance` run #85, run ID `35138374174`, exact SHA `04b0738933030f1d69de52f9260c7b2f11042d0e`, conclusion `success`. ISI-24A is `COMPLETE / CI_VERIFIED`.

Accepted ISI-24B implementation SHA: `0ad913db23cea44033e8adf693eb179edfa8fb5d`.

Accepted ISI-24B implementation tree: `1008022ebe4cf95b4d45a12ff746188e6c8efa11`.

Authoritative ISI-24B GitHub Actions: `ISI required acceptance` run #86, run ID `35147730914`, exact SHA `0ad913db23cea44033e8adf693eb179edfa8fb5d`, conclusion `success`. ISI-24B is `COMPLETE / CI_VERIFIED`.

Accepted ISI-24C implementation SHA: `76e4ca5265f48a096d2253c88898e1aaedbff991`.

Accepted ISI-24C implementation tree: `0a6ec7b7ab4db5d43c570c714c065f8fef7093f4`.

Authoritative ISI-24C GitHub Actions: `ISI required acceptance` run #87, run ID `35153774409`, exact SHA `76e4ca5265f48a096d2253c88898e1aaedbff991`, conclusion `success`. ISI-24C is `COMPLETE / CI_VERIFIED`.

Accepted ISI-24D implementation SHA: `49377e808845fc8746f0484ea7b452954c9e83b4`.

Accepted ISI-24D implementation tree: `c8ea52299d80551ee303dbeef95d343b59448892`.

Authoritative ISI-24D GitHub Actions: `ISI required acceptance` run #88, run ID `35220908672`, exact SHA `49377e808845fc8746f0484ea7b452954c9e83b4`, conclusion `success`. ISI-24D is `COMPLETE / CI_VERIFIED`.

Accepted ISI-24E remediation/closeout implementation SHA: `5937daa2ea7ff9c476bd6a05a04841d1534aefe2`.

Accepted ISI-24E remediation/closeout implementation tree: `6e75bf1cd13b95e23f9189b9e94453dd130eaa19`.

Authoritative ISI-24E GitHub Actions: `ISI required acceptance` run #90, run ID `35238623960`, attempt 2, exact SHA `5937daa2ea7ff9c476bd6a05a04841d1534aefe2`, conclusion `success`; `native-postgres`, ISI-19 recovery rehearsal and aggregate `acceptance` are green.

Overall `ISI-24-ORDO-PRODUCTION-METHODOLOGY` is `COMPLETE / CI_VERIFIED`. The mandatory whole-phase audit is closed: F01 and F02 are resolved, no Phase-24 `REMOVE_BEFORE_NEXT_SLICE` finding remains, and F08 remains explicitly deferred as `REMOVE_IN_NAMED_PHASE(ISI-25/ISI-27)`.

ISI-26 whole-phase closeout evidence: R1 is accepted on main SHA `e4b5b7f5927bc553fd616800d37beb5d115bb46e` (tree `9a30b280ba44798b987167c155f0be6ccc13776e`) from candidate fingerprint `98653d20a5223d4f6be66f3ee2017f998865b00ecb08a0950c07123d60dc2e24`. ISI-26A through ISI-26D are satisfied as formal coverage/gate checkpoints through that accepted R1 implementation; ISI-26E closes the whole-phase audit. No `REMOVE_BEFORE_NEXT_SLICE` finding remains open. Timing remains `UNCALIBRATED` exactly where the locked R1 calibration policy requires it, portable resource evidence remains `UNAVAILABLE`, and neither state is converted into a fabricated production SLO.

Overall `ISI-26-PERFORMANCE-LOAD-RESILIENCE` is `IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED`. `PRODUCTION_CAPACITY_VERIFIED=false`, `SERVER_VERIFIED=false`, and `GITHUB_ACTIONS_DISPATCH=NO` remain binding. ISI-27 B0-R1A bootstrap is CLOSED/PASS, the ISI-27 scope is locked, and ISI-27A is accepted on main and 27D is current; the current next action is `ISI-28 - Current Server Controlled Upgrade`. ISI-28 remains the exclusive authority for live server/DNS/certificate/central-ingress/SMTP/production-secret/data/server-Ollama mutation. Krcuga and OralScanXAI remain strict non-targets.

## ISI-27 scope lock

Corrected B0-R1A authority: DONE=6, PARTIAL=8, MISSING=5, DRIFT=0; 13 release blockers are not DONE. The corrected Help/XAI blocker set contains 12 shared production-critical surfaces. SBOM/signed provenance/attestation is MISSING, while image vulnerability enforcement is also MISSING.

Execution is deliberately grouped into four larger formal gates: **27A Shared Help & Release UX Completeness -> 27B RC Evidence & Governance Pack -> 27C Reproducible Release & Supply-Chain Assurance -> 27D Exact-Main RC Acceptance & Phase Closeout**. 27D is owner-controlled and owns the single explicit hosted release-candidate acceptance cycle. No hosted CI is authorized by scope lock itself.

Current next action: execute the owner-approved ISI-28 read-only server reconciliation after CI-verified signed RC #93. Server/live-host work remains frozen through ISI-27 and belongs exclusively to ISI-28. Krcuga and OralScanXAI remain strict non-targets.

## Mandatory bootstrap rule

Every new chat/task/function starts by reading the complete MasterPlan, reconstructing exact repository/CI state and prior accepted architecture/decisions, inspecting relevant as-built code, producing `DONE / PARTIAL / MISSING / DRIFT`, and performing the mandatory legacy/drift audit. Conflicting legacy is removed before the next slice unless explicitly classified as required compatibility/history or assigned to a named cleanup phase.

## Owner-facing state model

`BOOTSTRAP_VERIFIED -> SPEC_READY -> IMPLEMENTING -> IMPLEMENTED -> REVIEW_VERIFIED -> OWNER_APPROVED_MAIN_COMMIT -> CI_VERIFIED -> COMPLETE`

A failed required gate returns the active task to implementation/fix state. Required gates must not be weakened merely to make a task green.

## Industrialization roadmap

| Order | Task | Live status |
|---:|---|---|
| 17 | Autonomous Development Harness + CI | **COMPLETE** |
| 18 | Observability & Operational Diagnostics | **COMPLETE** |
| 19 | Backup, Restore & Disaster Recovery | **COMPLETE** |
| 20 | Enterprise Security Completion | **COMPLETE / CI_VERIFIED** |
| 21 | Data Governance & Privacy Controls | **COMPLETE / CI_VERIFIED** |
| 22 | Industrial Data Platform | **COMPLETE / CI_VERIFIED - 22A through 22G complete** |
| 23 | SIMPA Production Methodology + Help/User Guide | **COMPLETE / CI_VERIFIED - 23A through 23E complete** |
| 24 | ORDO Production Methodology + Help/User Guide | **COMPLETE / CI_VERIFIED - 24A through 24E complete** |
| 25 | Industrial AI / MLOps | **IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN - 25A f004732; 25B 7e11ee2; NOT CI_VERIFIED** |
| 26 | Performance, Load & Resilience | **IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED - R1 e4b5b7f; 26E closeout complete** |
| 27 | Industrial Release Candidate & Acceptance Pack | **COMPLETE / CI_VERIFIED exact RC 2b1f2ef / SERVER_VERIFIED=false** |
| 28 | Current Server Controlled Upgrade | **DEFERRED - fresh explicit owner approval required** |

## Locked execution boundaries

- Canonical authority: `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`.
- Canonical repo: `/Users/branislavradomirovic/Applications/Python/ISI`, branch `main`, exactly one worktree.
- Normal workflow is direct-main; branch/PR exceptions require explicit owner approval.
- ISI uses the standard `codex` CLI authenticated with the canonical owner account; project-specific wrappers/`CODEX_HOME` profiles are legacy and not active authority.
- Candidate stays unstaged/uncommitted through runner, analyzer and assistant human review; exact staging/commit/push requires explicit owner approval.
- `CI_VERIFIED` requires exact-main `ISI required acceptance` completed/success at an explicitly approved acceptance/release checkpoint; implementation-complete phases may remain explicitly `NOT CI_VERIFIED` when hosted acceptance is deliberately deferred by owner policy.
- SIMPA and ORDO remain the only current domain applications and remain domain-isolated over shared infrastructure.
- Numerical truth is deterministic/versioned statistical/ML output; LLM/VLM remains bounded evidence synthesis/explanation.
- Current server/DNS/ingress/real SMTP/production secrets/data/server Ollama remain frozen through ISI-27; only ISI-28 may authorize mutation.


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

At this historical handoff, parent ISI-27 was `IN PROGRESS` and the active checkpoint was **ISI-27B — RC Evidence & Governance Pack** (`spec_ready`). ISI-27C and ISI-27D were planned; ISI-28 remained deferred as the only server-mutable phase. Current authority is the later ISI-27D checkpoint record below.

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
Current checkpoint: `ISI-28 - Current Server Controlled Upgrade`.

The owner-approved 27C R2 implementation is accepted on main `b6f0bfaf453360da72f866d4bbd1d47b51655bf4` after the local gate set and independent review passed. Fingerprinted evidence is recorded under
`automation/evidence/ISI-27C/` and records 1,159 regression tests
(43 existing skips), 45 native PostgreSQL tests (0 skips), restore/recovery,
all 10 performance scenarios, quality, policy, diff and Compose PASS. The exact
amd64 Wolfi image has 117 CycloneDX components, zero HIGH/CRITICAL Trivy 0.75.0
findings and passing Python/UTC/API/Streamlit/auth-boundary checks. This is an
accepted implementation, not CI_VERIFIED or SERVER_VERIFIED. 27D is
specification-ready but awaits its separate usage precheck and explicit approval;
ISI-28 has not run.
No hosted/server acceptance is claimed.

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
is ignored and no release/server gate is bypassed. Owner approved the bounded
R2 proposal in `automation/specs/ISI-27C-R2-MINIMAL-RUNTIME-BASE-PROPOSAL.md`.
The Wolfi/Python 3.11 implementation passed the full local gates and is accepted
on main `b6f0bfaf453360da72f866d4bbd1d47b51655bf4`. It is not CI_VERIFIED or
SERVER_VERIFIED; 27D is specification-ready and ISI-28 deferred. No hosted
dispatch or production deployment occurred.

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

## ISI-27D closeout and ISI-28 start — 2026-10-05

Checkpoint #93 accepted exact RC `2b1f2ef20a2310df23947f2ac2128d16f81a98ea`; all 12 jobs passed and signed bundle verified. See `automation/specs/ISI-27D-ACCEPTANCE-CLOSEOUT.md`. The owner approved continuation to full production; read-only server audit is the first ISI-28 action. Legal publication and actual server acceptance remain open. Historical failed runs #91/#92 remain preserved; no failed run authorizes deployment.

Accepted predecessor states: **27A ACCEPTED ON MAIN / 27B ACCEPTED ON MAIN / 27C ACCEPTED ON MAIN**; the consolidated exact RC is CI_VERIFIED through #93.

Current execution state: **ISI-28 IN_PROGRESS**; exact ISI-27 RC is CI_VERIFIED, production remains unverified.

ISI-28 local legal-page discovery candidate: published localized footer links,
sitemap inclusion and desktop/mobile layout prepared; legal text remains draft.
Full regression observed one governance wording failure; corrected MasterPlan
current-checkpoint wording and reran the affected contract plus legal tests
successfully (14 tests). All other regression cases passed (43 existing skips).
Read-only server audit remains blocked: the confirmed target rejects the existing
key even through the working SSH agent socket. Public routes return HTTP 200,
but live robots disallows all indexing and legal links are absent. No deployment
or source/server alignment is asserted. Registered legal addresses and GoraNova
legal entity remain factual publication prerequisites. Proposed operational
periods are in `docs/ops/ISI-28-PRIVACY-OPERATIONS-BASELINE.md`, not enforced live.

### ISI-28 server preparation update — 2026-10-05

The earlier SSH blocker is resolved. Fresh protected database backup and isolated
restore PASS; original schema and counts of 90 tables matched. One 42-byte
storage object passed logical archive/byte recovery. Signed accepted RC was
transferred and its image verified against the archive's exact config/rootfs
and OCI manifest mapping. Migration preflight on an isolated restored database
PASS: 0013 -> 0034, 90 -> 140 tables, original table counts not decreased.
Full local regression after the wording correction: 1,123 passed, 43 existing
skips, zero failures/errors. Policy and diff checks PASS. Production DB/services
remain unchanged. See `docs/ops/ISI-28-CONTROLLED-DEPLOYMENT-PLAN.md`.
SMTP is owner-deferred **To Be Defined**; no external delivery is verified.
Central ISI Nginx noindex/robots guard remains until final portal publication.
Final source acceptance, legal facts, operational backup/monitoring and actual
cutover/server acceptance remain open; ISI-28 is still IN_PROGRESS.

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


## ISI-29A local runtime candidate — 2026-10-07

Graphical SIMPA coefficients/CI and ORDO forecast/backtest read models, scoped integrations and extended ten-field Help are present; new Help actions PARTIAL. Existing tables and domain contracts preserved. Responsive and keyboard checks use synthetic local evidence only. Final exact-candidate gates/report: `automation/evidence/ISI-29A/`. No commit/push, hosted checkpoint or server action. Subsequent 29B–F runtime is not implemented.


29A local verification record: IMPLEMENTED / REVIEW_VERIFIED candidate; 23 focused and 1203 regression passes, 43 existing native-lane skips, zero failures/errors. Four responsive widths and keyboard backtest selection verified on synthetic local preview. Exact report/fingerprint: `automation/evidence/ISI-29A/human-review.json`. No CI_VERIFIED or server deployment of 29A. 29B–F remain unimplemented; 29B read-only preparation recorded separately.


## ISI-29A approved main checkpoint and 29B continuation — 2026-10-07

Owner approved exact 29A candidate f220dd3dce9b172c05dc6982167f73b2cd848924b0060d48b1da4143970e492a; committed/pushed main `cad6892fd2d710b8263b936c06bb3d8137cdeddc` and direct remote equality verified with clean worktree. This supersedes mutable 29A unstaged/approval-pending wording; predecessor candidate/CI records remain LEGITIMATE_HISTORY. 29A NOT CI_VERIFIED; latest hosted acceptance #96 remains exact predecessor 374dda3. No CI/server action.

29B scoped geometry/storage/API/domain-adapter candidate is IN_PROGRESS. Contract automation/specs/ISI-29B-GIS-CONTRACTS.md; core_spatial_geometry_versions / migration0035; generic immutable geometry provenance and shared storage, separate SIMPA/ORDO adapters. WGS84 explicit lon/lat only; unknown/projected CRS and invalid topology rejected; no reprojection/provider/geocoder/tiles/PostGIS/indicator or AI changes. One geometry per version, human lifecycle, scoped permissions, immutable fingerprint and content hash. Actual approved boundary dataset absent; synthetic software tests only. Shapely2.1.2 added with existing NumPy preserved; no other lock versions upgraded. Help docs/help/ISI-SPATIAL-DATA-GUIDE.md covers source import/review, with GIS user interface still 29C. Native upgrade/downgrade, regression/dependency/independent review are gates, not yet claimed PASS in this record. 29C–F remain unimplemented. No new staging/commit/push or server mutation authorized by prior29A approval.


29B final candidate: scoped geometry API/storage/native0035 migration and separate SIMPA/ORDO identity adapters implemented locally. Initial39 focused/native1/regression gates PASS; final synchronized candidate requires repeated exact gates and independent/human review. Help ten-item guide present, new action matrix PARTIAL. Next29C map/table workflows; 29C–F not implemented. Institutional boundary data/licence not supplied; projected CRS rejected. No CI/server verification, no deployment or staging/commit/push of29B.


29B local verification closeout: IMPLEMENTED / REVIEW_VERIFIED unstaged candidate; 42 focused and 1 native PostgreSQL test passed in the pre-final-review cycle (full migration upgrade/downgrade/reupgrade, constraints and stale concurrent write rejection), 1246 regression passes / 43 existing native-lane skips, zero failures/errors. Independent analyzer repeat PASS; runtime dependency audit and fixed musllinux wheel/local import checks PASS. Exact final candidate identity is automation/evidence/ISI-29B/human-review.json, with complete repeated gates on this documentation-synchronized candidate required. This supersedes mutable 29B IN_PROGRESS/verification-pending notes above; previous candidate narratives are LEGITIMATE_HISTORY. No CI/server acceptance or staging/commit/push; institutional geometry dataset/licence and projected CRS remain explicit missing/unsupported states. 29C–F still not implemented.

Final bounded review correction: reject non-string geometry type as a controlled validation failure; require native fixture loopback host before any DB access. Full exact-candidate gates must pass again; final counts/identity in automation/evidence/ISI-29B/human-review.json supersede prior cycle counts. No test gate bypass.


## ISI-29B approved main and ISI-29C implementation — 2026-10-07

29B approved exact candidate1c5a531c6ba7e206a1d822e295d70b2e3377257fc06873872d6c07210331f418 committed/pushed main0d59f40aa03ab7115041f1c58052d4610aac3a54; all28 committed file hashes match approval, clean single main worktree/direct remote equality. Final29B43 focused/native1/regression1247 passes,43 predecessor native skips; NOT CI_VERIFIED, no new server verification. Latest hosted acceptance#96 remains predecessor374dda3. This supersedes mutable29B approval-pending notes; earlier candidate gates/history remain LEGITIMATE_HISTORY.

Owner now explicitly approves all planned verified29A-F commits/pushes; repeated per-candidate commit approval is no longer required. Exact deterministic gates, independent readonly analysis and assistant review remain mandatory.29F acceptance/deployment authorization is subject to usage pre/post, exact committed main CI, signed image/bundle and approved ISI-28 server contract. Shared edge non-target protection remains mandatory. SMTP pending/new backups owner-deferred.

29C locked candidate: automation/specs/ISI-29C-GIS-WORKFLOWS.md. Existing Data surface now includes shared GIS catalogue/import/review/date/layer/version/map/table/selected provenance and explicit geometry export. Existing ORDO spatial-unit identity lifecycle exposed; actual ORDO overview permission source fixed, stable resource code input added. Separate domain selectors; no new navigation/schema/formula/provider/model. Geometry date is not observation period. ORDO exact identity-only stored result viewer revalidates source/methodology/boundary/trace/arithmetic; no result-to-geography association exists for SIMPA, displayed unavailable. No institutional boundary source/licence auto-created.

Actual browser WebGL limitation rejected the Pydeck draft renderer (REMOVE_BEFORE_NEXT_SLICE). Final renderer uses existing Streamlit1.63 components.v2 with fixed code/data-only SVG DOM; no new dependencies/lock/install. Bounded25features/50000coordinates/1MB; render-only Mercator with exact source coordinates retained; safe textContent labels, selection/pan/zoom/keyboard controls and table fallback, no tiles/provider keys/user markup. Local focused/full/browser/independent gates required before IMPLEMENTED/REVIEW_VERIFIED closeout; evidence automation/evidence/ISI-29C.29D-F remain unimplemented. DEFERRED_SERVER_VERIFICATION.


## ISI-29C local verification closeout — 2026-10-07

IMPLEMENTED local candidate:37 focused tests and1283 regression tests pass,44 existing native-lane skips, zero failures/errors; lint/policy/mypy/pip/diff gates PASS. Synthetic desktop1280/mobile390 browser checks PASS: map click/Enter/Space, linked selected table/provenance, ORDO result table/chart, zoom/reset, no page overflow or external assets. Exact synchronized candidate requires matching acceptance/browser/independent-analysis/human-review reports under automation/evidence/ISI-29C before approved staging. First unfinished runtime package29D;29E/F planned. Standing owner approval covers verified commit/push. No new CI/server acceptance; DEFERRED_SERVER_VERIFICATION, no full-production claim. Historical pending notes above are LEGITIMATE_HISTORY superseded by this closeout.


## ISI-29C approved main / ISI-29D attribution candidate — 2026-10-08

29C accepted main a77f9f0b4e43038554ee203a0c5ad22cd0b9e981, exact26-file candidate025263734c8ff82ef85c01f01a229e8724ea22ed6b13cfffb312426bacf7f82d; repeated local7gate/independent twice/assistant review PASS.37 focused/1283 regression passes,44 existing native-lane skips; main/origin/direct equality and clean one-worktree checkpoint recorded. No hosted/server verification inherited. Mutable prior29C candidate/current-next text superseded (LEGITIMATE_HISTORY).

29D IN_PROGRESS locked automation/specs/ISI-29D-MODEL-ATTRIBUTION.md: additive0036 simpa_attribution_artifacts, exact interventional continuous OLS explanation from stored coefficients and revalidated complete-case training cohort. No refitting/dependency/provider/model-family change. Domain-owned source/result/contract/background/artifact hashes and immutable metadata; read revalidates source/methodology and stored metric/prediction parity. Scoped analysis.read, explicit analysis.run creation, fingerprint-only audit. Existing SIMPA result expander gains matrix/heatmap/global mean-absolute/local waterfall and ten-item Help docs/help/ISI-SHAP-GUIDE.md. Technical1e-8 tolerance is not institutional threshold.512 selected rows/24features bounded; original training cohort only, correlated features limitations visible. ORDO naive/seasonal SHAP remains unsupported; conditional new model execution not automatically selected. NOT CI_VERIFIED; server deferred to29F. Local/native/full/browser/independent/human exact gates required before phase closeout. Browser access restored on 2026-10-08; synthetic desktop1280/mobile390 visual/keyboard/viewer/unsupported/tamper gates passed, with screenshots under automation/evidence/ISI-29D/. Contradictory legacy non-SHAP caption corrected only in the new attribution panel. Native0036 test participates in the existing hosted native lane without skips. Final local gates/independent review are rerun on the exact updated candidate before authorized commit/push.29E/F unimplemented; current owner explicitly requests checkpoint/deployment of verified current source in preproduction-testing mode, separate from29F whole-plan completion.
