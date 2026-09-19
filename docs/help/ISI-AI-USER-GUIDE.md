# ISI Shared AI Evaluation and Promotion User Guide

Status: ISI-25B shared-AI guide. This guide does not claim that the remaining ISI-27 shared Help gaps are complete.

## Purpose and when to use each function

The registry records a model or deterministic artifact for one product scope, capability and family. Use it before governed evaluation or bound execution. A runtime `AIModel` says how a provider can be called; a model registration is the immutable governance identity and fingerprint for what capability that runtime or artifact represents.

Evaluation uses explicit expected, gold or evidence inputs. The two frozen `SIMPA-EVAL-v1` and `ORDO-EVAL-v1` manifests test the foundation only and can never promote a model. Promotion work uses a separately registered, frozen, approved, hash-addressed benchmark and a versioned capability threshold profile. Do not present a synthetic test benchmark as human-approved domain gold.

Promotion preview compares candidate and baseline on the same benchmark without an aggregate winner score. Promotion execution changes registry/runtime governance only after all hard gates and human approval pass. It does not install a model, change Ollama, deploy code or rewrite the legacy default runtime model. Rollback is a separate explicit, reasoned, audited action.

Fallback is used only for an explicitly registration-bound job after a registered trigger. An unbound legacy job remains selected-model-only. Circuit state prevents repeated direct calls after the configured failure threshold. Drift evaluation compares explicit observed/reference windows on demand; no scheduler, online learning or silent replacement exists.

## Roles and permissions

- `ai.run`: ordinary scoped AI execution.
- `analysis.run`: execute evaluation evidence and create scoped drift snapshots.
- `analysis.read`: inspect registrations, evaluation, runtime, drift and XAI status.
- `report.publish`: final evaluation review/sign-off.
- Platform administrator after normal organization/product/workspace resolution: register global benchmarks and thresholds and create promotion governance decisions.
- Promotion, rollback and circuit reset require both platform-admin authority and `report.publish`.

No `ai.manage` permission exists. UI visibility never replaces backend authorization.

## Conceptual workflow

1. Resolve the authorized organization, SIMPA or ORDO product, and workspace.
2. Register an immutable capability/model identity. Confirm product scope, family, runtime identity, version, provenance and fingerprint.
3. Register a separate promotion benchmark with stable case IDs, explicit evidence/gold metadata, privacy class, cases SHA-256, manifest fingerprint, frozen state and approval owner.
4. Register a threshold version with metric directions, absolute thresholds, candidate-versus-baseline deltas, non-compensable safety/provenance/structured-output gates, resource limits and circuit policy.
5. Run candidate and baseline on the same benchmark. Append typed metric, safety, provenance and evidence rows, then complete each run.
6. An authorized reviewer records a final `approved` review with evidence reference.
7. Preview promotion. Resolve every blocker; never average away a safety, privacy or provenance failure.
8. Execute only with the explicit owner-approval reference and compatible rollback registration.
9. Inspect champion, challenger, rollback, fallback, circuit and drift status. If rollback is required, supply a reason and evidence reference and execute it explicitly.

## States and interpretation

Registration lifecycle:

- `candidate`: registered for controlled evaluation.
- `challenger`: eligible comparator or former champion; not automatically active.
- `champion`: the one governed registration pinned for an exact product-scope/capability after promotion.
- `retired`: disabled for new governed use while historical evidence remains readable.

Benchmark and evaluation:

- A promotion benchmark must be `frozen` and `approved`; changing content under the same key/version is rejected.
- Runs move `created -> running -> completed|failed`. Terminal results have an immutable fingerprint.
- Metric rows state direction, support, evidence state and case/source references. `unavailable` or `not_applicable` is not zero.
- Review is `pending`, `approved`, `changes_requested` or `rejected`; only a final authorized `approved` review satisfies promotion.

Runtime:

- Circuit `closed` permits normal direct use; `open` blocks repeated direct use; after cooldown the next explicit request becomes a `half_open` probe; success closes and resets, failure opens again.
- Drift is `ok`, `warning`, `blocker` or `insufficient_evidence`. A blocker cannot silently train, replace or roll back a model.
- A successful fallback with `requires_human_review=true` ends `review_required` with `human_review_status=pending`, not ordinary success.

## Synthetic example

A platform administrator registers two synthetic SIMPA local LLM registrations for capability `simpa.evidence_summary`. A frozen synthetic promotion benchmark contains stable cases with supplied source references, but is clearly not production gold. The baseline and challenger runs both complete. The challenger improves grounded factuality by the required delta, satisfies structured-output and provenance gates, stays within latency limits, and has an approved final review. Promotion preview is eligible only after a compatible local rollback registration is recorded. With the owner reference, execution changes the governed champion. It neither downloads nor deploys either model.

If the challenger instead improves latency but fails a PII or prompt-injection case, preview is blocked. Latency cannot compensate for that safety failure.

## Common blockers and recovery

- `bound_model_registration_not_accessible`: use the exact enabled, non-retired registration visible to the selected product.
- `bound_registration_selected_model_mismatch`: the supplied runtime model and registration disagree; correct the request instead of guessing.
- No fallback: check exact source registration, trigger code, semantic-equivalence declaration, product/family match, target runtime, provider policy and circuit state.
- `foundation_fixture_cannot_be_promotion_benchmark`: register a new promotion-benchmark identity; never relabel a v1 foundation fixture.
- `required_metric_missing`, threshold/delta failure or non-compensable gate failure: add valid evidence or create a new run after correcting the underlying candidate. Do not weaken the threshold to hide a defect.
- `approved_final_evaluation_review_required`: obtain authorized representative-case review with an evidence reference.
- Open circuit: wait for the configured cooldown and make an explicit probe, or use the strongly authorized reasoned reset. There are no sleeps or background resets.
- `insufficient_evidence` drift/VLM/OCR state: provide the missing explicit reference evidence; never substitute a fabricated score.

## Security, privacy and methodology limits

Sensitive SIMPA remains local-only; fallback and promotion never override provider/data policy. Private SIMPA/ORDO and organization namespaces remain isolated. Benchmark manifests must contain no credentials or production secrets. AI output remains evidence-bounded decision support and requires institutional human responsibility.

MLOps does not define SIMPA formulas, weights, thresholds, citizen eligibility/risk or policy conclusions. It does not change ORDO scenario-versus-forecast truth: scenario `NOT_ESTIMATED` plus `NO_APPROVED_RESPONSE_MODEL` is intentional unestimation, `LEGACY_NOT_EVALUATED` remains history, and forecast-family selection/fallback or scenario-impact automation is not authorized.

## Provenance and XAI

The read model exposes product/capability, registration version and fingerprint, lifecycle, prompt/policy identity, benchmark/run/result fingerprints, source provenance, metric direction/support, structured-output status, fallback edge/attempt, review-required state, circuit/drift state, final human review and rollback identity. It distinguishes deterministic numerical authority from generative synthesis.

Confidence, probability, calibration, uncertainty, feature importance and SHAP/attribution are shown as `unavailable` unless the specific evaluated result supplies an approved semantic contract and evidence. The system never invents them.

## Explicit non-goals

There is no automatic deployment, model installation, online learning, self-training, automatic winner, generic aggregate score, silent fallback, silent rollback, silent replacement, background scheduler, external sensitive-SIMPA fallback, ORDO forecast-family fallback, automatic scenario impact, causal conclusion or policy/ranking authority.
