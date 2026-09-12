# ISI ORDO Methodology v1 - Canonical Design Baseline

Status: **OWNER-APPROVED DIRECTION / NOT YET VALIDATED METHODOLOGY**
Decision date: **2026-09-12**

This document defines the production-methodology design contract for ISI-24. It does not validate any ORDO indicator formula, threshold, causal model, forecast model, scenario impact coefficient, competitiveness score, sustainability score, or institutional development conclusion.

## 1. Purpose

ORDO is a destination-intelligence, planning and scenario-support application. It is intended to help authorized users understand destination evidence, trends, seasonality, capacity, spatial relationships, development goals, possible scenarios and uncertainty.

ORDO is not allowed to present unsupported scenario assumptions as predictions or causal effects.

## 2. Canonical analytical progression

The production analytical flow is:

`development goal -> evidence -> indicator methodology -> descriptive analytics -> model output -> forecast and/or scenario -> uncertainty -> AI synthesis -> human review`

Forecast and scenario are separate objects with separate semantics.

## 3. Canonical analytical key

A typical ORDO analytical record may be keyed by:

`destination x period x source x methodology version`

Additional dimensions may include:

- source market;
- market segment;
- accommodation/service category;
- geographic/spatial unit;
- season;
- event;
- mobility/accessibility dimension;
- environmental or social indicator dimension;
- scenario ID;
- forecast/model version.

## 4. Evidence and data contract

Every production analytical observation should preserve, where available:

- source identity and version;
- ingestion timestamp;
- destination/geographic scope;
- time period and frequency;
- unit of measure;
- methodology version;
- data quality and validation state;
- missingness state;
- provenance/lineage pointer;
- human validation state where required.

`missing`, `not collected`, `not applicable`, `suppressed`, and numerical zero are distinct states.

Missing data must never be silently converted to zero.

## 5. Methodology lifecycle

Minimum lifecycle:

`DRAFT -> PROPOSED -> VALIDATED -> RETIRED`

A production analytical result records the exact methodology version and model version used.

No forecast or scenario impact is labelled validated before the corresponding methodology/model has passed the approved validation protocol.

## 6. Descriptive and KPI layer

Possible KPI families, only where methodology explicitly defines them, include:

- arrivals;
- overnights;
- occupancy;
- average length of stay;
- capacity;
- seasonality;
- market-source distribution;
- spatial concentration/distribution;
- accessibility indicators;
- employment/economic aggregates;
- environmental/sustainability evidence;
- cultural/natural asset evidence;
- evidence completeness and freshness.

A readiness or evidence-quality score must not be presented as destination performance unless a separate validated methodology defines such a measure.

## 7. Indicator contract

Each production indicator must specify:

- stable indicator ID and name;
- analytical purpose;
- formula/computation rule where applicable;
- required fields;
- unit/scale;
- spatial aggregation;
- temporal aggregation;
- missing-data rule;
- outlier/revision rule;
- quality preconditions;
- reference dataset/calculation;
- methodology lifecycle state;
- approver;
- version/effective dates.

No formula is inferred from a name or invented by an LLM.

## 8. Regression and explanatory model layer

Model family is selected by target semantics.

Preferred baselines:

- count targets such as arrivals/overnights: Poisson;
- over-dispersed counts: Negative Binomial;
- continuous targets such as average stay/expenditure where appropriate: linear or robust regression;
- rates/proportions such as occupancy: statistically appropriate fractional/beta-type model;
- repeated destination/panel data: fixed-effects, mixed-effects or hierarchical models where justified.

Challengers may include gradient-boosted trees or hybrid models only after baseline comparison.

Minimum output contract:

- target definition;
- feature list/versions;
- training/evaluation period;
- sample size;
- error/fit metrics;
- uncertainty/confidence interval where appropriate;
- diagnostics;
- methodology/model version;
- limitation and non-causal wording unless an approved causal design exists.

## 9. Forecasting methodology

Forecasting is allowed only for targets with sufficient validated historical data and an explicit forecast methodology.

### 9.1 Baseline families

Preferred starting models may include:

- naive/seasonal naive benchmark;
- ETS/exponential smoothing;
- SARIMA/SARIMAX;
- count time-series model where target semantics require it.

Challengers may include:

- gradient boosting using lag/seasonal features;
- other registered ML time-series models;
- approved hybrid models.

A challenger must outperform an appropriate simple baseline under the approved backtest before promotion.

### 9.2 Temporal validation

Random train/test splitting is not valid for production time-series acceptance.

Use rolling-origin/forward-chaining backtesting, for example:

`train through T1 -> test T1+1`

`train through T2 -> test T2+1`

and aggregate performance across multiple origins.

### 9.3 Core forecast metrics

Use target-appropriate metrics, including where applicable:

- MAE;
- RMSE;
- sMAPE;
- MASE;
- bias;
- prediction-interval coverage;
- interval width/sharpness;
- seasonal baseline comparison.

### 9.4 Forecast presentation

Never present only one exact future value when uncertainty is material.

Preferred output:

- point/median estimate;
- lower/upper interval;
- model/version;
- training window;
- backtest metrics;
- assumptions/exogenous variables;
- limitations.

## 10. Scenario methodology

A scenario is a planning object, not automatically a forecast.

A scenario contains user-authored or methodology-authored assumptions such as:

- capacity change;
- transport/accessibility change;
- event assumption;
- market assumption;
- investment/measure assumption;
- environmental constraint;
- policy/planning measure.

### 10.1 Deterministic scenario engine

The first production scenario engine should be deterministic and explicit.

For each scenario variable record:

- baseline value;
- assumption/change;
- transformation rule;
- resulting value if directly computable;
- source/methodology;
- uncertainty if available.

