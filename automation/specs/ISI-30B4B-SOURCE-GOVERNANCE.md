# ISI-30B4B — source governance and record adjudication

Baseline15204d72532215667fed86f3213a78746cbfc540 canonical main/origin, clean
one worktree/index/stash.30B4A reviewed committed/pushed;33focused/1543regression
PASS/46 inherited skips. Latest CI/server f587ed0. Owner30B–F approval retained.
MasterPlan/inventory/governance catalogs/schemas/source update/record service and
actual API read/write permissions inspected before scope lock. DONE governed
pipeline and recovery; MISSING customer profile/record adjudication; privacy
retention/anonymization/export/purge REMOVE_IN_NAMED_PHASE(30B4C). Old candidate
ledgers/runners LEGITIMATE_HISTORY; base read/retry REQUIRED_COMPATIBILITY.

Mutable: this spec; src/streamlit_app/data_governance_api.py;
data_governance_workspace.py; data_source_workspace.py; tests/test_isi_30b4b_governance.py;
tools/qa/{run_isi30b4b.py,analyze_isi30b4b.py}; MasterPlan;
src/platform/data/schemas.py; src/platform/data/record_governance_service.py;
TECHNICAL_DOCUMENTATION.md; automation/STATUS.md; automation/tasks.json;
docs/help/{ISI-SOURCE-GOVERNANCE-GUIDE.md,ISI-HELP-COVERAGE-MATRIX.md}.
Canonical inventory impact INV-A08/A21, existing profile/record presentation only.

Explicit profile load, typed classification/privacy/purpose/owner/steward/retention/
AI/export/state/rationale form, current revision pinned and confirmation required.
Use existing enums/current values; do not manufacture institutional decisions.
Only changed fields sent; optional verified anonymization proof ID; backend checks
scope/active membership/policy/downgrade proof/required metadata/CAS. No weakening.
Read-only data.read can view profile/policies, never quarantine. Quarantine list,
detail and resolution require data.governance.manage, exact source/scope, explicit
detail load before human decision, reference and confirmation; backend remains
identity/conflict acceptance authority. Display normalized selected/current records
as field/value tables, not an arbitrary JSON editor. Refresh changes draft generation
and clears stale approvals/detail; switching source/product/workspace scopes forms.

Audit correction before gates: current record can change between reviewer read and
resolution. Add optional expected_current_accepted_record_id to existing request;
new UI always pins ID or explicit null. Backend compares under the existing lock
before mutation, returning existing state-conflict error on drift. Omitted field
preserves historical caller compatibility. No database schema/migration needed.
Inventory impact INV-A08 and data governance API contract; no permission expansion.
No dependency/AI/production mutation. Existing domain semantics remain unchanged.
Focused payload/scope/revision/permission/confirmation/stale-refresh/record tests,
7local gates, exact read-only analyzer/human review,1280/390 synthetic browser checks.
Illustrated action Help/Word30E and release30F remain pending, no CI/server inheritance.
