# ISI-25 Model Registry Contract

Status: **ISI-25A FOUNDATION IMPLEMENTED CANDIDATE; ISI-25B REQUIRED**

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

Model substitution is not inferred by scanning enabled runtime models. ISI-25A runtime execution fails closed to the explicitly selected/default runtime model only, even when a persisted fallback edge exists. No different runtime model is attempted in 25A.

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

ISI-25B remains required for capability/registration-bound fallback activation with enforced edge review/semantic gates, evaluator engines, nDCG/MRR/Recall and other scoring, factuality/Serbian/VLM/adversarial evaluation, threshold definition, baseline comparison, winner selection, champion promotion, circuit breaker, drift jobs, operational dashboards and production rollback execution. No model is production-promoted in ISI-25A.