### 10.2 Impact boundary

If there is no approved response/impact model linking an assumption to an outcome, report:

`impact = NOT_ESTIMATED`

Do not ask an LLM to invent a percentage effect.

### 10.3 Sensitivity and uncertainty

Where a validated response model exists, later scenario analysis may expose:

- one-way sensitivity;
- multi-variable sensitivity;
- scenario ranges;
- Monte Carlo or equivalent uncertainty propagation.

Monte Carlo is not automatically valid. Distributional assumptions must be methodology-owned and validated.

## 11. Spatial/GIS analytical contract

ORDO may use spatial analysis when data and methodology support it.

Spatial outputs must preserve:

- coordinate/reference system;
- geographic unit/version;
- aggregation rule;
- source/provenance;
- spatial precision/privacy rule;
- methodology version.

Possible visualization/analysis families include:

- choropleth maps;
- point/asset maps;
- accessibility/service-area views;
- spatial concentration;
- distance/travel-time measures;
- spatial clustering only with validated methodology.

A map is evidence presentation, not causal proof.

## 12. Segmentation and clustering

ORDO may use unsupervised methods for market/destination analytical profiles where justified.

Candidate families:

- K-Means;
- hierarchical clustering;
- mixture models.

Requirements:

- methodology-defined features/scaling;
- stability analysis;
- neutral profile labels;
- human-reviewed interpretation;
- no normative ranking unless a separate validated methodology defines one.

## 13. Feature governance

Every feature used by a registered ORDO model must preserve:

- stable feature key;
- source lineage;
- transformation;
- spatial/temporal granularity;
- aggregation window;
- missing-data rule;
- sensitivity class;
- version;
- methodology/model dependencies.

Future values of exogenous features used for forecasts must be explicitly marked as known, assumed, scenario-derived or externally forecast.

## 14. Explainability and uncertainty

Classical regression models expose coefficients and confidence intervals where appropriate.

Tree/boosting models may expose:

- global feature importance;
- SHAP or equivalent contribution analysis;
- partial dependence where appropriate.

Required UI warning:

`Feature contribution or statistical association does not by itself establish causal effect.`

Forecast views expose intervals and validation metrics.

Scenario views expose assumptions separately from estimated outcomes.

## 15. Document AI and evidence extraction

ORDO may use VLM/document models for:

- OCR;
- table extraction;
- chart interpretation;
- planning-strategy document extraction;
- GIS screenshot/context extraction;
- metadata/source tagging.

Machine-extracted facts are marked `EXTRACTED_UNVERIFIED` until deterministic validation or human review where required.

## 16. RAG and knowledge contract

Allowed namespace families remain:

- `PUBLIC/ISI`;
- `PUBLIC/ORDO`;
- `ORG-<organization UUID>/ORDO`.

SIMPA private namespaces are not valid ORDO private retrieval context.

Use a dedicated evaluated embedding model for retrieval.

## 17. LLM synthesis contract

The LLM receives a structured analytical snapshot rather than unbounded raw data.

Minimum conceptual input:

```json
{
  "goal": {},
  "period": "...",
  "methodology_versions": [],
  "validated_indicators": [],
  "descriptive_results": [],
  "regression_results": [],
  "forecast_results": [],
  "scenario_results": [],
  "spatial_results": [],
  "data_quality": {},
  "missing_evidence": [],
  "retrieved_evidence": [],
  "limitations": []
}
```

The synthesis must preserve distinctions among:

- observed fact;
- calculated indicator;
- statistical association;
- forecast;
- user scenario assumption;
- model-estimated scenario impact;
- missing/not-estimated result.

The LLM must not turn `NOT_ESTIMATED` into a prediction.

## 18. User-interface presentation contract

Canonical order:

`Evidence -> Destination KPIs -> Trend/Seasonality -> Models -> Forecast and/or Scenario -> AI interpretation -> Human review`

Recommended ORDO visualizations:

- time-series line chart;
- seasonality heatmap;
- map/spatial view;
- source-market distribution;
- forecast fan chart/interval band;
- scenario waterfall/delta view;
- model feature-importance/SHAP view where appropriate;
- evidence and methodology details panel.

### Forecast view

Must show interval/range, model version, backtest quality and limitations.

### Scenario view

Must show assumptions separately from outcomes. If no response model exists, show `NOT_ESTIMATED` rather than a fabricated delta.

## 19. Champion/challenger lifecycle

Each ORDO statistical/ML/embedding/LLM/VLM capability has:

- champion model;
- challenger set;
- dataset/eval version;
- forecast backtest or problem-specific metrics;
- approval record;
- rollback target.

No promotion occurs solely because a model is newer, larger or popular externally.

## 20. ISI-24 implementation acceptance

ISI-24 cannot close until at minimum:

- production indicator registry contracts are defined;
- every implemented formula has reference calculation coverage and methodology state;
- forecast and scenario semantics are technically separated;
- forecasting uses temporal backtesting;
- uncertainty is displayed;
- no unsupported causal/impact claim is introduced;
- scenario impact is `NOT_ESTIMATED` without an approved response model;
- provenance is visible;
- AI synthesis consumes bounded analytical snapshots;
- Help and User Guide explain forecast/scenario distinctions and limitations;
- DRAFT/PROPOSED outputs cannot be confused with VALIDATED methodology.

## 21. Open methodology items intentionally not decided here

This baseline does not decide:

- validated ORDO indicator formulas;
- destination ranking weights;
- competitiveness/sustainability thresholds;
- causal response coefficients;
- production forecast target list;
- scenario impact distributions;
- institutional development recommendations.

Those require separate evidence and explicit owner/human methodology approval.
