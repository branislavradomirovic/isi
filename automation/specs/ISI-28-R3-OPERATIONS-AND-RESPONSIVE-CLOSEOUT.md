# ISI-28 R3 — bounded operations and responsive closeout

Baseline: main 1bf0552d702c0e6cefc659b38184f505118f11d1, exact required
acceptance #95 / 37503549452 completed success in all 12 jobs. Owner authorized
production data transition, placeholder legal publication and operational
controls; SMTP remains pending. R2 activation, coordinated recovery checkpoint,
production database/bucket and four accepted runtimes passed. The first activation
rolled back because a helper tried to inspect removed old ISI containers; recovery
corrected that check and proved non-ISI identities unchanged. Preserve failed history.
Live acceptance passed login/context for SIMPA-only, ORDO-only and dual access,
readiness, both real RQ workers and storage readback. Full production acceptance remains open. Owner now explicitly defers all new
backups and requests application/server testing in pre-production mode. No offsite
input is required for this narrowed test scope; production acceptance is not claimed.

## Reconciliation / legacy

DONE: source alignment, #95, signed image, new production data targets, legal
publication, RQ and role-context probes. PARTIAL: operational enforcement and AI.
MISSING for full production only: offsite recovery and monitored alert/duty-holder operation. Owner defers backup activation while preproduction testing proceeds.
DRIFT: desktop 1280 header clips Open platform and shrinks product wordmarks.
Classify historical deployment scripts and stale staging status as
REMOVE_IN_NAMED_PHASE(ISI-28); first attempt evidence as LEGITIMATE_HISTORY;
precutover fixtures/old DB/bucket as REQUIRED_COMPATIBILITY for rollback.
No domain/provider/champion promotion or shared edge mutation is authorized here.

## Locked mutable surface

Add tools/server/isi28_operations.py and dedicated tests for server-only,
release-bound READ-ONLY monitoring and a namespaced monitoring-cron helper.
Only fixed ISI containers, protected runtime configuration, API/UI/queue/dependency
status, disk capacity and existing ISI certificate are in scope. No stop/start,
backup, purge, outbound alerts or other product changes. Refuse image/config drift
and require explicit preproduction-testing/backups_disabled lock. Preserve any
existing crontab entries; no timer is claimed from local code/tests.

Repair public header geometry only: use existing accessible collapsed navigation
through 1380px, keep product links from shrinking, bound menu height with scrolling.
Synchronize keyboard/resize navigation behavior with the same breakpoint. Validate
SR/EN legal pages at desktop/mobile, including all link bounds and menu operation.
No redesign, new content, domain semantics, dependency or schema change.

Update MasterPlan inventory/as-built reference, status/task ledgers, deployment
plan and privacy/legal checklists to confirmed server results and pending gates.
Add deterministic runner and independent read-only analyzer. Candidate stays
unstaged until full gates, independent review and owner exact approval. New
runtime source requires separate exact-SHA manual hosted checkpoint before deploy.
Ops monitoring activation/cron is not claimed from local unit tests; backups are excluded.

Canonical system inventory impact: INV-J01/J03/J06-J09 production target state;
INV-J13/J15 verified existing ingress; INV-J14 availability unresolved; INV-K02
production DB; INV-K SMTP explicit pending; INV-J34/INV-M13 add read-only server monitoring authority; INV-B15/INV-E02/INV-K07 add optional ISI request thread configuration;
INV-A01 legal publication/header behavior; INV-A02/A04/A05 pending recovery presentation. Existing owners/boundaries preserved.

## Observed ISI-only AI execution correction

Default embedding probes timed out at 120 and 300 seconds. A bounded synthetic
request with options.num_thread=2 succeeded in 0.33s with 768 dimensions, without
restarting the shared service. Extend exact surface only to src/core/config.py,
src/platform/ai/providers.py, gateway.py and dedicated tests: optional validated
AI_OLLAMA_NUM_THREAD (1..64; unset retains old payload) propagated to ISI-only
completion and both embedding endpoint payloads. Production candidate uses 2.
This is provider resource configuration, not model/prompt/methodology promotion;
no shared host configuration or other product is changed. Update AI configuration
inventory ownership in the same candidate. Native application-provider execution
is still a post-acceptance deployment gate; the direct bounded probe is insufficient.
Historical test freezing 980px is updated to 1380px with equivalent assertions.

## Owner steering — 6 October 2026

Owner: "ne treba za sada nikakve rezervne kopije da se prave jer tek treba da se
testira aplikacija i server u pre-production modu". This supersedes R3 backup
scheduling/creation scope. No new backups, offsite copies or purge are executed.
Existing rollback/recovery media remain intact. New data targets retain their
observed names; runtime security profile remains production so explicit SMTP
pending stays fail-closed. Operational acceptance is PREPRODUCTION_TESTING, not
full production. No shared Nginx or public publication reversal is authorized.
Only bounded provider execution/header fix/read-only monitoring and testing
continue. SMTP remains pending. Production capacity/real methodology, staffed
alerts and disaster recovery are not asserted by this test release.

Deterministic runner: tools/qa/run_isi28_r3.py. Independent read-only analyzer: tools/qa/analyze_isi28_r3.py. All twenty candidate files stay unstaged pending exact approval.

## SMTP-pending presentation drift

Live recovery panel still offered send buttons without explaining pending email.
Add only src/streamlit_app/app.py and dedicated UI tests: clear unavailable notice,
disabled recovery sends and guard against forced UI submissions in pending mode.
Keep login and existing token confirmations unchanged. Existing auth isolation and
API503 contracts remain authoritative. This completes already accepted R2 pending
email presentation; no SMTP/provider/credential activation. Candidate now twenty
files; local runner/analyzer include this surface.
