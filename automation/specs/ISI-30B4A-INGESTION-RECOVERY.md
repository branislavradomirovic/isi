# ISI-30B4A — controlled ingestion recovery

Baseline6a70f4619b81a9c6e6a38f3ba50c40da69612d05, canonical clean main/origin,
one worktree/empty stash.30A/B1/B2/B3 locally reviewed committed; last hosted/server
proof f587ed0. Owner30B–F approval covers verified commit/push/checkpoint/deployment.

MasterPlan-first bootstrap and actual schemas/routes/ingestion_run_service and
ingestion_operations_service inspected. DONE existing governed authoring;
PARTIAL customer operations; MISSING backfill/replay/dead-letter forms and explicit
observed timestamp. Historic baseline runners LEGITIMATE_HISTORY; original retry
REQUIRED_COMPATIBILITY; absent privacy/quarantine controls REMOVE_IN_NAMED_PHASE(30B4B).
No incompatible unclassified legacy within this slice. Data recovery is a customer
operator action with existing data.upload/governance permissions; worker dispatch,
arbitrary connector commands and filesystem operations remain operator-internal.

Exact mutable surface: this spec; src/streamlit_app/data_operations_api.py;
data_operations_workspace.py; data_source_workspace.py; data_ingestion_workspace.py;
tests/test_isi_30b4a_operations.py; tools/qa/run_isi30b4a.py;
tools/qa/analyze_isi30b4a.py; MasterPlan; TECHNICAL_DOCUMENTATION.md; automation/STATUS.md; automation/tasks.json;
docs/help/ISI-INGESTION-RECOVERY-GUIDE.md; docs/help/ISI-HELP-COVERAGE-MATRIX.md.
Inventory impact INV-A08/A21 customer recovery UI; backend/schema/domain boundaries unchanged.

Typed existing requests only. Explicit UTC-offset timestamp, empty means unknown
and does not manufacture freshness. Backfill requires full active binding chain
and allowed policy; file16MB, author cursors/key/observation, confirmed. Replay
uses selected immutable pinned run and its policy, terminal state only, explicit
new key; backend rechecks policy/content/live runs/idempotency. Dead-letter list
metadata only; OPEN requeue/resolve with confirmation, key or note. DISCARDED is
a retained disposition, not deletion. Existing permission checks remain server
authority. Refresh clears stale operational selection/drafts. No raw credentials,
domain conclusions, new dependency, schema, model or server mutation.

Focused validation/path/scope/timestamp/RBAC/confirmation/refresh tests, full local
7 gates, independent exact manifest analyzer and human review,1280/390 synthetic
browser evidence before commit.30B4B privacy/record governance,30C–F remain pending.
