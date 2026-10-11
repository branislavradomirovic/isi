# ORDO User Guide

Status: ISI-24E F01/F02 remediation candidate guide for the authenticated ORDO product.

This guide explains the implemented ORDO destination-intelligence workflow. It does not grant access, validate a methodology by itself, replace expert review or certify a production deployment. Backend organization, product, workspace and permission checks remain authoritative.

## 1. Access and workspace context (ORDO-H01)

Sign in with an institutional account, select the organization, select ORDO and then select an authorized workspace. The active organization -> membership -> role/permission -> ORDO entitlement -> workspace chain scopes every request. UI visibility is not authorization.

Typical read actions require `indicator.read` or `analysis.read`; configured mutations use `workspace.manage`, `indicator.manage` or `analysis.run`. If a module or action is absent, do not manipulate URLs or IDs. Select an authorized context or ask an administrator to assign the correct access. ORDO Help appears only for ORDO; SIMPA Help and data remain product-isolated.

## 2. Destination profile, resources and stakeholders (ORDO-H02)

The Overview records the destination profile, destination assets/resources and stakeholders. Users with `workspace.manage` can use the configuration forms. Required names must describe real institutional records; optional type, year, location and notes provide context.

Example: record a protected natural asset and its manager as separate asset and stakeholder records. These records do not assign a destination score, monetary value, rank, forecast or policy conclusion. The organization is responsible for accuracy and for avoiding unauthorized personal or sensitive data.

Safe recovery: correct rejected required fields or restore the correct workspace/permission context. Never fill missing institutional data with invented examples.

## 3. Monitoring cycles (ORDO-H03)

A monitoring cycle organizes evidence within a period. With `indicator.manage`, create a code, title, start date, end date and one of `planned`, `open` or `closed`. The end cannot precede the start.

These are workflow states. `closed` does not mean a development objective succeeded, evidence is complete or an intervention worked. A cycle must match the time semantics of its approved methodology and source evidence. Historical analytical results should not be rewritten when a new cycle is required.

## 4. Indicators, observations and methodology state (ORDO-H04)

The indicator screen shows the ORDO registry by pillar and dimension, its unit hint and methodology summary, plus persisted provenance-ready observations. A visible conceptual indicator is not automatically calculable.

Methodology follows `DRAFT -> PROPOSED -> VALIDATED -> RETIRED`:

- `DRAFT` is authoring.
- `PROPOSED` is controlled review/testing.
- `VALIDATED` records explicit human approval with the required evidence.
- `RETIRED` preserves historical reproducibility but is not authority for new work.

Missing values are not zero. An indicator name, note or Help text never creates a formula, weight, threshold, target value, performance class or ranking. When evidence or a validated methodology is unavailable, obtain it through the governed lifecycle; do not generate a value.

## 5. Governed analytical artifacts and evidence quality (ORDO-H05)

ORDO analytics consumes only an eligible governed analytical snapshot (`VALIDATED`/`FROZEN`) or an eligible single-snapshot feature version (`GOVERNED`/`FROZEN`), with no invalidation. The selector exposes the artifact ID and fingerprint. Raw upload bytes and legacy/invalidated runs do not authorize new analytics.

The evidence snapshot shows observation and validated-observation coverage, provenance, indicator, dimension and pillar coverage. Its evidence-quality score/band summarizes the implemented evidence contract. It is not a competitiveness, sustainability, inclusion, employment, quality-of-life, investment or destination-performance score.

Example: full provenance coverage alongside missing dimensions means the present records are traceable; it does not mean the destination is performing well. If no artifact is eligible, return to the governed data workflow and validate/freeze an appropriate artifact.

## 6. Methodology and specification lifecycle (ORDO-H06)

With `analysis.read`, review time-series specifications and their exact governed-run, indicator, methodology, input SHA-256, contract, version/fingerprint and lifecycle evidence. With `indicator.manage`, create a `DRAFT`, propose it, validate it with a nonblank human validation note and evidence reference, or retire a `VALIDATED` version with a retirement note. The backend resolves the current validated indicator-methodology ID/version/fingerprint and locked semantics; users do not enter those authority fields.

Authoring selects an existing governed analytics run and records the series key, target indicator/semantic, time index/frequency/key fields, observation window/as-of, minimum history, maximum missing ratio and rule, outlier/revision/comparability policies, transformation/trend/optional seasonality, candidate families, horizon/unit, diagnostic requirements, limitations and rolling-origin plan. If the run is inaccessible, legacy, changed, or lacks a current validated methodology, creation fails closed.

