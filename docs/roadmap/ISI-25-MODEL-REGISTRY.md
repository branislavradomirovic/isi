# ISI-25 Model Registry Contract

Status: **ISI-25A ACCEPTED ON `f0047321ee4410522697144ecfa464087f1b83bc`; ISI-25B ACTIVE CANDIDATE**

## Purpose and authority

This document defines the shared lifecycle-identity layer added by ISI-25A. It extends the existing `AIModel`, `AIPrompt`, `AIPromptVersion`, `AIPolicyProfile`, `AIJob`, attempt, audit and embedding substrate. It does not replace the provider gateway, deterministic SIMPA/ORDO analytical authorities, or central RBAC.

The provider gateway remains the single provider invocation boundary. `AIModel` remains runtime/provider configuration. `AIModelRegistration` is the governance identity for a capability/artifact across `statistical_ml`, `embedding`, `llm` and `vlm` families, including artifacts that do not invoke a provider.

## Immutable registration identity

A registration fingerprint is SHA-256 over canonical UTF-8 JSON (`ensure_ascii=false`, sorted keys, compact separators) containing:

- capability key and `SHARED`/`SIMPA`/`ORDO` product scope;
- model family, governed model/artifact key, version and optional revision;
- optional runtime `AIModel` identity plus provider/runtime name;
- optional artifact URI and SHA-256 checksum;
- explicit provenance.

Lifecycle state, enabled state and retirement trace are not part of that immutable identity. A changed identity requires a new registration. Existing runtime models are not backfilled and are never silently designated champion.

The lifecycle vocabulary is `candidate`, `challenger`, `champion`, `retired`. ISI-25A allows creation of candidates/challengers and retirement. Any attempt to create or transition to `champion` fails closed with `champion_promotion_requires_isi_25b_evaluation_and_approval_evidence`. No permanent or hard-coded champion exists.

## Persisted fallback graph and 25A runtime boundary

Model substitution is never inferred by scanning enabled runtime models. Jobs without an explicit registration binding retain the accepted 25A selected/default-model-only behavior (`REQUIRED_COMPATIBILITY`). A 25B-bound job pins one exact source registration; executable fallback resolves edges from that identity only, in priority order, and enforces trigger, semantic-equivalence, capability/family/product, provider/data-policy, runtime-enabled, circuit and human-review gates. The earlier helper that selected a first-created registration from `runtime_model_id` is `REMOVE_BEFORE_NEXT_SLICE` and is no longer used or exposed.

The fallback graph remains governed foundation evidence: edges require valid compatible registrations, forbid self-reference/cycles and persist deterministic priority, trigger codes, semantic-equivalence declaration, human-review requirement, provenance, actor, timestamp and fingerprint. The `semantically_equivalent` and `requires_human_review` declarations are contract metadata, not executable 25A gates, and no route or runtime path treats an edge as production-executable.

Capability-bound cross-model activation is deferred to ISI-25B. That execution contract must bind each job/evaluation to one unambiguous capability/registration and enforce trigger, semantic-equivalence, human-review and provider/data-policy gates. This avoids choosing implicitly when one runtime model has multiple capability registrations. Sensitive SIMPA remains local-only, and ORDO forecast-family fallback remains forbidden.

## Prompt rollback identity

`AIPromptVersion` content, version and checksum remain immutable execution identity. A governed rollback target is a separate persisted relation from one version to an earlier version of the same prompt. Self-targets, cross-prompt targets and non-prior targets are rejected. The relation pins both checksums plus actor, provenance, timestamp and fingerprint.

Registering a target does not rewrite a prompt version, change which version is active, or execute production rollback. Rollback execution remains outside ISI-25A.

## Evaluation persistence foundation

`AIEvaluationDataset`, `AIEvaluationRun`, `AIEvaluationResult` and `AIEvaluationReview` persist future evaluator inputs/evidence:

- frozen dataset key/version/case hash/manifest fingerprint;
- scoped run identity, model registration, optional baseline, prompt and policy identity;
- input/provenance and environment/config fingerprints;
- typed deterministic JSON evidence/result rows while a run is mutable;
- immutable terminal result fingerprint;
- reviewer membership, bounded decision, notes/evidence reference and immutable final trace.

`SIMPA-EVAL-v1` and `ORDO-EVAL-v1` are deterministic synthetic, non-production `CONTRACT/FIXTURE` baselines. Their `foundation_only_not_production_promotion_evidence=true` marker is mandatory. They prove loader, hashing and persistence contracts only; they are not model-quality evidence.

## Security and domain boundaries

All scoped API operations resolve organization, product and workspace before mutation. Because registrations, fallback relations, prompt rollback targets and evaluation datasets are global/shared records, their mutation is platform-admin-only using existing `User.is_platform_admin` authority after normal scope resolution. Evaluation execution-record mutation uses `analysis.run`; inspection, including review inspection, uses `analysis.read`; evaluation review writes use existing `report.publish` sign-off authority; ordinary inference remains `ai.run`. No new permission taxonomy exists.

The registry is not numerical or methodology authority. It cannot alter SIMPA calculations or ORDO 24C/24E semantics. In particular, scenario is not forecast, scenario `NOT_ESTIMATED` with `NO_APPROVED_RESPONSE_MODEL` is not zero/failure, `LEGACY_NOT_EVALUATED` remains historical truth, and ORDO forecast families never gain automatic selection or fallback through this registry.

## ISI-25A / ISI-25B boundary

ISI-25A implements identity, provenance, persisted fallback-graph evidence, rollback-target identity, frozen fixture contracts and evaluation persistence only. Runtime remains selected/default-model-only.

ISI-25B adds capability/registration-bound fallback activation, deterministic evaluator engines, separate promotion benchmarks, capability thresholds, evidence-gated promotion and rollback, circuit state, on-demand drift snapshots and shared AI XAI/read models. It installs or deploys no model and preselects no winner. `SIMPA-EVAL-v1` and `ORDO-EVAL-v1` remain `REQUIRED_COMPATIBILITY` foundation fixtures forever and cannot satisfy promotion evidence. No application scheduler is added (`REQUIRED_COMPATIBILITY`).

Historical 25A tests that froze current-global selected-only behavior are `REMOVE_BEFORE_NEXT_SLICE`; they now assert the historical unbound-job contract while 25B tests own current bound execution. F08/global shared Help beyond AI evaluation/provenance/promotion/fallback remains `REMOVE_IN_NAMED_PHASE(ISI-27)`.
