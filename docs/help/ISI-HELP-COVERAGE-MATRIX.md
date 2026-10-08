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
