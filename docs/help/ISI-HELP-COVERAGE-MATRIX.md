# ISI Help Coverage Matrix

Status: CANONICAL CROSS-PRODUCT HELP/XAI COVERAGE ARTIFACT

This matrix implements MasterPlan 0.5A. It inventories every customer-facing USER SURFACE row (INV-A01 through INV-A21) and records honest coverage. ISI-23D verifies SIMPA-owned surfaces and ISI-24D verifies ORDO-owned surfaces; neither falsely promotes shared surfaces owned by later phases.

Coverage vocabulary: MISSING, PARTIAL, COMPLETE, VERIFIED. Only VERIFIED satisfies production completeness for an owned production-critical action. Checklist-level NOT_APPLICABLE must be explicitly justified; none is used to hide missing owned SIMPA content.

| Inventory | Surface | Coverage | Roadmap owner | Canonical Help / evidence |
| --- | --- | --- | --- | --- |
| INV-A01 | Public website | VERIFIED | FOUNDATION / ISI-27 | ISI-H01; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_public_help_contract.py. |
| INV-A02 | Login | VERIFIED | ISI-20 / ISI-27 | ISI-H02; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py. |
| INV-A03 | Invitation onboarding | VERIFIED | ISI-13 / ISI-20 | ISI-H03; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py. |
| INV-A04 | Email verification | VERIFIED | ISI-20 | ISI-H04; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py. |
| INV-A05 | Password reset | VERIFIED | ISI-20 | ISI-H05; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py. |
| INV-A06 | Authenticated app shell | VERIFIED | FOUNDATION / ISI-23 / ISI-24 | ISI-H06; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; tests/test_isi_27a_shared_help_contract.py. |
| INV-A07 | Overview workspace | MISSING | FOUNDATION | Shared overview Help remains open. |
| INV-A08 | Data workspace | VERIFIED | ISI-22 | ISI-H07; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; tests/test_isi_27a_shared_help_contract.py. |
| INV-A09 | AI workspace | VERIFIED | ISI-25 | Shared registry/evaluation/promotion/fallback/circuit/drift/XAI actions are covered by docs/help/ISI-AI-USER-GUIDE.md and tests/test_isi_25b_monitoring_xai_help.py; non-AI shared Help remains separately owned. |
| INV-A10 | SIMPA indicators | VERIFIED | ISI-23 | SIMPA-H02/H03/H04 plus SIMPA User Guide; tests/test_isi_23d_help_xai_contract.py. |
| INV-A11 | SIMPA analytics | VERIFIED | ISI-23 | SIMPA-H05 through H12 plus deterministic statistical XAI; ISI-23D tests. |
| INV-A12 | ORDO indicators | VERIFIED | ISI-24 | ORDO-H01 through H06 plus ORDO User Guide; tests/test_isi_24d_help_xai_contract.py. |
| INV-A13 | ORDO analytics and scenarios | VERIFIED | ISI-24 | ORDO-H05 through H11, governed time-series-spec lifecycle, series discovery, explicit forecast execution, persisted-result presentation and deterministic forecast/scenario XAI; ISI-24D/24E tests. |
| INV-A14 | Reporting workspace | VERIFIED | ISI-27 | ISI-H08; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; tests/test_isi_27a_shared_help_contract.py. |
| INV-A15 | Administration workspace | VERIFIED | ISI-20 / ISI-27 | ISI-H09; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; tests/test_isi_27a_shared_help_contract.py. |
| INV-A16 | Account security workspace | VERIFIED | ISI-20 | ISI-H10; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; tests/test_isi_27a_shared_help_contract.py. |
| INV-A17 | Public self-registration | VERIFIED | ISI-20 | ISI-H11; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py. Runtime NOT_PRESENT; invitation-only; public signup absence tested. |
| INV-A18 | SIMPA Help, User Guide and XAI interpretation | VERIFIED | ISI-23 / ISI-25 / ISI-27 | SIMPA domain Help/statistical XAI plus ISI-25 shared AI evaluation/provenance/promotion/fallback interpretation are verified; remaining global release Help remains ISI-27. |
| INV-A19 | ORDO Help, User Guide and XAI interpretation | VERIFIED | ISI-24 / ISI-25 / ISI-27 | ORDO forecast/scenario Help/XAI plus ISI-25 shared AI evaluation/provenance/promotion/fallback interpretation are verified; remaining global release Help remains ISI-27. |
| INV-A20 | Commercial checkout/payment surface | MISSING | OUT_OF_SCOPE | Surface is NOT_PRESENT; no ISI commercial payment architecture exists. |
| INV-A21 | Cross-product Help Coverage Matrix | VERIFIED | ISI-23 / ISI-24 / ISI-25 / ISI-27 | ISI-H12; src/streamlit_app/shared_help_workspace.py; docs/help/ISI-SHARED-USER-GUIDE.md; tests/test_isi_27a_shared_help_contract.py. All production-critical USER SURFACE rows VERIFIED as Help coverage; A17 absence explicitly tested. |


