# ISI-28 R1 — Controlled production upgrade

Status: **IN_PROGRESS — READ-ONLY SERVER RECONCILIATION**.
Baseline signed/CI-verified RC: `2b1f2ef20a2310df23947f2ac2128d16f81a98ea`, run #93.
Authority: MasterPlan, ADR-0026 and owner instructions to deploy the final
platform and continue to full production. Preserve the one canonical main
worktree; never execute historical ISI-15/16 deployment scripts.

## Locked first slice

Read-only audit of the existing target `ubuntu@94.230.189.146:222` (historical
connection identity to verify with existing SSH trust), `/home/ubuntu/ISI`,
central-ingress-nginx-1 and ISI-owned containers, volumes/networks and release
metadata. Read only allowlisted non-secret configuration facts. Do not print
environment files, credentials, raw logs, request bodies or institutional data.
Capture paths/digests, schema revision, counts and health rather than content.
Record aggregate disk/memory/CPU capacity and backup metadata, then construct
the concrete mutation/rollback plan from those observations. No service stop,
recreation, migration, backup deletion, DNS/SMTP/model change in this first slice.

## Production prerequisites

1. Confirm current source/image and central Nginx :8445 upstream configuration.
2. Confirm ISI isolation and health baselines for Krcuga :8443/OralScanXAI :8444.
3. Identify backup coverage/retention and validate a new restore-capable backup
   within ISI-owned protected server storage before any migration.
4. Resolve configuration/schema/image compatibility, rootless image volume
   permissions, worker queues, SMTP, storage and model/provider policies.
5. Finalize SR/EN Terms/Privacy with confirmed legal entities, roles, hosting,
   cookies, retention and contact; publish via existing CMS process.
6. Validate any source candidate locally, commit under owner authorization,
   manually accept the final exact main SHA and sign its immutable artifacts.
7. Deploy only those artifacts. Run migration preflight and controlled migration;
   update ISI services, keeping other products unchanged.
8. Verify health/readiness, auth/RBAC/tenant/product boundaries, API/UI, workers,
   AI policy, SMTP and data integrity; desktop/mobile portal and legal/SEO routes.
9. Record source/image/config identities, operational checks and actual rollback
   readiness. Only observed server acceptance earns SERVER_VERIFIED.

The approved direction includes policy drafting, source fixes and controlled
deployment; it does not supply missing factual legal identities or authorize
unreviewed changes to SIMPA/ORDO methodology, shared products, or production
secret disclosure. Unknown factual prerequisites block their dependent action.

Canonical system inventory impact: NONE for this initial read-only slice.
Potential deployment/public/legal changes must reconcile INV-J/INV-K/INV-L and
public-surface rows with actual changes before final source acceptance.
Help/XAI impact: NONE for read-only reconciliation.
Evidence: ignored `automation/evidence/ISI-28/` (sanitized JSON only).

## Parallel local slice — published legal page discovery

Owner-authorized Terms/Privacy implementation can prepare portal integration
while SSH/legal identity facts are pending. Exact mutable runtime surface:
`src/public/content_service.py`, `src/public/routes.py`,
`src/public/readiness_routes.py`, `src/public/templates/partials/footer.html`,
`src/public/templates/page.html` (localized legal-page eyebrow),
`src/public/static/css/approved-design.css`, and
`tests/test_isi_28_public_legal_links.py`. Add no legal facts or CMS records yet.
Use the existing `legal` PublicPage type, existing published/draft/archived
lifecycle, localized route renderer and metadata. Footer/sitemap expose only
published legal pages in the requested locale; no cross-language silent fallback,
draft exposure or new private API/schema boundary. Existing footer Help remains.

Canonical inventory impact: INV-A01 public website gains published legal-page
footer/sitemap discovery; it does not claim that legal content is finalized or
published. Update that row and the controlled technical reference in the same
candidate. Help/XAI impact: NONE — no analytical output, authentication action,
permission or private workflow changes; public link labels are self-describing.
Test published/draft/archived/missing translations, existing localized canonical
and alternate metadata, public routes/sitemap and preserved auth/robots behavior.
Visual desktop/mobile verification remains required when final legal content is
available. No source candidate is deployment-qualified by the older #93 run.

## Parallel policy preparation

The owner authorized proposing and preparing the missing policies. Exact
additional document surface: `docs/ops/ISI-28-PRIVACY-OPERATIONS-BASELINE.md`
and `docs/legal/ISI-LEGAL-NOTICES-RELEASE-CHECKLIST.md`. Define concrete
retention/rights/incident/backup targets and evidence needed to activate them.
Keep proposed periods distinct from verified live behavior and preserve scoped
retention/legal-hold/purge approvals. Record already-confirmed identity/contact
facts so they are not requested again. Do not fabricate operator legal identity,
registered address, hosting location, agreements, DPO status or live enforcement.

