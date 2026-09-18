# ISI-25 Promotion Policy

Status: **FUTURE GATE DOCUMENTED; PROMOTION EXECUTION / WINNER SELECTION NOT IMPLEMENTED IN ISI-25A**

## Fail-closed rule

ISI-25A provides lifecycle vocabulary and evidence persistence but exposes no operation that selects a winner or promotes a registration to `champion`. Candidate/challenger registration and retirement do not change production deployment. A human review record cannot promote a model. No runtime/server model is installed, activated, replaced or rolled back by this foundation.

Promotion belongs to ISI-25B and may be considered only after a separate owner-approved implementation defines capability-specific evaluator behavior and acceptance thresholds.

## Mandatory future promotion evidence

A future promotion decision must require all of the following:

1. a frozen, versioned evaluation dataset with immutable case hash and manifest fingerprint;
2. candidate and registered baseline evaluated on the same relevant dataset/methodology/prompt/feature/policy identities;
3. capability-appropriate quality evidence and explicitly approved thresholds, never a generic winner score;
4. safety, privacy, namespace-isolation, sensitivity and provenance acceptance with no new blocker;
5. structured-output acceptance where applicable;
6. faithful explanation/XAI support, with unsupported confidence, calibration, attribution or feature importance reported unavailable;
7. latency/resource/failure evidence appropriate to the intended deployment;
8. immutable run/result fingerprints and code/environment provenance;
9. final human-review evidence from authorized membership identities with no unresolved blocker;
10. an explicit registered rollback identity and operational rollback plan;
11. explicit owner approval where methodology or institutional output changes materially.

Improvement on one metric cannot compensate for worse safety, privacy, provenance, institutional interpretability or domain-boundary compliance. External benchmarks do not replace ISI-specific evidence.

## Capability and product separation

Promotion is capability-specific. Statistical/ML, embedding, LLM and VLM registrations are not interchangeable, and one model need not be champion across roles. SIMPA and ORDO evaluation, methodology, prompts, private namespaces and decision semantics remain separate even when infrastructure is shared.

Sensitive SIMPA requests remain local-only. No fallback or promotion may authorize an external provider contrary to policy. ORDO promotion can never introduce automatic forecast-family selection/fallback, scenario impact estimation, causal claims, rankings or policy recommendations without separately accepted domain methodology.

The ISI-25A fallback graph is persistence/contract evidence only. Its `requires_human_review` and semantic-equivalence declarations do not activate cross-model execution. ISI-25B must bind execution to an unambiguous capability/registration and enforce those declarations before any fallback can become executable; until then runtime uses the selected/default model only.

## Rollback prerequisite

Before a future promotion can be executed, the candidate must have a governed rollback target whose identity/checksum is immutable and whose compatibility has been evaluated. The prompt registry similarly records rollback targets without changing the active prompt. ISI-25A registration of rollback identity is evidence only; production rollback execution is not implemented.

## Deferred ISI-25B implementation

ISI-25B must define capability-bound fallback execution and its review/semantic gates, evaluator engines, comparison logic, deterministic promotion criteria, approval transaction/audit behavior, circuit-breaker and drift behavior, and the exact rollback execution contract. Until that slice is accepted, `champion_promotion_requires_isi_25b_evaluation_and_approval_evidence` is the stable fail-closed outcome and no current permanent champion exists.