## ISI-25B shared AI material actions

Every action below satisfies the MasterPlan ten-point checklist through `docs/help/ISI-AI-USER-GUIDE.md`.

| Inventory | Material user action | Coverage | Test/evidence authority |
| --- | --- | --- | --- |
| INV-A09 | Register/inspect governed model capability identity | VERIFIED | tests/test_isi_25b_monitoring_xai_help.py |
| INV-A09 | Register/inspect frozen promotion benchmark and thresholds | VERIFIED | tests/test_isi_25b_promotion.py; tests/test_isi_25b_monitoring_xai_help.py |
| INV-A09 | Execute/interpret deterministic evaluation and final review | VERIFIED | tests/test_isi_25b_evaluation_engines.py |
| INV-A09 | Preview/execute explicit promotion and rollback | VERIFIED | tests/test_isi_25b_promotion.py |
| INV-A09 | Interpret fallback review-required, circuit and drift states | VERIFIED | tests/test_isi_25b_capability_runtime.py; tests/test_isi_25b_monitoring_xai_help.py |
| INV-A18/INV-A19 | Interpret shared AI provenance/XAI and unsupported states | VERIFIED | tests/test_isi_25b_monitoring_xai_help.py |
| INV-A21 | Open/use ISI shared AI User Guide | VERIFIED for ISI-25 ownership | tests/test_isi_25b_monitoring_xai_help.py |

## ISI-23D SIMPA material actions

Every action below satisfies the ten-point MasterPlan checklist through the matching in-app SIMPA topic and `docs/help/SIMPA-USER-GUIDE.md`.

| Inventory | Material user action | In-app topic | Coverage | Test/evidence authority |
| --- | --- | --- | --- | --- |
| INV-A10 | Select SIMPA workspace/access context | SIMPA-H01 | VERIFIED | tests/test_isi_23d_help_xai_contract.py |
| INV-A10 | Configure/read local-system profile and actors | SIMPA-H02 | VERIFIED | tests/test_isi_23d_help_xai_contract.py |
| INV-A10 | Create/read monitoring cycles | SIMPA-H03 | VERIFIED | tests/test_isi_23d_help_xai_contract.py |
| INV-A10 | Read/filter indicator registry and observations | SIMPA-H04 | VERIFIED | tests/test_isi_23d_help_xai_contract.py |
| INV-A11 | Select/review eligible governed analytical artifact | SIMPA-H05 | VERIFIED | tests/test_isi_23d_help_xai_contract.py |
| INV-A11 | Interpret methodology lifecycle | SIMPA-H06 | VERIFIED | tests/test_isi_23d_help_xai_contract.py |
| INV-A11 | Interpret reference suite/case PASS evidence | SIMPA-H07 | VERIFIED | tests/test_isi_23d_help_xai_contract.py |
| INV-A11 | Create/review monitoring snapshot | SIMPA-H08 | VERIFIED | tests/test_isi_23d_help_xai_contract.py |
| INV-A11 | Review statistical contract lifecycle/specification | SIMPA-H09 | VERIFIED | tests/test_isi_23d_help_xai_contract.py |
| INV-A11 | Run deterministic statistical model | SIMPA-H10 | VERIFIED | tests/test_isi_23d_statistical_xai.py |
| INV-A11 | Interpret OLS/Poisson/Binomial/Fractional result and XAI | SIMPA-H11 | VERIFIED | tests/test_isi_23d_statistical_xai.py |
| INV-A11 | Run/review bounded local AI synthesis | SIMPA-H12 | VERIFIED | tests/test_isi_23d_help_xai_contract.py |
| INV-A18 | Open/use SIMPA Help/User Guide | SIMPA-H01..H12 | VERIFIED | tests/test_isi_23d_help_xai_contract.py |

