# ISI-30A — workflow shell and design system

Owner authorization 2026-10-10: finish customer workflows, improve the GUI, then
continue implementation. GoraNova dual-product test account email supplied;
SMTP remains pending. Credentials are owner-entered, never task artifacts.

## Baseline and bootstrap

Canonical single main/worktree f587ed0a194043cadf7190ceae9f6f29c1d76c55;
clean index/tree, empty stash, origin and direct GitHub equality checked.
Exact required acceptance37914718258 completed/success, all12 jobs independently
queried. Recorded29F signed release/server acceptance/schema0037 is scoped to
PREPRODUCTION_TESTING; no fresh server verification in30A.

DONE:29A-F software release, linked reports, illustrated Help and reviewed Word.
PARTIAL: full customer reachability and populated-action Help/screens.
MISSING: dedicated reachable Scenarios entry, data-governance authoring UI,
some methodology/reference/model lifecycle forms, separate GoraNova account.
DRIFT: active ledgers/inventory still show29F pending/schema0036.

Legacy classification: stale active governance REMOVE_BEFORE_NEXT_SLICE (resolve here);
SIMPA/ORDO phase/future captions REMOVE_IN_NAMED_PHASE(ISI-30C); Scenarios dead-end and scope-retained
forms REMOVE_IN_NAMED_PHASE(ISI-30A); missing governed authoring controls
REMOVE_IN_NAMED_PHASE(ISI-30B); methodology/model reachability
REMOVE_IN_NAMED_PHASE(ISI-30C); deeper AI/admin flow and recovery presentation
REMOVE_IN_NAMED_PHASE(ISI-30D); populated Help/manual coverage
REMOVE_IN_NAMED_PHASE(ISI-30E). Historical checkpoints LEGITIMATE_HISTORY;
legacy read-only results, route markers, staging/signed-release machinery
REQUIRED_COMPATIBILITY. No branches/worktrees/stash or auto full-CI triggers.

## Exact first mutable package

Existing Streamlit shell, shared CSS, pure presentation/session helper, existing
ORDO scenario workflow extraction reused in analytics and new Scenarios entry.
No backend authorization change, model/schema/dependency or formula change.
SIMPA has no scenario implementation: suppress unsupported menu entry in the
presentation; retained backend navigation payload is compatibility only.
ORDO Scenarios uses existing analysis.read/run guards and source eligibility.
Existing forecast and AI panels remain in Analytics. Expose existing scenario status and assessment review endpoints through bounded forms with explicit human confirmation; backend contracts and permissions unchanged. Clear non-auth widget data
on organization/product/workspace switches; clear entire app state on logout or
expired session; refreshing access re-fetches backend context. Escape all new
HTML labels. Context band, useful empty/error states, legible typography,
consistent controls, visible keyboard focus and mobile sidebar control.

Allowed files: this spec; docs/roadmap/ISI-30-WORKFLOWS-AND-GUI-PLAN.md;
MasterPlan; TECHNICAL_DOCUMENTATION.md; automation/STATUS.md; automation/tasks.json;
src/streamlit_app/{app.py,workflow_shell.py,ordo_analytics_workspace.py,ordo_analytics_api.py};
src/streamlit_app/assets/app-shell.css; docs/help/ISI-WORKFLOW-SHELL-GUIDE.md;
docs/help/ISI-HELP-COVERAGE-MATRIX.md; tests/test_isi_30a_workflow_shell.py;
tools/qa/{run_isi30a.py,analyze_isi30a.py}.

Bounded regression recovery: tests/test_isi_23d_help_xai_contract.py and
tests/test_isi_24d_help_xai_contract.py replace helper-location source-string
coupling with executable two-product menu isolation assertions; existing route
and Help assertions retained. tests/test_isi_27a_shared_help_contract.py supplies
the new pure helper/Path dependencies to its extracted-function AppTest fixture.
These obsolete fixture assumptions are REMOVE_BEFORE_NEXT_SLICE, resolved here;
no permission/security test removed, skipped or weakened. Existing Help labels
are preserved for compatibility and prior user workflows.

Canonical system inventory impact: INV-A06/A07/A13/A21 and INV-B02/M04,
existing presentation only; backend/domain/RBAC authority unchanged.

## Gates

Focused executable AppTest and pure transition/escaping/navigation tests;
predecessor shell/ORDO/security tests; full regression; Ruff/policy/mypy/pip/diff;
desktop1280/mobile390 browser screenshots and keyboard/sidebar/overflow checks.
Runner pins exact allowed-file hashes; independent analyzer read-only verifies
XML/log hashes, actual browser evidence and same candidate. Human diff review.
Evidence automation/evidence/ISI-30A/. No stage/commit/push/checkpoint/deployment
until new exact-candidate approval; prior standing approval covered29A-F only.
Not full production; institutional validation, capacity, alert routing, legal
facts, real MFA, owner-deferred SMTP/new backups retain their existing gates.
