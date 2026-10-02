# ISI-27A-R0-R1 — Corrected Shared Help & Release UX Code-Level Surface Audit

Baseline SHA: `39dc1d59a74a03c86f68df093cc07e32d41d028c`  
Baseline tree: `3c7027b375b041043f7305cdab008aee35f16ef7`  
Repository mutation: **NO**  
Hosted GitHub Actions dispatch: **NO**  
Server mutation: **NO**

## Corrected twelve-blocker matrix prestate

| Inventory | Surface | Coverage | Current evidence |
|---|---|---|---|
| INV-A01 | Public website | **MISSING** | Not owned by ISI-23D. |
| INV-A02 | Login | **MISSING** | Not owned by ISI-23D. |
| INV-A03 | Invitation onboarding | **MISSING** | Not owned by ISI-23D. |
| INV-A04 | Email verification | **MISSING** | Not owned by ISI-23D. |
| INV-A05 | Password reset | **MISSING** | Not owned by ISI-23D. |
| INV-A06 | Authenticated app shell | **PARTIAL** | SIMPA access/workspace context covered by SIMPA-H01; cross-product shell Help remains open. |
| INV-A08 | Data workspace | **PARTIAL** | SIMPA governed analytical prerequisite covered by SIMPA-H05; full Data workspace Help remains open. |
| INV-A14 | Reporting workspace | **MISSING** | Shared reporting Help remains open. |
| INV-A15 | Administration workspace | **MISSING** | Shared administration Help remains open. |
| INV-A16 | Account security workspace | **MISSING** | Shared security Help remains open. |
| INV-A17 | Public self-registration | **MISSING** | Surface is intentionally NOT_PRESENT; cross-product absence/help wording remains outside ISI-23D. |
| INV-A21 | Cross-product Help Coverage Matrix | **PARTIAL** | ISI-25-owned shared AI guidance is VERIFIED; Login/Reporting/Administration/Security/shared release coverage remains REMOVE_IN_NAMED_PHASE(ISI-27), so the global matrix honestly remains PARTIAL. |

## Protected predecessor Help/XAI

- `INV-A10` remains **VERIFIED** and is protected from reimplementation.
- `INV-A11` remains **VERIFIED** and is protected from reimplementation.
- `INV-A12` remains **VERIFIED** and is protected from reimplementation.
- `INV-A13` remains **VERIFIED** and is protected from reimplementation.
- `INV-A18` remains **VERIFIED** and is protected from reimplementation.
- `INV-A19` remains **VERIFIED** and is protected from reimplementation.

## Code-level findings

- Public site already has shared base/header/footer template seams but no canonical shared Help guide authority is referenced there.
- Streamlit shell already centralizes login, selection/navigation and calls Data/Reporting/Administration/Account Security workspaces; it is the natural shared authenticated Help entry-point seam.
- Domain-specific SIMPA and ORDO Help workspaces already exist and remain protected predecessor authority.
- Auth API exposes login, invitation acceptance, email verification and password-reset workflows; no public self-registration route was found.
- INV-A17 must therefore be closed as explicit justified NOT_APPLICABLE/NOT_PRESENT coverage, not by adding signup.
- The canonical matrix is honest but shared surfaces remain MISSING/PARTIAL and INV-A21 remains PARTIAL.

## Proposed next implementation shape

- docs/help/ISI-SHARED-USER-GUIDE.md (new canonical shared guide)
- docs/help/ISI-HELP-COVERAGE-MATRIX.md
- src/streamlit_app/app.py
- src/streamlit_app/data_workspace.py
- src/streamlit_app/reporting_workspace.py
- src/streamlit_app/administration_workspace.py
- src/streamlit_app/security_workspace.py
- src/public/templates/partials/header.html and/or footer.html (public Help entry point; exact choice after implementation inspection)
- tests/test_isi_27a_shared_help_contract.py (new)
- targeted inherited auth/public/app-shell tests only where needed

## Scope protection

- INV-A07 is not silently pulled into the corrected twelve-blocker release scope.
- INV-A20 remains OUT_OF_SCOPE/NOT_PRESENT.
- No auth/security semantics, model methodology, runtime data model, dependency, migration, Compose, workflow or server boundary is changed by this audit.

`READY_FOR_ISI27A_IMPLEMENTATION_CONTRACT=PASS` means the code-level surface is understood; it does not mean Help coverage is complete.