## ISI-24D/24E ORDO material actions

Every action below satisfies the ten-point MasterPlan checklist through the matching in-app ORDO topic and `docs/help/ORDO-USER-GUIDE.md`.

| Inventory | Material user action | In-app topic | Coverage | Test/evidence authority |
| --- | --- | --- | --- | --- |
| INV-A12 | Select ORDO workspace/access context | ORDO-H01 | VERIFIED | tests/test_isi_24d_help_xai_contract.py |
| INV-A12 | Configure/read destination profile, resources and stakeholders | ORDO-H02 | VERIFIED | tests/test_isi_24d_help_xai_contract.py |
| INV-A12 | Create/read monitoring cycles | ORDO-H03 | VERIFIED | tests/test_isi_24d_help_xai_contract.py |
| INV-A12 | Read/filter indicator registry, observations and methodology state | ORDO-H04 | VERIFIED | tests/test_isi_24d_help_xai_contract.py |
| INV-A13 | Select/review governed analytical artifact and evidence quality | ORDO-H05 | VERIFIED | tests/test_isi_24d_help_xai_contract.py |
| INV-A13 | Author/review time-series specification and perform status-aware human lifecycle | ORDO-H06 | VERIFIED | tests/test_isi_24d_help_xai_contract.py; tests/test_isi_24e_forecast_workflow_api.py; tests/test_isi_24e_forecast_workflow_ui.py |
| INV-A13 | Create/review analytical snapshot and provenance | ORDO-H07 | VERIFIED | tests/test_isi_24d_help_xai_contract.py |
| INV-A13 | Create/review development goals and scenarios | ORDO-H08 | VERIFIED | tests/test_isi_24d_help_xai_contract.py |
| INV-A13 | Create/interpret evidence-only scenario assessment | ORDO-H09 | VERIFIED | tests/test_isi_24d_forecast_xai.py |
| INV-A13 | Discover eligible series identity, explicitly execute from a VALIDATED spec and review persisted ESTIMATED/NOT_ESTIMATED results | ORDO-H10 | VERIFIED | tests/test_isi_24d_forecast_xai.py; tests/test_isi_24e_forecast_workflow_api.py; tests/test_isi_24e_forecast_workflow_ui.py |
| INV-A13 | Run/review bounded local ORDO AI synthesis | ORDO-H11 | VERIFIED | tests/test_isi_24d_help_xai_contract.py |
| INV-A19 | Open/use ORDO Help/User Guide | ORDO-H01..H12 | VERIFIED | tests/test_isi_24d_help_xai_contract.py; tests/test_isi_24e_forecast_workflow_ui.py |

## Hard boundaries

- ISI-27A supplies independent shared Help/test authority for the twelve corrected blockers. A07 stays MISSING and non-production-critical; A20 stays OUT_OF_SCOPE/NOT_PRESENT and non-production-critical. This is not a claim that ISI-27 is ready or CI/server verified.
- Unsupported XAI is shown as unavailable, never invented.
- No Help text creates a formula, LISI weight, threshold, citizen risk label, eligibility rule, causal claim, forecast or policy conclusion.
- Server verification/deployment remains deferred to owner-approved ISI-28.

## ISI-27A shared material actions

All ten checklist fields are supplied by the matching canonical shared topic and
`docs/help/ISI-SHARED-USER-GUIDE.md`. Public/auth topics require no tenant data.
VERIFIED records focused local Help/UX evidence, not overall runner acceptance or
CI_VERIFIED. The top-level table is the coverage authority; later material-action
rows never overwrite it. Protected domain/AI guide references to earlier global
PARTIAL coverage are LEGITIMATE_HISTORY, not current cross-product coverage.

