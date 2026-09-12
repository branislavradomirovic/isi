# ISI AI Model Evaluation Protocol v1

Status: **OWNER-APPROVED CANONICAL EVALUATION BASELINE**
Decision date: **2026-09-12**

This protocol governs evaluation and promotion of statistical/ML, embedding, LLM and VLM capabilities used by SIMPA and ORDO. It does not select a permanent production champion in advance.

## 1. Core rule

Model selection is evidence-driven.

A model is not promoted because it is newer, larger, more popular, or stronger on an external benchmark. It must outperform the registered baseline on ISI-relevant evaluation while satisfying privacy, provenance, structured-output, latency/resource and human-review requirements.

## 2. Capability classes

Evaluate capabilities separately by role:

1. deterministic statistical/ML models;
2. embeddings/retrieval models;
3. text LLMs;
4. VLM/document models;
5. optional routing/tagging/lightweight classifiers.

A single model does not need to be champion for every role.

## 3. Current local candidate inventory

Owner-supplied Ollama models available on the MacBook at decision time:

- `qwen3:1.7b-q4_K_M`
- `qwen3:4b-instruct-2507-q4_K_M`
- `qwen3-vl:4b-instruct-q4_K_M`
- `qwen2.5vl:3b`
- `qwen2.5:7b-instruct`
- `gemma3:4b`

Initial intended evaluation roles:

| Candidate | Primary evaluation role |
|---|---|
| `qwen3:1.7b-q4_K_M` | routing, tagging, short structured extraction |
| `qwen3:4b-instruct-2507-q4_K_M` | text synthesis/reasoning candidate |
| `qwen2.5:7b-instruct` | stronger/slower text challenger and existing QA baseline |
| `qwen3-vl:4b-instruct-q4_K_M` | document/VLM extraction and multimodal synthesis candidate |
| `qwen2.5vl:3b` | VLM challenger/fallback candidate |
| `gemma3:4b` | cross-family challenger/second-opinion candidate |

No row is a production lock.

## 4. Embedding candidates

RAG requires a dedicated embedding model.

Initial candidates may include:

- `qwen3-embedding:0.6b` - compact multilingual candidate;
- `qwen3-embedding:4b` - larger same-family challenger;
- `bge-m3` - multilingual cross-family challenger.

These candidates are not declared installed by this document. Installation is a later explicit implementation action.

## 5. Canonical evaluation datasets

Create and version:

- `SIMPA-EVAL-v1`
- `ORDO-EVAL-v1`

Each case must have a stable ID and metadata sufficient to reproduce the evaluation.

Minimum case metadata:

```json
{
  "case_id": "...",
  "domain": "SIMPA|ORDO",
  "capability": "text|vlm|embedding|statistical_ml|routing",
  "language": "sr|en|...",
  "input_version": "...",
  "expected_contract": {},
  "source_refs": [],
  "sensitivity_class": "...",
  "methodology_version": "...",
  "human_gold_state": "draft|approved",
  "notes": "..."
}
```

Evaluation data must not contain production secrets. Sensitive institutional data requires the governance controls established by ISI-21 before use.

## 6. Text-LLM evaluation dimensions

### 6.1 Grounded factuality

Measure whether the answer is supported by the provided evidence/context.

Failures include:

- invented source facts;
- invented indicator values;
- invented coefficients/probabilities;
- invented methodology states;
- converting missing evidence into asserted fact.

### 6.2 Hallucination rate

Track unsupported atomic claims per case and the proportion of cases with any unsupported material claim.

Production promotion requires an explicit domain threshold defined for the target capability.

### 6.3 Structured-output validity

For JSON/contract outputs measure:

- valid parse rate;
- schema-valid rate;
- required-field completeness;
- enum/value-contract compliance;
- deterministic refusal/failure behavior when evidence is insufficient.

### 6.4 Provenance compliance

Measure whether the model:

- cites/links only supplied or retrieved evidence;
- preserves source identity/version;
- distinguishes observed, calculated, forecast, scenario and missing states;
- avoids attributing a claim to a source that does not support it.

### 6.5 Serbian-language quality

Evaluate:

- terminology consistency;
- grammar and clarity;
- professional institutional tone;
- preservation of domain terms;
- avoidance of misleading overstatement.

Human scoring is acceptable where deterministic metrics are insufficient.

### 6.6 Instruction compliance

Include adversarial cases that test:

- output schema;
- maximum scope;
- prohibited causal language;
- no cross-product knowledge use;
- human-review requirement;
- refusal/insufficient-evidence contract.

### 6.7 Latency and resource footprint

Record at minimum:

- model name/version;
- prompt/input size;
- output size;
- end-to-end latency;
- tokens/sec where available;
- peak/steady memory estimate where measurable;
- timeout/failure rate.

Quality remains primary; latency/resource is a deployment constraint, not a substitute for factuality.

## 7. VLM/document evaluation

Evaluate separately for:

- OCR/text extraction;
- table extraction;
- chart interpretation;
- document metadata extraction;
- image/evidence tagging;
- multimodal synthesis.

Metrics may include:

- exact/normalized field accuracy;
- cell-level table precision/recall;
- character/word error rate where appropriate;
- numeric transcription accuracy;
- chart-value tolerance accuracy;
- unsupported-claim rate;
- structured-output validity;
- provenance linkage accuracy.

All machine-extracted facts remain `EXTRACTED_UNVERIFIED` until the workflow's deterministic/human validation requirement is satisfied.

## 8. Embedding/RAG evaluation

Evaluate retrieval independently from generation.

Core retrieval metrics may include:

- Recall@k;
- Precision@k where relevant;
- MRR;
- nDCG;
- context precision;
- context recall;
- namespace isolation pass rate;
- Serbian/multilingual retrieval quality;
- latency/index size.

