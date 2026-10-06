# ISI-28 observed-state deployment plan

Status: R2 DATA/RUNTIME ACTIVATION PASS; R3 OPERATIONAL CLOSEOUT IN_PROGRESS.
The observed baseline and initial ordered gates below are retained historical
recovery evidence; the dated activation record at the end supersedes current state.
Owner authorized continuation through full production and restored SSH access on
5 October 2026. Target: ubuntu@94.230.189.146:222, ISI :8445 only.

## Observed baseline

- Server repository main: bf4a648b1e118a0b087b437579d2f3f12ef2db94, clean,
  one worktree. Local/GitHub accepted RC: 2b1f2ef20a2310df23947f2ac2128d16f81a98ea.
- API/UI image: sha256:2f841bbb9882a5a4a1ba027f9b28e2db5e610b6e4815412ffa22940a3ca1989c.
- Worker image: sha256:cfa57311e026421e1ba13b53e993595b82e57eda446ec9f7d22d07814e1265b6.
- PostgreSQL 17, schema 20260828_0013; 90 public tables; about 14.4 MB.
- ISI volumes and isi_internal/isi_ingress are independent; aliases match
  ADR-0026. Central Nginx is healthy and already routes to the correct aliases.
- Current API/UI include runtime/docker-compose.test-access.yml override;
  do not carry this historical test override into the final deployment blindly.
- SMTP is Mailpit:1025 without external authentication. This is test capture,
  not external delivery of invitations, verification or password recovery.
- Effective settings: production environment, staging deployment profile;
  workers retain older public/application URLs. Reconcile all four runtimes.
- Host Ollama has qwen2.5:7b-instruct, gemma3:4b and qwen2.5vl:3b. Configured
  nomic-embed-text is absent; embedding-dependent workflows are not verified.
- 16 CPUs, about 62.8 GB RAM, 103 GB free root disk. Aggregate availability
  does not establish production capacity or calibrated SLOs.
- Existing August backups are historical rehearsals; no ISI backup timer found.

## Completed recovery prerequisites

Protected checkpoint /home/ubuntu/ISI/backups/isi28-db-20261005T204927Z:
PostgreSQL custom dump restored into a fresh network-none container, original
schema and all table counts matched. Source counts were stable before/after
backup; this is not a cross-service transactional snapshot. Container removed.
Application bucket contained one 42-byte object; archive and isolated filesystem
restore hashes matched, with stable key/ETag/size inventory. Media and names
remain on the server. Sanitized evidence is in automation/evidence/ISI-28/.
Offsite backup, encryption, scheduled retention/RPO and full MinIO service
recovery remain unverified. Do not infer them from these successful rehearsals.

## Ordered remaining gates

1. Verify transferred accepted bundle, signature, source/image identity and
   rehearse migrations against another isolated restore of the old database.
2. Owner deferred SMTP as **To Be Defined** on 5 October 2026. Record this
   exception and keep external email-dependent workflows explicitly deferred.
   Do not treat Mailpit capture as delivered email. Later enable the actual
   provider/secure server-side credentials and verify delivery to an
   owner-controlled recipient with explicit send authorization.
3. Confirm operator registered facts and processing map, then finalize legal
   content through existing published CMS lifecycle. Proposed retention targets
   must be distinguished from enforced operations.
4. Reconcile deployment profile, all app/worker URLs, host allowlist, queue
   transport, local-only AI policy and required provider/model capabilities.
   Do not fabricate model promotion or methodology validation.
5. Complete final local candidate review/independent gates, owner-authorized
   exact-file commit/push and final exact-SHA manually approved acceptance with
   Actions usage checks. Sign the resulting immutable bundle. Earlier accepted
   RC may be used for preflight but cannot qualify new source changes.
6. Record non-target Krcuga/OralScanXAI baseline and preserve shared ingress
   configuration digest. Prefer no central ingress mutation when aliases work.
7. Establish maintenance/write boundary, fresh coordinated database/object
   backup, protected runtime-config rollback copy and immutable prior image
   retention; verify isolated restore before production migration.
8. Migrate production only after successful isolated rehearsal and all gates;
   replace only ISI API/UI/data-worker/ai-worker with the final accepted image.
   Preserve PostgreSQL/Redis/MinIO volumes and product/tenant boundaries.
9. Verify API/UI health, authenticated roles and tenant/product isolation,
   jobs/queues, approved local AI, SMTP, storage/data integrity, public legal
   and SEO routes and desktop/mobile workflows. Compare non-target health.
10. Record accepted source SHA, image ID, effective safe configuration and schema;
    prove local/GitHub/server identity. Update canonical documents to observed
    results. Only this final acceptance earns SERVER_VERIFIED.

## Rollback boundary

Before production changes retain current source/archive, both prior runtime
image IDs and protected configuration. App rollback alone is permitted only
when migration backward compatibility is proven. Otherwise restore the verified
coordinated database/object checkpoint during the recorded maintenance boundary
and restart all four ISI runtimes with matching prior configuration. Never
restore production data into unrelated products or delete shared volumes.
Current preliminary checkpoint alone is not complete cutover rollback readiness.

Accepted-image isolated migration rehearsal passed: 20260828_0013 to
20260918_0034, 90 to 140 tables, no original table counts decreased. The
initial engine-ID lookup failed because Docker containerd reports an OCI
manifest ID rather than the accepted hosted config ID. Cryptographic archive
manifest/config checks plus exact loaded config, rootfs and platform comparisons
resolved the mapping; no signed payload was changed. Retain both identities.
External noindex behavior is confirmed to originate in the ISI central-Nginx
block, including the inline robots response and X-Robots-Tag header.

## Legacy classification and inventory

August recovery media: LEGITIMATE_HISTORY. Historical deployment scripts:
REMOVE_IN_NAMED_PHASE(ISI-28), never execute. Mixed images, test SMTP, staging
profile and test override: REMOVE_IN_NAMED_PHASE(ISI-28). Missing embedding
capability: REMOVE_IN_NAMED_PHASE(ISI-28); inspect approved model/eval authority
before resolving. SSH blocker: resolved. Earlier public robots observation is
historical until fresh external/internal responses are reconciled.
Canonical system inventory impact: NONE for this read-only/transient preparation;
existing deployment, recovery, provider and public rows retain ownership.

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
