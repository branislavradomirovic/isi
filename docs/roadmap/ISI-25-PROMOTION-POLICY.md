# ISI-25 Promotion Policy

Status: **ISI-25B EVIDENCE-GATED REGISTRY/RUNTIME PROMOTION CANDIDATE**

## Fail-closed rule

Promotion is a registry/runtime-governance transaction only. It never installs, downloads, deploys or enables provider software, never rewrites the legacy default runtime model, and never mutates server configuration. There is no preselected or permanent champion and no generic aggregate winner score.

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

## 25B execution and rollback

Preview persists deterministic per-metric comparisons and non-compensable blockers. Execution additionally requires platform-admin authority, `report.publish`, an eligible immutable decision and an explicit owner-approval reference. The candidate becomes the sole enabled champion for its exact product scope/capability, the prior champion becomes challenger, and runtime state pins champion, rollback and circuit policy atomically.

Rollback is explicit, reasoned, evidence-referenced and audited under the same authority. It restores only the recorded compatible enabled registration. It is never silent and never installs or deploys a model. Circuit and on-demand drift evidence may block use or promotion, but never causes online training, silent replacement or automatic rollback.