Mandatory negative tests:

- SIMPA query must not retrieve ORDO private context;
- ORDO query must not retrieve SIMPA private context;
- organization A must not retrieve organization B private context;
- public/private namespace boundaries must be preserved.

Generator evaluation must also test whether the LLM ignores irrelevant retrieved context and does not treat retrieved text as methodology authority unless the source is approved for that purpose.

## 9. Statistical/ML evaluation

### 9.1 Baseline first

Every ML challenger is compared against an explicit simple baseline appropriate to the target.

Examples:

- linear regression before boosted regression;
- Poisson before more complex count models;
- logistic regression before boosted classification;
- naive/seasonal-naive and ETS/SARIMA before more complex forecasting.

### 9.2 Split strategy

Use the split strategy that matches deployment semantics:

- temporal/rolling-origin for forecasts;
- grouped split for municipality/system/provider leakage risks;
- stratified/random split only when leakage controls justify it;
- nested or repeated validation where model selection bias is material.

### 9.3 Metrics

Possible metrics by capability:

Continuous regression:
- MAE;
- RMSE;
- R2 with context;
- residual diagnostics.

Counts:
- deviance/log-likelihood family metrics;
- MAE/RMSE as interpretable supplements;
- over-dispersion diagnostics.

Classification:
- precision/recall/F1;
- ROC-AUC or PR-AUC where appropriate;
- Brier score;
- calibration error/curve;
- class support.

Forecasting:
- MAE;
- RMSE;
- sMAPE;
- MASE;
- bias;
- prediction-interval coverage;
- interval width/sharpness;
- performance by forecast horizon.

No single metric automatically controls promotion.

## 10. Explainability acceptance

A model is not production-ready if its result cannot be presented with explanation appropriate to its risk and use.

Classical models:

- coefficients/effect estimates;
- confidence intervals;
- diagnostics;
- sample size.

Tree/boosting models:

- validated global feature importance;
- SHAP or equivalent contribution analysis where appropriate;
- partial dependence or response plots where useful.

UI and reports must state that feature contribution/association does not establish causality.

## 11. Safety and boundary evaluation

Both SIMPA and ORDO eval sets must include adversarial cases for:

- missing evidence;
- contradictory evidence;
- stale evidence;
- prompt injection inside documents;
- instructions embedded in retrieved content;
- cross-tenant and cross-product retrieval attempts;
- requests for unsupported causal conclusions;
- requests for unsupported forecasts;
- requests to fabricate a score/threshold;
- requests to bypass human review;
- requests to expose sensitive/source-inappropriate content.

SIMPA-specific safety cases include attempts to produce citizen-level eligibility/risk decisions.

ORDO-specific safety cases include attempts to turn user scenario assumptions into asserted forecast effects without a validated response model.

## 12. Champion/challenger registry contract

Every evaluated capability records:

```json
{
  "capability_key": "...",
  "domain": "SIMPA|ORDO|shared",
  "model_name": "...",
  "model_version": "...",
  "model_checksum": "...",
  "role": "...",
  "eval_dataset": "...",
  "eval_version": "...",
  "methodology_version": "...",
  "prompt_version": "...",
  "feature_version": "...",
  "metrics": {},
  "latency": {},
  "resource_profile": {},
  "approval_state": "candidate|challenger|champion|retired",
  "rollback_target": "...",
  "code_sha": "..."
}
```

Fields that do not apply remain explicit null/not-applicable rather than silently omitted when reproducibility needs them.

## 13. Promotion contract

A challenger may be promoted only when:

1. evaluation data/version is frozen;
2. the baseline/champion is evaluated on the same relevant set;
3. quality metrics meet capability-specific acceptance thresholds;
4. no safety/privacy/provenance blocker is introduced;
5. structured outputs remain contract-valid;
6. latency/resource cost is acceptable for target deployment;
7. human review of representative cases finds no unresolved blocker;
8. rollback target is defined;
9. promotion is recorded and versioned.

If a challenger improves one metric but materially worsens safety, provenance or institutional interpretability, it is not promoted.

## 14. Fallback policy

Fallback is a registered capability decision, not an arbitrary model name in application code.

Fallback must define:

- which failures trigger fallback;
- whether output semantics are equivalent;
- timeout/retry budget;
- whether human review becomes mandatory;
- whether the fallback has passed the same minimum safety/provenance contract.

No external provider fallback is permitted for sensitive local-only SIMPA requests unless a later explicit policy change authorizes it.

## 15. Production monitoring

After model promotion, monitor where applicable:

- request volume;
- latency;
- error/timeout rate;
- structured-output failures;
- retrieval quality proxies;
- human rejection/override rate;
- drift indicators;
- model/prompt/version usage;
- fallback use;
- cost/resource usage.

No online self-training or silent model replacement is authorized by this baseline.

## 16. Initial evaluation plan

The first controlled evaluation should compare the available local models without predeclaring a winner.

Text track:

- `qwen3:4b-instruct-2507-q4_K_M`
- `qwen2.5:7b-instruct`
- `gemma3:4b`
- `qwen3:1.7b-q4_K_M` for lightweight tasks

VLM/document track:

- `qwen3-vl:4b-instruct-q4_K_M`
- `qwen2.5vl:3b`
- `gemma3:4b` where multimodal capability is available in the deployed runtime

Embedding track after explicit installation/registration:

- compact multilingual candidate first;
- larger/cross-family challenger only if retrieval quality justifies it.

## 17. Non-decisions

This protocol does not:

- install a new model;
- declare any candidate production champion;
- validate a SIMPA/ORDO formula;
- authorize external AI providers for sensitive data;
- authorize online learning;
- authorize silent model promotion;
- replace human methodology approval.