| Inventory | Material user action | In-app topic | Coverage | Test/evidence authority |
| --- | --- | --- | --- | --- |
| INV-A01 | Javni sajt | ISI-H01 | VERIFIED | tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_public_help_contract.py |
| INV-A02 | Prijava | ISI-H02 | VERIFIED | tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py |
| INV-A03 | Prihvatanje poziva | ISI-H03 | VERIFIED | tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py |
| INV-A04 | Potvrda emaila | ISI-H04 | VERIFIED | tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py |
| INV-A05 | Oporavak lozinke | ISI-H05 | VERIFIED | tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py |
| INV-A06 | Organizacija, platforma i workspace | ISI-H06 | VERIFIED | tests/test_isi_27a_shared_help_contract.py; src/streamlit_app/shared_help_workspace.py |
| INV-A08 | Podaci i poreklo | ISI-H07 | VERIFIED | tests/test_isi_27a_shared_help_contract.py; src/streamlit_app/shared_help_workspace.py |
| INV-A14 | Izveštaji, pregled i izvoz | ISI-H08 | VERIFIED | tests/test_isi_27a_shared_help_contract.py; src/streamlit_app/shared_help_workspace.py |
| INV-A15 | Administracija | ISI-H09 | VERIFIED | tests/test_isi_27a_shared_help_contract.py; src/streamlit_app/shared_help_workspace.py |
| INV-A16 | Bezbednost naloga | ISI-H10 | VERIFIED | tests/test_isi_27a_shared_help_contract.py; src/streamlit_app/shared_help_workspace.py |
| INV-A17 | Pristup samo po pozivu | ISI-H11 | VERIFIED | tests/test_isi_27a_shared_help_contract.py; tests/test_isi_27a_auth_ux_contract.py |
| INV-A21 | Kako koristiti zajedničku Pomoć | ISI-H12 | VERIFIED | tests/test_isi_27a_shared_help_contract.py; src/streamlit_app/shared_help_workspace.py |

For INV-A17, signup fields, execution results and model XAI are NOT_APPLICABLE
because public signup is NOT_PRESENT; institutional onboarding remains invitation-only.
Shared Help does not compute model outputs: numerical XAI is NOT_APPLICABLE here;
domain/AI XAI remains owned by its accepted guides. ISI-H07 covers upload/catalog,
analytical/feature inspection, lineage and eligibility; API-only governance is
explicitly identified. H08 covers version/review/publication/export; H09 covers
members/access/roles/invitations/workspaces/organization/audit; H10 covers password
assurance and self-session revocation. No additional runtime capabilities are implied.

Candidate acceptance evidence belongs under
`automation/evidence/ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS/`.
The independent runner and review gates remain required before IMPLEMENTED/REVIEW_VERIFIED.


## ISI-29A new graphical actions (separate from accepted predecessor coverage)

| Action | Surface | Help | State | Evidence authority |
| --- | --- | --- | --- | --- |
| SIMPA-29A-COEFFICIENT-CHART | INV-A11 / INV-A22 | SIMPA-H11; SIMPA-USER-GUIDE.md 29A | PARTIAL | tests/test_isi_29a_xai_charts.py; tests/test_isi_29a_xai_help_contract.py; local visual/full gates pending |
| ORDO-29A-FORECAST-CHART | INV-A13 / INV-A22 | ORDO-H10; ORDO-USER-GUIDE.md 29A | PARTIAL | tests/test_isi_29a_xai_charts.py; tests/test_isi_29a_xai_ui_contract.py; local visual/full gates pending |
| ORDO-29A-ORIGIN-SELECT | INV-A13 / INV-A22 | ORDO-H10; ORDO-USER-GUIDE.md 29A | PARTIAL | tests/test_isi_29a_xai_ui_contract.py; local keyboard/full gates pending |

All ten mandatory Help fields for these actions extend the existing SIMPA-H11/ORDO-H10 topics. Predecessor VERIFIED rows retain accepted scope. New actions are PARTIAL pending exact-candidate acceptance; SHAP/GIS remain outside 29A.


## ISI-29B source geometry API actions — local candidate

