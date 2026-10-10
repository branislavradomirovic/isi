# ISI-30B2 governed ingestion authoring contract

Baseline main be2ae69 after30B1 verified12-file commit/push; exact local24focused,
1456regression/46 inherited skips and1280/390 browser/action checks. Clean single
worktree/index/stash. Last hosted/server proof f587ed0; no inherited CI/server.
MasterPlan architecture and actual22A–E schemas/services/routes inspected: connector
registration is transport-neutral, ingestion uses supplied files not remote fetch.
Typed schema/mapping, record policy and operational policy activation are existing
APIs guarded by data.governance.manage. Normal ingest requires data.upload and
active exact connector/mapping/record/operational bindings. No new semantics.

DONE30A/30B1 local review; PARTIAL data platform customer reachability; MISSING
these typed forms. Empty registry placeholder REMOVE_IN_NAMED_PHASE(30B3);
future method/admin captions30C/D; Word30E. Old exact candidate runners and
baseline history LEGITIMATE_HISTORY, old read compatibility REQUIRED_COMPATIBILITY.
No alternate branches/worktrees/dependencies/schema/provider/domain changes.

Mutable files: this spec; data_ingestion_api.py; data_ingestion_workspace.py;
data_source_workspace.py; tests/test_isi_30b2_ingestion_workflows.py; tests/test_isi_30b_data_workflows.py (supply empty contract API to predecessor synthetic fixture, retain all assertions);
tools/qa/run_isi30b2.py and analyze_isi30b2.py; MasterPlan; technical; status;
Help coverage; docs/help/ISI-GOVERNED-INGESTION-GUIDE.md.
Inventory impact INV-A08/A21, existing UI boundaries only.

Authoring uses fixed upload-batch connector profile (existing tested
inbound/batch transport), no secrets/configuration/URL editor or network retrieval.
Field grid restricted to existing enums; source ordinal deterministic row order,
MAP/IGNORE explicit, missing tokens newline separated, preserve missing semantics.
Record policy selects identity keys from pinned MAP fields. Operational policy
thresholds are explicitly author-entered, never institutional defaults. All
activation and writes need checkbox confirmation. Normal ingest only active
matching chain and required explicit idempotency key; resubmission same key/content
safe per existing API; ambiguous dispatch refresh guidance. Source/context/form
keys isolate drafts; upstream immutable contract IDs key downstream drafts, so activation invalidates stale authoring values. Scope always taken from active shell, payload validated with
existing Pydantic contracts. Error messages omit submitted data validation values.
Operational backfill/replay/DLQ/quarantine/privacy dedicated later30B slices.

Focused payload validation/RBAC/scope/pinned chain/confirmation/empty/error/AppTest,
full regression/lint/policy/mypy/pip/diff; exact manifest/read-only analyzer/human
review; browser1280/390 including authoring/activation/ingestion before commit.
Owner already authorizes verified commits and final30F acceptance/deployment.
No hosted CI/server here. Full30B/HelpWord30E/full production not yet complete.
