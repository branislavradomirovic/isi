# ISI-11 Browser / Ollama QA Matrix

Use the ORDO or dual-access demo account after the automated local smoke passes.

| Area | Expected result |
|---|---|
| ORDO navigation | `Analitika` opens the ORDO analytics workspace, not the former placeholder and not SIMPA analytics. |
| Evidence snapshot | Observation, provenance, indicator, dimension and pillar coverage are visible. `Kvalitet dokaza` is clearly described as evidence quality, not a destination outcome score. |
| Methodologies | No methodology is presented as validated unless explicitly created and reviewed. Initial conceptual indicators remain conceptual. |
| Development goal | A user can create a development goal with a focus area. No fake target or statistic is pre-filled. |
| Scenario | A user can create assumptions and measures as planning inputs. They are visually framed as user-authored inputs. |
| Scenario assessment | Assessment is labeled evidence-only / readiness-oriented and `forecast_performed=false`. It does not generate visitor, investment, employment, inclusion or sustainability forecasts. |
| ORDO AI | Local synthesis uses the shared ISI gateway, ORDO prompt and local-only policy. |
| AI output | Output separates evidence from assumptions, presents limitations, `forecast_performed=false`, and requires human review. |
| Human review | Pending synthesis can be accepted or rejected explicitly. |
| SIMPA isolation | Switching to SIMPA shows SIMPA analytics. ORDO goals/scenarios/syntheses are not visible in SIMPA. |
| Product switch | Dual user can switch SIMPA ↔ ORDO without cross-product data leakage. |
| Sidebar | Existing button-based navigation remains intact. |
| Browser launch | QA opens one Streamlit tab only. |
| Errors | No traceback, raw exception, or database error is shown. |

Manual acceptance token: `ISI-11 VISUAL QA PASS`.