| Action | Coverage | Authority | Evidence |
| --- | --- | --- | --- |
| ISI-29B-GEOMETRY-REGISTER | PARTIAL | docs/help/ISI-SPATIAL-DATA-GUIDE.md sections1–10 | tests/test_isi_29b_geometry_contract.py; tests/test_isi_29b_spatial_api.py |
| ISI-29B-GEOMETRY-REVIEW | PARTIAL | docs/help/ISI-SPATIAL-DATA-GUIDE.md sections1–10 | tests/test_isi_29b_spatial_registry.py; tests/test_isi_29b_native_postgres.py |
| ISI-29B-GEOMETRY-READ | PARTIAL | docs/help/ISI-SPATIAL-DATA-GUIDE.md sections1–10 | tests/test_isi_29b_spatial_api.py |

These rows extend INV-B29/C45/A22 action inventory without promoting GIS frontend, institutional boundary correctness, SHAP or extraction. Existing VERIFIED rows retain accepted scope. Full ten-item checklist present; local/native/exact-review and later hosted release evidence required before production completeness.


ISI-29C GIS user actions: PARTIAL until exact release/server evidence. Podaci→GIS source import/review, ORDO identity authoring/review, map/table/date/layer/version/keyboard selection, linked revalidated ORDO result and explicit geometry export: docs/help/ISI-SPATIAL-DATA-GUIDE.md; src/streamlit_app/spatial_workspace.py; tests/test_isi_29c_spatial_api.py, test_isi_29c_spatial_view.py, test_isi_29c_spatial_ui.py and test_isi_29c_ordo_link.py. Existing VERIFIED historical topics remain scope-bound.29F Word/browser live screenshots pending; institutional boundary source missing and SIMPA numeric geography binding unavailable.


### ISI-29D accepted preproduction attribution

| Customer action | Coverage | Guide | Authority |
|---|---|---|---|
| SIMPA stored OLS result → create/read SHAP | PARTIAL | docs/help/ISI-SHAP-GUIDE.md (ten items) | tests/test_isi_29d_*; accepted95fec435 exact12CI and recorded preproduction server checks |
| SIMPA sample×feature matrix/heatmap/global ranking/local waterfall | PARTIAL | docs/help/ISI-SHAP-GUIDE.md | source invalidation/additivity/coalition reference/UI parity;29F release/server required |
| ORDO unsupported attribution | PARTIAL | docs/help/ISI-SHAP-GUIDE.md | existing naive/seasonal explanation retained; no invented SHAP |


### ISI-29E locally verified extraction candidate

| Customer action | Coverage | Guide | Authority |
|---|---|---|---|
| SIMPA/ORDO governed TXT/snapshot → local queued extraction; cancel pending | PARTIAL | docs/help/ISI-EXTRACTION-GUIDE.md (ten items) | tests/test_isi_29e_*; ai.run + data.read; explicit scoped load; exact candidate gates required |
| Source quotes, spans/cells, versions, limitations and proposed identity | PARTIAL | docs/help/ISI-EXTRACTION-GUIDE.md | data.read; source invalidation/tenant/product isolation; original SR/EN preserved |
| Final human accept/reject, resolve identity, separately dated claim territory | PARTIAL | docs/help/ISI-EXTRACTION-GUIDE.md | data.validate; attestation/immutable review/current identity + geometry checks; not truth/methodology certification |
| Accepted-only exact period/geometry retrieval | PARTIAL | docs/help/ISI-EXTRACTION-GUIDE.md | no unverified/rejected/stale claims;29F report/manual/release pending |

29E local coverage is verified only with matching exact-candidate acceptance/browser/review evidence. Release/server/Word coverage remains PARTIAL until29F; no institutional extraction accuracy certification.

## ISI 29F linked report extension

INV-A14/A22 actions: explicit accepted claim selection, human result association,
source/dated territory/map/XAI preview, draft/version, review/publish and current
revalidated export. Coverage COMPLETE in docs/help/ISI-LINKED-REPORTS-GUIDE.md
and src/streamlit_app/linked_reporting_workspace.py;10 checklist items. VERIFIED
only after matching final focused/browser/manual acceptance under ISI-29F.
Legacy shared/domain Help coverage remains accepted for its earlier scope.
No unsupported confidence, ORDO SHAP, domain truth or production quality claim.

