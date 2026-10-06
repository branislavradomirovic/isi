# ISI-28 R2 — production activation with explicitly pending email

Status: IN_PROGRESS. Baseline: main 3986a03182eed04ba8055a6156d6722bca1504f5,
exact required acceptance checkpoint 94 passed; protected image verified.
Owner explicitly authorizes production database/storage transition, publication
of SR/EN legal notices with visible placeholders, operational policy preparation
and completion of remaining production checks. SMTP remains pending indefinitely.
This supersedes R1's missing-fact publication gate only for transparently marked
placeholders; unknown facts must never become asserted legal identities.

DONE: exact-SHA CI, signed image, isolated schema rehearsal, approved ISI ingress.
PARTIAL: backups, runtime configuration, legal content and operational controls.
MISSING: final cutover, live application acceptance, operational enforcement.
DRIFT: R1 legal publication blockers and old checkpoint references are legitimate
history superseded by this owner instruction. Test SMTP/staging runtime remains
REMOVE_IN_NAMED_PHASE(ISI-28), never production delivery evidence.

## Exact source surfaces

Implement explicit AUTH_DELIVERY_MODE=pending: no delivery, no tokens generated
by mail-request endpoints, account-independent HTTP 503 before database work.
Preserve login, existing tokens and SMTP adapter behavior. Production validates
pending mode only with no configured SMTP host/sender/credentials; staging and
normal SMTP retain existing contracts. Record email-dependent capability as
DEFERRED, not verified. Mutable files: deployment/runtime.py, auth/delivery.py,
api/auth_routes.py and dedicated tests. Security validator still rejects null.

Add a narrowly scoped legal publication tool and versioned SR/EN content payload
under tools/ and data/public/. Existing legal PublicPage lifecycle/renderer owns
publication. Tool uses an explicit approval digest, checks routes/ownership and
all translations before changes, and refuses conflicting existing content.
Public text distinguishes known facts, placeholders, policy targets and verified
controls; no invented hosting/legal basis/personnel or retrospective effective date.

Update privacy ops baseline, legal checklist, MasterPlan, technical reference and
task/status ledgers to actual evidence. Add ISI-only ops scripts and tests only
under a follow-on exact contract after backup/storage/retention boundary review.
No automatic full CI, credentials, new dependencies or schema changes.

## Activation gates

Local targeted/full regression, independent read-only analysis and exact owner
candidate approval before staging. Separate manual exact-SHA hosted checkpoint
and usage checks before signing new image. No unaccepted source reaches server.
Cutover uses fresh coordinated checkpoint under ISI-only write boundary, restores
a new database/copies private bucket without removing old targets, compares data,
and changes all four ISI runtimes together. Never mutate non-target products.
Do not make additional central ingress changes without exact owner confirmation.

Operational roles are assigned to role titles; staffing/contacts remain explicit
unknowns until confirmed. Offsite destination cannot be invented. Controls not
actually operating retain pending labels and block their acceptance claim.

Canonical system inventory impact: INV-A01 legal publications; authentication
configuration/delivery rows gain explicit pending state; INV-J/INV-K/INV-L remain
owners of recovery/runtime/operational controls. Preserve all domain boundaries.
Help/XAI impact: explain temporarily unavailable email workflows; no analytics,
methodology, scoring or AI policy change. Required tests cover disabled requests,
no database/token/SMTP effects, unchanged SMTP and fail-closed configuration,
legal collision/idempotency/locales/footer/sitemap and desktop/mobile acceptance.

## First exact source candidate / deterministic gate

Publisher: tools/publish_isi_legal_notices.py; content: data/public/legal_notices.json.
Tests: tests/test_isi_28_pending_email.py and tests/test_isi_28_legal_publication.py.
Runner: tools/qa/run_isi28_r2.py. Independent read-only analyzer:
tools/qa/analyze_isi28_r2.py. This candidate implements pending email and legal
publication capability/policy targets; it does not claim completed server data
cutover, backup scheduling, model readiness or duty-holder staffing. Subsequent
server controls remain part of R2 under separately locked exact actions.