Indicator methodologies, statistical contracts and time-series specifications retain exact IDs, versions, contract content and fingerprints. A change to methodology, inputs or contract meaning requires a new version rather than rebinding history. The accepted 24B specification keeps `forecast_execution=false`, `automatic_model_selection=false` and `non_causal=true`; the separate 24C runtime consumes that immutable specification without rewriting it. Validation approves the specification, not a champion/model promotion, future-performance guarantee or causal claim.

## 7. Analytical snapshots and provenance (ORDO-H07)

With `analysis.read`, review snapshots. With `analysis.run`, save a new snapshot from the currently selected eligible artifact. A run stores the artifact and dataset-contract bindings, quality state, coverage and fingerprints used by downstream workflows.

An immutable run is a reproducibility checkpoint, not a forecast or scenario result. If its governed binding changes, becomes invalid or is legacy-only, downstream work fails closed. Create a new governed artifact and run rather than editing the historical identity.

## 8. Development goals and scenarios (ORDO-H08)

With `analysis.run`, create a development goal and then a scenario linked to that goal. Scenario assumptions and proposed measures are user-authored planning inputs. Workflow states such as goal `draft/active/closed` and scenario `draft/review_ready/accepted/rejected` are not evidence of effectiveness.

Example: “a new transport line will operate next year” is an assumption until supported by evidence. Even an accepted scenario does not establish that the line exists, forecast visitor volume, estimate financial or social effects, or recommend implementation.

Relevant financial, environmental, regulatory and social assessments remain separate human-controlled obligations.

## 9. Evidence-only scenario assessment (ORDO-H09)

Select a scenario and eligible analytical snapshot, then create an evidence-only assessment. The persisted boundary is explicit:

- `forecast_performed=false` means the scenario assessment is not a forecast.
- `impact=NOT_ESTIMATED` with `NO_APPROVED_RESPONSE_MODEL` means impact was deliberately not estimated because no approved response/impact model exists.
- An absent numeric impact remains absent; it is never zero.
- `LEGACY_NOT_EVALUATED` is historical compatibility truth. It must not be rewritten as if a later assessment or forecast executed.

The assessment may present evidence coverage and missing dimensions. It does not produce a causal effect, predictive confidence, feature importance, rank or automatic recommendation. The scenario contract version, methodology key/version, input snapshot SHA-256, reference identities, limitations and human-review state support review and reproduction.

## 10. Governed forecast execution, backtesting and uncertainty (ORDO-H10)

The Analytics workspace exposes the complete governed workflow. With `analysis.read`, list and inspect specifications, discover eligible series identities and review persisted runs. With `analysis.run`, execute only from an existing `VALIDATED` specification:

1. Select a specification by human-readable series key, version and indicator; do not paste a specification UUID.
2. Select one deterministic series identity discovered by the backend from the exact revalidated governed binding. Discovery returns only unique key/value identities, never raw source records.
3. Explicitly select one family from that specification’s `candidate_families`.
4. Select interval level `0.80`, `0.90` or `0.95`.
5. Execute and review the newly persisted result plus XAI/provenance.

There is no automatic family selection, ranking, winner or fallback. Only accepted 24C `naive` and `seasonal_naive` families can produce `ESTIMATED`; an allowed family without accepted execution semantics persists `NOT_ESTIMATED` with its bounded reason. A family outside the validated specification is rejected.

### Result states

`ESTIMATED` means the accepted deterministic runtime produced and persisted output for the exact validated specification, governed input, explicit series identity, explicitly requested family and interval level. Only this state displays persisted point/lower/upper values.

`NOT_ESTIMATED` is a successful bounded outcome, not zero, a fabricated empty series or a hidden failure. The stable reason code explains why the runtime intentionally did not produce forecast points. Unsupported family, transformation, missing/invalid/irregular evidence, insufficient history/origins/seasonal evidence/interval calibration, or unavailable required metrics must remain explicit. Safe recovery is to correct governed evidence or author a new specification version through the approval lifecycle; never mutate historical contract/result truth or substitute a fallback.

### Requested and executed family

The request identifies one family. An `ESTIMATED` run records the executed family. A `NOT_ESTIMATED` run has no executed family. `automatic_model_selection=false` means the system did not compare candidates and choose a winner, and it did not automatically fall back. Validation of a candidate-family list is specification approval, not model promotion.

### Intervals

Forecast points contain stored time, point, lower, upper and calibration residual count. The stored interval method and configured interval level describe the accepted uncertainty-output contract. They are not a generic probability that the forecast is correct, a model confidence score or a causal interval.

### Rolling-origin backtesting and metrics

The rolling-origin plan and per-origin records preserve chronological evaluation. Aggregate MAE, RMSE, bias, sMAPE, MASE, optional seasonal baseline comparison and interval summaries are shown only when persisted. Metric availability records whether a metric exists and its denominator. An unavailable metric remains unavailable.

