# ISI Autonomous Industrialization Status

This is the human-facing live execution ledger. The MasterPlan is the canonical roadmap/architecture/governance authority; `automation/tasks.json`, accepted code, exact-main GitHub Actions and recorded evidence provide synchronized execution proof.

Last status update: 2026-10-04.

## Current execution

Last accepted implementation slice: `ISI-27C - Reproducible Release & Supply-Chain Assurance` on main `b6f0bfaf453360da72f866d4bbd1d47b51655bf4` (`NOT CI_VERIFIED`), tree `8d52631012121c078d077a39d75e201d4ffadcbd`, candidate fingerprint `7dc381dd31d94e6ada447c7cffc945399bddbe4a7ec138ec88ae69e77e9be8ea`.

Separate owner-approved public portal audit remediation `ISI-PUBLIC-PORTAL-AUDIT-REMEDIATION-R1` is accepted on main `c177f9d705efd6f68d95ef7d13847b03a8e19229`, with local acceptance and review PASS, NOT CI_VERIFIED and NOT SERVER_VERIFIED. It fixes the icon-only document catalog, English knowledge routes/visible Serbian fallback and the mobile Documents hero. Existing favicon, robots, sitemap, manifest, metadata, 404, accessibility and responsive contracts were checked; desktop and 390px mobile preview passed. No production deployment of this remediation has occurred. Earlier unstaged/no-push wording is superseded accepted history. Evidence: `automation/evidence/ISI-PUBLIC-PORTAL-AUDIT-REMEDIATION-R1/acceptance.json`.

`ISI-PUBLIC-LEGAL-NOTICES-DRAFT-R1` produced internal SR-Latn Terms and Privacy drafts with EN working translations and an owner/legal publication checklist. They are explicitly not publishable until the legal entity, controller/processor roles, processing purposes and bases, cookies, providers/transfers, retention, rights contacts, content licensing, and legal terms are confirmed. The public portal currently has no Terms/Privacy page or footer links. No live page, database, deployment, or production configuration changed. The exact current public site was read-only checked on 2026-10-04; it still shows the document-index claim and existing public content.

Deployment request is recorded, but the release dependency remains **27A ACCEPTED ON MAIN / 27B ACCEPTED ON MAIN / 27C ACCEPTED ON MAIN → 27D exact-main hosted acceptance → ISI-28 deferred**. The owner explicitly authorized final implementation and local/GitHub/server alignment; 27C is accepted on main after local review. The 27D `release-candidate` workflow still requires a fresh usage precheck and explicit checkpoint approval. The pre-ISI-28 runbook is historical/superseded, and no current-server audit or mutation has been performed.

ISI-26 - Performance, Load & Resilience Engineering is `IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED`. ISI-27 B0-R1A corrected read-only bootstrap is CLOSED/PASS on baseline `e46128752e29f46dc6d9b8510198739f88da50e9`; current phase is `ISI-27 - Industrial Release Candidate & Acceptance Pack` with **27A ACCEPTED ON MAIN / 27B ACCEPTED ON MAIN / 27C ACCEPTED ON MAIN / 27D SPEC_READY / NOT CI_VERIFIED**. Current checkpoint: `ISI-27D - Exact-Main RC Acceptance & Phase Closeout`.

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

Overall `ISI-26-PERFORMANCE-LOAD-RESILIENCE` is `IMPLEMENTATION COMPLETE / ACCEPTED ON MAIN / NOT CI_VERIFIED`. `PRODUCTION_CAPACITY_VERIFIED=false`, `SERVER_VERIFIED=false`, and `GITHUB_ACTIONS_DISPATCH=NO` remain binding. ISI-27 B0-R1A bootstrap is CLOSED/PASS, the ISI-27 scope is locked, and ISI-27A is accepted on main and 27D is current; the current next action is `ISI-27D - Exact-Main RC Acceptance & Phase Closeout`. ISI-28 remains the exclusive authority for live server/DNS/certificate/central-ingress/SMTP/production-secret/data/server-Ollama mutation. Krcuga and OralScanXAI remain strict non-targets.

## ISI-27 scope lock

Corrected B0-R1A authority: DONE=6, PARTIAL=8, MISSING=5, DRIFT=0; 13 release blockers are not DONE. The corrected Help/XAI blocker set contains 12 shared production-critical surfaces. SBOM/signed provenance/attestation is MISSING, while image vulnerability enforcement is also MISSING.

Execution is deliberately grouped into four larger formal gates: **27A Shared Help & Release UX Completeness -> 27B RC Evidence & Governance Pack -> 27C Reproducible Release & Supply-Chain Assurance -> 27D Exact-Main RC Acceptance & Phase Closeout**. 27D is owner-controlled and owns the single explicit hosted release-candidate acceptance cycle. No hosted CI is authorized by scope lock itself.

Current next action: execute the locked ISI-27C reproducible-release contract from accepted ISI-27B main. Server/live-host work remains frozen through ISI-27 and belongs exclusively to ISI-28. Krcuga and OralScanXAI remain strict non-targets.

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
| 27 | Industrial Release Candidate & Acceptance Pack | **IN PROGRESS / 27A ACCEPTED ON MAIN / 27B ACCEPTED ON MAIN / 27C ACCEPTED ON MAIN / 27D SPEC_READY / NOT CI_VERIFIED** |
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
Current checkpoint: `ISI-27D - Exact-Main RC Acceptance & Phase Closeout`.

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
