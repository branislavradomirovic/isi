# ISI Help Coverage Matrix

Status: CANONICAL CROSS-PRODUCT HELP/XAI COVERAGE ARTIFACT

This matrix implements MasterPlan 0.5A. It inventories every customer-facing USER SURFACE row (INV-A01 through INV-A21) and records honest coverage. ISI-23D verifies the SIMPA domain surface only; it does not falsely promote ORDO/shared surfaces that belong to later phases.

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
| INV-A09 | AI workspace | PARTIAL | ISI-25 | SIMPA bounded synthesis covered by SIMPA-H12; shared AI workspace Help/XAI remains ISI-25. |
| INV-A10 | SIMPA indicators | VERIFIED | ISI-23 | SIMPA-H02/H03/H04 plus SIMPA User Guide; tests/test_isi_23d_help_xai_contract.py. |
| INV-A11 | SIMPA analytics | VERIFIED | ISI-23 | SIMPA-H05 through H12 plus deterministic statistical XAI; ISI-23D tests. |
| INV-A12 | ORDO indicators | MISSING | ISI-24 | ORDO Help/XAI is owned by ISI-24. |
| INV-A13 | ORDO analytics and scenarios | MISSING | ISI-24 | ORDO Help/XAI is owned by ISI-24. |
| INV-A14 | Reporting workspace | MISSING | ISI-27 | Shared reporting Help remains open. |
| INV-A15 | Administration workspace | MISSING | ISI-20 / ISI-27 | Shared administration Help remains open. |
| INV-A16 | Account security workspace | MISSING | ISI-20 | Shared security Help remains open. |
| INV-A17 | Public self-registration | MISSING | ISI-20 | Surface is intentionally NOT_PRESENT; cross-product absence/help wording remains outside ISI-23D. |
| INV-A18 | SIMPA Help, User Guide and XAI interpretation | VERIFIED | ISI-23 / ISI-25 / ISI-27 | In-app SIMPA Help + docs/help/SIMPA-USER-GUIDE.md + statistical XAI are implemented; shared AI evaluation remains ISI-25. |
| INV-A19 | ORDO Help, User Guide and XAI interpretation | MISSING | ISI-24 / ISI-25 / ISI-27 | Owned by ISI-24. |
| INV-A20 | Commercial checkout/payment surface | MISSING | OUT_OF_SCOPE | Surface is NOT_PRESENT; no ISI commercial payment architecture exists. |
| INV-A21 | Cross-product Help Coverage Matrix | PARTIAL | ISI-23 / ISI-24 / ISI-25 / ISI-27 | Matrix artifact is CURRENT_AS_BUILT; SIMPA domain coverage is VERIFIED but global cross-product coverage remains open. |

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

## Hard boundaries

- MISSING/PARTIAL shared or ORDO coverage remains a release blocker for its owning phase; this matrix is not a claim that ISI-27 is ready.
- Unsupported XAI is shown as unavailable, never invented.
- No Help text creates a formula, LISI weight, threshold, citizen risk label, eligibility rule, causal claim, forecast or policy conclusion.
- Server verification/deployment remains deferred to owner-approved ISI-28.