The existing Terms/Privacy draft headers record the already confirmed Institute
name, operator brand and privacy mailbox. Their factual release blockers remain;
no legal CMS record or effective-date publication is created by this candidate.

## Observed execution boundary — 5 October 2026

The owner reconfirmed the historical SSH target/socket. Authentication failed
with the existing agent and selected public key; no remote command executed.
Live public routes are available, but robots disallows all indexing and legal
footer links are absent. These are ISI-28 production prerequisites, not evidence
of deployed source identity. Local synthetic SR/EN desktop/mobile legal layouts
were inspected without horizontal overflow. The full regression found one
MasterPlan current-checkpoint wording failure; the wording was corrected and
the affected contract plus legal tests passed (14 tests). Candidate remains
unstaged; exact-main acceptance and server verification are still required.

## Authorized next slice — protected backup and isolated restore

Owner renewed continuation to full production after SSH access was fixed.
Observed server main is `bf4a648b1e118a0b087b437579d2f3f12ef2db94`,
schema `20260828_0013`; API/UI and workers have different image identities.
Central ingress and ISI aliases match ADR-0026. SMTP uses test-only Mailpit;
no ISI backup timer was found and existing backups are August rehearsals.
Classify old backups as LEGITIMATE_HISTORY and mixed runtime/config/test SMTP
as REMOVE_IN_NAMED_PHASE(ISI-28). SSH blocker is resolved.

Before migrations or service replacement, create a fresh exclusive mode-0700
directory under `/home/ubuntu/ISI/backups/isi28-*`, with mode-0600 PostgreSQL
custom dump and checksum metadata. Keep production media on the server.
Restore the dump into a new ISI-28-owned PostgreSQL 17 container with no network
and no published ports, bounded memory/CPU and temporary database storage.
Compare schema revision and aggregate table row counts with the consistent
dump source snapshot; never print payloads. Remove only this newly created
restore container after recording success/failure. No production DB restore,
service recreation, write freeze, queue deletion or shared-ingress mutation.
This database-only checkpoint does not establish object backup consistency,
offsite recovery, encryption, scheduled RPO or complete deployment readiness.
Inventory impact: NONE for this transient verification slice; existing INV-J
recovery ownership applies. Preserve all existing backups and production data.

Extend the same protected checkpoint with an application-bucket logical object
archive read through the existing API container's S3 client. Keep object names
and bytes only on the server. Compare the bucket key/ETag/size inventory before
and after archive creation, reject changes, verify archive payload hashes by
extracting into a fresh mode-0700 directory under the checkpoint. Never restore
to the live bucket. This verifies logical byte recovery, not MinIO service
recovery or a transactionally coordinated database/object recovery point.

## Accepted-image migration preflight

Transfer the already signed checkpoint-93 bundle to a new exclusive protected
server directory, verify every digest and its OpenSSH signature against copied
repository-pinned public trust, then load only that image. Do not rebuild it.
Verify loaded image/config identity and OCI source revision. Rehearse migrations
on a new restore of the checkpoint dump in an ISI-28-only internal Docker
network, with no published ports and bounded CPU/memory. Allow only the new
PostgreSQL and accepted migration containers to attach. Record old/new schema
heads and preservation of original table counts. Cleanup only resources created
by this rehearsal; retain the image, bundle and backup for later verification.
No production schema change, checkout update or service replacement is allowed
by this preflight. A new source candidate will require its own accepted bundle.

## Preparation closeout and source candidate review

Owner deferred real SMTP as To Be Defined; keep external email workflows
DEFERRED rather than claim capture is successful delivery. SSH is resolved;
database/object recovery and accepted-image migration preflight passed. The
server containerd OCI manifest and hosted config digest were cryptographically
mapped to the same signed archive/config/rootfs/platform without payload changes.
The operational plan is `docs/ops/ISI-28-CONTROLLED-DEPLOYMENT-PLAN.md`.
Public Nginx noindex/robots guard remains until final publication conditions.

Complete local candidate surface consists of the previously listed six public
runtime files and legal-link test, the three legal draft/checklist documents,
the two ISI-28 ops documents, this contract, ISI-27D acceptance closeout,
MasterPlan, technical reference, STATUS and task registry. No schema, domain,
private API, dependency, image-build or CI workflow changes are included.
Full regression: 1,123 passes/43 existing skips/zero failures. Read-only
independent candidate analysis and exact owner approval precede source staging.
No new source SHA inherits checkpoint-93 acceptance or authorizes cutover.