## Owner-requested illustrated Help — 2026-10-09

Existing36 canonical shared/SIMPA/ORDO topics gain numbered workflows, documented field tables, dated baseline availability and37 reviewed local screenshots. Product Help includes detailed GIS, extraction and linked-report chapters; SIMPA also includes supported SHAP. Ten-item canonical text remains intact; public six-topic allowlist remains independent of authentication. Images do not read live tenant data and have exact checksums, provenance/date and synthetic/baseline captions. Authority: docs/help/ISI-ILLUSTRATED-MANUAL.json, src/streamlit_app/help_manual.py and tests/test_isi_29f_illustrated_help.py. COMPLETE content candidate; VERIFICATION requires matching final29F gates/browser/manual/review. Existing historical21-row matrix is predecessor evidence, not a claim that illustrated Help was previously shipped.
# ISI-30A action-level extension — local candidate

Historical VERIFIED rows below refer to their accepted phase scope. The new
shell/scenario GUI has not inherited screenshot/manual or server verification.

|Action|Status|Help|Test/evidence|
|---|---|---|---|
|Organization/product/workspace switch, refresh access, logout|PARTIAL|ISI-WORKFLOW-SHELL-GUIDE.md|test_isi_30a_workflow_shell.py; browser/mobile pending|
|Dedicated ORDO scenarios entry, existing goal/scenario/assessment creation|PARTIAL|ISI-WORKFLOW-SHELL-GUIDE.md|test_isi_30a_workflow_shell.py; browser/populated screenshots pending|
|Existing scenario status and assessment human review|PARTIAL|ISI-WORKFLOW-SHELL-GUIDE.md|test_isi_30a_workflow_shell.py; API contracts unchanged; browser pending|
|SIMPA scenario menu absence|PARTIAL|ISI-WORKFLOW-SHELL-GUIDE.md|Product navigation test; no SIMPA scenario contract created|


### ISI-30B1 action coverage (candidate)

|Action|Help|Status|Remaining|
|---|---|---|---|
|Source/version quality inspection|ISI-DATA-WORKFLOWS-GUIDE.md|PARTIAL|Exact browser/screens/Word30E|
|New existing-source version|ISI-DATA-WORKFLOWS-GUIDE.md|PARTIAL|Browser action/Word30E|
|Run/job/evaluation/governed-output inspection|ISI-DATA-WORKFLOWS-GUIDE.md|PARTIAL|Browser action/Word30E|
|Confirmed fresh FAILED retry|ISI-DATA-WORKFLOWS-GUIDE.md|PARTIAL|Browser action/Word30E|


### ISI-30B2 candidate action coverage

|Action|Help|Status|Remaining|
|---|---|---|---|
|Connector registration/activation|ISI-GOVERNED-INGESTION-GUIDE.md|PARTIAL|Browser/Word30E|
|Typed field mapping registration/activation|ISI-GOVERNED-INGESTION-GUIDE.md|PARTIAL|Browser/Word30E|
|Identity policy registration/activation|ISI-GOVERNED-INGESTION-GUIDE.md|PARTIAL|Browser/Word30E|
|Operational policy registration/activation|ISI-GOVERNED-INGESTION-GUIDE.md|PARTIAL|Browser/Word30E|
|Active-chain idempotent governed upload|ISI-GOVERNED-INGESTION-GUIDE.md|PARTIAL|Browser/Word30E|


### ISI-30B3 analytical authoring candidate

|Action|Help|Status|Remaining|
|---|---|---|---|
|Dataset/feature registry creation|ISI-ANALYTICAL-AUTHORING-GUIDE.md|PARTIAL|Browser/Word30E|
|Typed field contract/activation|ISI-ANALYTICAL-AUTHORING-GUIDE.md|PARTIAL|Browser/Word30E|
|Governed-output snapshot creation|ISI-ANALYTICAL-AUTHORING-GUIDE.md|PARTIAL|Browser/Word30E|
|Eligible snapshot feature-version creation|ISI-ANALYTICAL-AUTHORING-GUIDE.md|PARTIAL|Browser/Word30E|
|Revision-pinned snapshot/feature lifecycle|ISI-ANALYTICAL-AUTHORING-GUIDE.md|PARTIAL|Browser/Word30E|


