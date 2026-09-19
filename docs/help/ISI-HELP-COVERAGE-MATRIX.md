# ISI Help Coverage Matrix

Status: CANONICAL CROSS-PRODUCT HELP/XAI COVERAGE ARTIFACT

This matrix implements MasterPlan 0.5A. It inventories every customer-facing USER SURFACE row (INV-A01 through INV-A21) and records honest coverage. ISI-23D verifies SIMPA-owned surfaces and ISI-24D verifies ORDO-owned surfaces; neither falsely promotes shared surfaces owned by later phases.

Coverage vocabulary: MISSING, PARTIAL, COMPLETE, VERIFIED. Only VERIFIED satisfies production completeness for an owned production-critical action. Checklist-level NOT_APPLICABLE must be explicitly justified; none is used to hide missing owned SIMPA content.

| Inventory | Surface | Coverage | Roadmap owner | Canonical Help / evidence |
| --- | --- | --- | --- | --- |
| INV-A01 | Public website | MISSING | FOUNDATION / ISI-27 | Not owned by ISI-23D. |
| INV-A02 | Login | MISSING | ISI-20 / ISI-27 | Not owned by ISI-23D. |
| INV-A03 | Invitation onboarding | MISSING | ISI-13 / ISI-20 | Not owned by ISI-23D. |
| INV-A04 | Email verification | MISSING | ISI-20 | Not owned by ISI-23D. |
| INV-A05 | Password reset | MISSING | ISI-20 | Not owned by ISI-23D. |
| INV-A06 | Authenticated app shell | PARTIAL | FOUNDATION / ISI-23 / ISI-24 | SIMPA access/workspace context covered by SIMPA-H01; cross-product shell Help remains open. |
| INV-A07 | Overview workspace | MISSING | FOUNDATION | Shared overview Help remains open. |
| INV-A08 | Data workspace | PARTIAL | ISI-22 | SIMPA governed analytical prerequisite covered by SIMPA-H05; full Data workspace Help remains open. |
| INV-A09 | AI workspace | VERIFIED | ISI-25 | Shared registry/evaluation/promotion/fallback/circuit/drift/XAI actions are covered by docs/help/ISI-AI-USER-GUIDE.md and tests/test_isi_25b_monitoring_xai_help.py; non-AI shared Help remains separately owned. |
| INV-A10 | SIMPA indicators | VERIFIED | ISI-23 | SIMPA-H02/H03/H04 plus SIMPA User Guide; tests/test_isi_23d_help_xai_contract.py. |
| INV-A11 | SIMPA analytics | VERIFIED | ISI-23 | SIMPA-H05 through H12 plus deterministic statistical XAI; ISI-23D tests. |
| INV-A12 | ORDO indicators | VERIFIED | ISI-24 | ORDO-H01 through H06 plus ORDO User Guide; tests/test_isi_24d_help_xai_contract.py. |
| INV-A13 | ORDO analytics and scenarios | VERIFIED | ISI-24 | ORDO-H05 through H11, governed time-series-spec lifecycle, series discovery, explicit forecast execution, persisted-result presentation and deterministic forecast/scenario XAI; ISI-24D/24E tests. |
| INV-A14 | Reporting workspace | MISSING | ISI-27 | Shared reporting Help remains open. |
| INV-A15 | Administration workspace | MISSING | ISI-20 / ISI-27 | Shared administration Help remains open. |
| INV-A16 | Account security workspace | MISSING | ISI-20 | Shared security Help remains open. |
| INV-A17 | Public self-registration | MISSING | ISI-20 | Surface is intentionally NOT_PRESENT; cross-product absence/help wording remains outside ISI-23D. |
| INV-A18 | SIMPA Help, User Guide and XAI interpretation | VERIFIED | ISI-23 / ISI-25 / ISI-27 | SIMPA domain Help/statistical XAI plus ISI-25 shared AI evaluation/provenance/promotion/fallback interpretation are verified; remaining global release Help remains ISI-27. |
| INV-A19 | ORDO Help, User Guide and XAI interpretation | VERIFIED | ISI-24 / ISI-25 / ISI-27 | ORDO forecast/scenario Help/XAI plus ISI-25 shared AI evaluation/provenance/promotion/fallback interpretation are verified; remaining global release Help remains ISI-27. |
| INV-A20 | Commercial checkout/payment surface | MISSING | OUT_OF_SCOPE | Surface is NOT_PRESENT; no ISI commercial payment architecture exists. |
| INV-A21 | Cross-product Help Coverage Matrix | PARTIAL | ISI-23 / ISI-24 / ISI-25 / ISI-27 | ISI-25-owned shared AI guidance is VERIFIED; Login/Reporting/Administration/Security/shared release coverage remains REMOVE_IN_NAMED_PHASE(ISI-27), so the global matrix honestly remains PARTIAL. |

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

- MISSING/PARTIAL shared coverage remains a release blocker for its owning phase; ORDO references do not make shared Login/Data/AI/Reporting/Administration/Security Help VERIFIED, and this matrix is not a claim that ISI-27 is ready.
- Unsupported XAI is shown as unavailable, never invented.
- No Help text creates a formula, LISI weight, threshold, citizen risk label, eligibility rule, causal claim, forecast or policy conclusion.
- Server verification/deployment remains deferred to owner-approved ISI-28.