Rolling-origin metrics are historical backtest diagnostics, not proof of future performance. Diagnostics and warnings are displayed exactly as stored. The presentation adds no universal pass/fail, good/bad or production-quality threshold.

### Provenance and limitations

Review the exact forecast run/schema, analytics run, time-series specification ID/version/fingerprint, target indicator, target methodology ID/version/fingerprint, input snapshot SHA-256, series identity, request/result fingerprints, engine key/version and creation metadata. `non_causal=true` forbids causal interpretation. `automatic_policy_recommendation=false` means the output does not select an intervention.

Feature importance, generic confidence, causal effect, destination ranking, automatic recommendation and unpersisted values are explicitly unavailable.

## 11. Bounded local ORDO AI synthesis (ORDO-H11)

The AI section uses the governed snapshot as evidence and retains `source_snapshot_sha256`, provider, model, effective policy, prompt key/version, structured output or error and human-review status. ORDO’s current policy is local-only. AI text is explanatory evidence synthesis; it is not numerical authority.

Select a governed snapshot, choose monitoring or scenario review, and submit only if `analysis.run` is authorized. For scenario review, select an existing scenario. Review all provenance and limitations before accepting or rejecting with a note. `pending` is not accepted.

Provider, queue or structured-output failure stays visible and must not be replaced with invented text. ISI-24D does not claim champion/challenger evaluation, model promotion, fallback quality or winner status; those shared contracts belong to ISI-25.

## 12. Help, recovery and human review (ORDO-H12)

Open “ORDO Help” only inside the ORDO product and select ORDO-H01 through ORDO-H12. Each topic supplies the ten MasterPlan 0.5A fields: purpose, time of use, role boundary, exact steps, state semantics, example, non-goals, recovery, limitations and provenance/human review.

If UI behavior and this guide disagree, stop the affected institutional interpretation, preserve a non-sensitive description and report governance drift. Do not improvise formulas, values, permissions or model claims.

The ORDO-owned matrix rows/actions become `VERIFIED` through ISI-24D tests. Global `INV-A21` remains `PARTIAL`: shared Login, Data, AI, Reporting, Administration and Security Help are not made complete merely because this ORDO guide references their boundaries. Server verification remains deferred to owner-approved ISI-28.


## 29A Graphical XAI — pregled grafikona sačuvanih rezultata

**Šta/kada:** grafikon pomaže u pregledu postojeće tabele rezultata; nije novo modeliranje. Otvorite Analitika → sačuvani rezultat. **Prava:** ista analysis.read prava i organization/product/workspace scope kao za rezultat.

**Koraci:** pročitajte model/skaliranje i legendu, pregledajte grafikon, uporedite sa izvornom tabelom, proverite fingerprint i metodološka ograničenja, zatim obavite human review.

**Polja/stanja:** numerička nula ostaje zero; missing interval je unavailable. Nepodržani schema/model, neispravni brojevi ili intervali daju poruku umesto izmišljenog grafikona. NOT_ESTIMATED nema nultu prognozu. ORDO prognoze prikazuju sačuvane tačke i intervale; SHAP matrice pripadaju podržanom SIMPA numeričkom modelu i nisu objašnjenje ORDO prognoze ili LLM teksta.

**Primer:** coefficient estimate=0 je validna tačka; missing CI nije zero-width interval. **Non-goals:** grafikoni nisu uzročni efekti, policy zaključci ili AI confidence score. Nema novih residual/calibration tačaka kada nisu sačuvane.

**Errors / safe recovery:** koristite tabelu/JSON ako grafikon nije dostupan; proverite verziju/format dokaza kroz postojeći workflow. Ne menjajte stari rezultat da biste dobili grafikon.

**Limits:** najviše 24 koeficijenta, 60 tačaka i 40 selectable origins; svaki ograničen prikaz je označen, postojeće pune tabele/JSON ostaju dostupne. Oznake se skraćuju u grafikonu; puni termini su u tabeli. Chart SVG je responsive; tabelarni fallback ostaje pristupačan tastaturom.

**Provenance/review:** prikaz ne refituje model, ne čita nove izvore i ne menja evidence. Methodology/model/input/result identitet i human review ostaju autoritet.

Prognoza prikazuje point i sačuvane lower/upper granice, uz interval method/level. U „Backtest poreklo / origin” izaberite jedan zapis; braon označava actual, plavo forecast. X osa backtesta koristi sačuvani observation index, ne izmišljeni datum. Preklapajući origins se ne spajaju. Empirijski interval ne mora sadržati point; prikazuje se tačno sačuvan.