### ISI-30B4A controlled recovery candidate

|Action|Help|Status|Remaining|
|---|---|---|---|
|Offset-aware observed timestamp|ISI-INGESTION-RECOVERY-GUIDE.md|PARTIAL|Illustrated Word30E|
|Policy-bound backfill / replay|ISI-INGESTION-RECOVERY-GUIDE.md|PARTIAL|Browser/Word30E|
|Dead-letter requeue / reviewed disposition|ISI-INGESTION-RECOVERY-GUIDE.md|PARTIAL|Browser/Word30E|


### ISI-30B4B source governance candidate

|Action|Help|Status|Remaining|
|---|---|---|---|
|Revision-pinned source classification/privacy/AI/export profile|ISI-SOURCE-GOVERNANCE-GUIDE.md|PARTIAL|Browser/Word30E|
|Governance-only quarantine detail/record comparison|ISI-SOURCE-GOVERNANCE-GUIDE.md|PARTIAL|Browser/Word30E|
|Human record decision pins reviewed current accepted record|ISI-SOURCE-GOVERNANCE-GUIDE.md|PARTIAL|Browser/Word30E|


### ISI-30B4C privacy candidate

|Action|Help|Status|Remaining|
|---|---|---|---|
|Retention policy registration / revision-pinned hold|ISI-PRIVACY-CONTROLS-GUIDE.md|PARTIAL|Browser/Word30E|
|External-output anonymization evidence proposal / human review|ISI-PRIVACY-CONTROLS-GUIDE.md|PARTIAL|Browser/Word30E|
|Purpose-confirmed allowed version export|ISI-PRIVACY-CONTROLS-GUIDE.md|PARTIAL|Browser/Word30E; real sensitive MFA pending|
|Purge request and retention metadata|ISI-PRIVACY-CONTROLS-GUIDE.md|PARTIAL|Operator approval/execution; archive not verified|


## 30C1 SIMPA authoring — PARTIAL

Existing direct_observation DRAFT/propose/reference-suite/run/human validate/retire and four statistical semantic-family contract/lifecycle forms: docs/help/SIMPA-METHODOLOGY-WORKFLOWS-GUIDE.md. Ten-item action Help added; local/browser evidence and illustrated Word parity remain required. No invented institutional approval; global registry and supersession disclosed.


## 30C2A ORDO authoring — PARTIAL

Existing global direct_observation method DRAFT/propose/human validate/retire; optional identity-based spatial-rule metadata, full source_requirements review; explicit time-series authoring/lifecycle and validated-spec/discovered-identity forecast: docs/help/ORDO-METHODOLOGY-WORKFLOWS-GUIDE.md. Local/browser and illustrated Word30E required. Statistical/spatial execution customer reachability remains named30C2B. No automatic champion or institutional conclusion.

## 30C2B1 ORDO identity aggregation — PARTIAL
ORDO-SPATIAL-AGGREGATION-GUIDE.md: explicit scoped load/selection/reviewed method/confirmation/execution/current GIS revalidation/recovery; ten items. Action illustrations and Word parity pending30E.

## 30C2B2 ORDO statistical specifications — PARTIAL
ORDO-STATISTICAL-SPECIFICATION-GUIDE.md ten-item typed authoring/pagination/review/lifecycle/role/recovery and no-fitting/no-results distinction. Action illustrations/Word parity pending30E.

30D1 action guide: `ISI-ADMINISTRATION-WORKFLOWS-GUIDE.md` (ten sections). Scoped administrative confirmation, safe error/receipt and session boundaries; illustrated parity pending30E.

30D2 ten-item action guide: `ISI-AI-REVIEW-WORKFLOWS-GUIDE.md`; bounded typed scoped evaluation/job/XAI review, no invented SHAP/calibration or automatic model promotion; illustrations pending30E.

30D3A ten-item action guide: `ISI-RESULT-EVIDENCE-GUIDE.md`; faithful typed domain/source/provenance/SHAP/unsupported views; no new numerical support, illustrated parity pending30E.

30D3B ISI-REPORTING-WORKFLOWS-GUIDE.md covers ten reporting workflow items; explicit selections/current evidence confirmations; action-level illustrations/Word parity pending30E.

