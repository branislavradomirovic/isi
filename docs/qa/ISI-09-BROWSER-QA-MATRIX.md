# ISI-09 Browser QA Matrix

Validate with the SIMPA-only and dual QA accounts.

- `Analitika` opens the SIMPA analytics workspace.
- Empty workspaces clearly report no observations instead of fabricating results.
- Evidence-quality cards are labelled as evidence/coverage metrics, not social-risk metrics.
- Conceptual indicator count remains visible and no indicator is marked validated unless explicitly approved.
- Methodology section reports that no validated method exists by default.
- Creating a monitoring snapshot works and remains scoped to the active SIMPA workspace.
- AI synthesis uses the shared gateway and shows local-only + human-review requirements for sensitive SIMPA data.
- Ollama QA model is `qwen2.5:7b-instruct` for the current development test only.
- AI output is visibly marked as decision support pending human review.
- Accept / reject review controls update only the selected synthesis.
- Switching the dual account to ORDO does not expose the SIMPA analytics workspace or SIMPA data.
- Sidebar remains button-based and the launcher opens one browser tab.