### 30F Help illustration parity — local candidate, 2026-10-18

Review found that existing multi-screen workflow chapters were difficult to discover because private workflow selection appeared below long topic content and was mixed with short SIMPA/ORDO topics. The local candidate separates these selectors at the top of each authenticated Help surface and labels each detailed choice with its desktop screenshot count. It retains36 short topics,19 detailed chapters, the public six-topic allowlist, product filtering and SIMPA-only SHAP. The manual contains122 figure placements (96 unique images); an exact ordered asset/hash parity check confirms every figure is present in a Help topic or detailed chapter. Focused tests pass (27 passed), full regression passes (1823 passed,46 inherited skips), all seven local gates pass and the independent exact-candidate analyzer passes. The owner's controlled walkthrough follows this Help closeout. Historical VERIFIED coverage rows are not promoted by this candidate; no hosted/server verification is claimed.


## 2026-10-11 — 30D3B reviewed closeout and30D4 scope lock
30D3B IMPLEMENTED/REVIEW_VERIFIED b6812a4:40focused/1781regression PASS/46 inherited skips, seven gates and1280/390/native reporting QA.30D4 IN_PROGRESS typed self-session inventory, fresh identity/status-bound revoke confirmations and safe receipts; existing invitation/recovery/pending SMTP preserved. Exact automation/specs/ISI-30D4-ACCOUNT-SECURITY-WORKFLOWS.md. No auth backend/schema/provider/role expansion; GoraNova real onboarding remains controlled30F, owner credential entry. Illustrated HelpWord30E and final30F pending; hosted/server f587ed0 unchanged.


## 2026-10-11 — 30D4 reviewed closeout and30E scope lock
30D4 IMPLEMENTED/REVIEW_VERIFIED e3ac9c7:24focused/1805regression PASS/46 inherited skips, seven gates and1280/390/native self-session QA.30E IN_PROGRESS governed101 new reviewed screenshot assets,36 basic topics/19 detailed Help chapters, current source/lifecycle/security directions and Word parity. Exact automation/specs/ISI-30E-ILLUSTRATED-HELP-MANUAL.md; asset paths/source hashes enumerated in automation/contracts/ISI-30E-ASSET-PLAN.json. Public six-topic allowlist and product-only SHAP preserved; old artifacts legitimate dated history. Word layout/every-page review and final gates pending; no CI/server inheritance. Real GoraNova onboarding and final checkpoint/ISI-only deployment30F remain pending; last hosted/server f587ed0 unchanged.

## 2026-10-11 — 30E local illustrated Help and Word closeout

30E locally IMPLEMENTED/REVIEW_VERIFIED: seven local gates PASS,6 focused/1812 regression passes/46 inherited skips, native1280/390 keyboard/public/product Help checks,197/197 individually reviewed Word pages and152 figures.36 basic topics/19 chapters/138 dated assets include101 new30 workflow images. Five stale Help regression assertions reconciled with delivered SHAP/product boundaries; no skipped or weakened domain gate. No backend/schema/provider/dependency change. Word hash089cbc886486c7a1be13a5c888c4ab839a44db03ad7295e1892b3464eeffefce. Final exact-main hosted checkpoint, signed ISI-only deployment and real GoraNova onboarding remain30F; last CI/server f587ed0/37914718258 unchanged. SMTP pending, new backups owner-deferred, institutional/MFA/calibration/legal facts remain separately unverified.

## Owner desktop correction — 2026-10-12

Active SIMPA/ORDO Help and Word references are desktop/laptop only. Earlier mobile product captures remain historical evidence, with no active topic/chapter references. Public landing responsiveness remains relevant. The revision adds a section index, bounded image display (no upscaling), a deterministic linked Word index with printed page numbers, and normal-scale desktop replacement captures of existing controls. `automation/contracts/ISI-30F-DESKTOP-DOCUMENTATION.json` governs exact capture identity and scope. `tests/test_isi_30f_desktop_help.py` retains public/product and image identity boundaries. Final candidate, every-page Word review, exact hosted acceptance and controlled ISI-only deployment are pending; earlier release evidence is not reused as verification of this revision.
