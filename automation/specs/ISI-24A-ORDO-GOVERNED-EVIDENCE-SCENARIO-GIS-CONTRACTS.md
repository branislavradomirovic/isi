# ISI-24A - ORDO Governed Evidence, Scenario and GIS Contracts

## Baseline

Immutable implementation baseline:

`3894f5d4ce9b78abc39f9a565fecf83bc2ce7a73`

Accepted baseline tree:

`29c84c2bac1251af6e18c0a9dbccc6c52e69a97a`

Accepted baseline CI:

`ISI required acceptance` run #84 / `35084716444` / `completed` / `success` on the exact baseline SHA.

ISI-23 is complete and CI-verified. ISI-24A is the first governed ORDO production-methodology slice.

## R1 recovery classification

The first ISI-24A implementation runner stopped before governance/test completion because its status-ledger parser expected a non-existent `| Phase |` table header. The actual immutable baseline uses `| Order | Task | Live status |`. This is a package/harness defect, not an ORDO implementation defect.

R1 is a narrow recovery. It MUST begin only from the exact deterministic eight-path partial postimage produced by the failed R0 run, must verify those bytes from the immutable baseline before continuing, and must not stage, commit, push, reset, checkout or contact the production server.

R1 also closes two defects found during recovery review before another expensive acceptance run:

- canonical scenario snapshot hashing must be implemented explicitly rather than calling an undefined helper;
- scenario input identities must reflect the actual governed analytical-source keys (`artifact_id`, `dataset_contract_version_id`, `resolved_snapshot_id`) rather than non-existent keys.

R1 also preserves historical truth: pre-24A scenario-assessment rows MUST NOT be falsely relabeled as having been created under `ORDO-SCENARIO-CONTRACT-v1`. Migration defaults/backfill must distinguish legacy rows from newly created v1 rows.

## Scope

ISI-24A SHALL:

1. add a tenant/workspace-scoped governed reference-evidence registry;
2. use explicit `draft -> proposed -> validated -> retired` lifecycle transitions with no automatic promotion;
3. pin source identity/version plus artifact/content SHA-256 and validity/provenance metadata;
4. add a GIS-ready spatial-unit registry with boundary source/version, geometry identity, CRS, artifact SHA-256, validity and provenance;
5. preserve the existing ORDO scenario evidence-only assessment and strengthen it with an explicit versioned scenario contract;
6. persist scenario input identities, input snapshot fingerprint, limitations, uncertainty semantics and human-review state;
7. preserve `forecast_performed = false`, non-causal interpretation and human review;
8. keep all existing ORDO API/UI/reporting behavior backward compatible;
9. synchronize governance so ISI-23 is verified and ISI-24A is the current slice;
10. update the canonical SYSTEM INVENTORY for the new independently governed ORDO reference-evidence and spatial-unit entities and the strengthened scenario-contract authority.

## Required reference-evidence contract

Each governed evidence row SHALL expose:

- organization/workspace identity;
- stable `evidence_key`;
- optional ORDO indicator binding;
- optional core data-source-version binding;
- source identity and source version;
- external identity;
- artifact SHA-256 and content SHA-256;
- `valid_from` / `valid_to`;
- lifecycle state;
- structured provenance lineage;
- human lifecycle actors/timestamps and notes.

Promotion to `proposed` or `validated` SHALL require non-empty source identity/version, both 64-hex fingerprints and provenance lineage. Lifecycle transitions cannot skip states and cannot be reversed. Every lifecycle transition requires an explicit human actor; no automatic validation/promotion is allowed.

## GIS-ready spatial-unit contract

Each governed spatial unit SHALL expose:

- organization/workspace identity;
- stable spatial-unit key and type;
- human-readable name;
- boundary source and boundary version;
- geometry identity;
- CRS;
- boundary artifact SHA-256;
- validity interval;
- provenance;
- explicit lifecycle state and human lifecycle trace.

24A establishes identity/provenance contracts only. It does not implement geometry storage, spatial joins or spatial statistics.

## Scenario contract

Every newly created scenario assessment SHALL persist:

- `scenario_contract_version = ORDO-SCENARIO-CONTRACT-v1`;
- `methodology_key = ordo_evidence_readiness_v1`;
- `methodology_version = 1`;
- input reference identities derived from the actual governed analytical-source binding;
- a canonical SHA-256 of the complete input analytical snapshot;
- limitations;
- `uncertainty_semantics = not_applicable_scenario_not_forecast`;
- `human_review_state` (`pending`, `reviewed`, or `rejected`).

The canonical snapshot fingerprint SHALL be SHA-256 over deterministic UTF-8 JSON with sorted keys and compact separators. No runtime-dependent or unordered serialization is acceptable.

The structured assessment payload SHALL explicitly encode:

- `scenario_is_forecast = false`;
- `causal_claim = false`;
- `automatic_policy_recommendation = false`.

Existing legacy scenario-assessment rows are migration-compatible but MUST remain historically truthful. They may retain an empty input snapshot fingerprint and MUST use explicit legacy contract/methodology identity rather than being falsely backfilled as v1-created rows. Their human-review state SHALL be backfilled from the pre-existing assessment status where applicable. New 24A assessments MUST persist a 64-hex fingerprint and the v1 contract identity.

## Canonical system inventory impact

The MasterPlan SYSTEM INVENTORY SHALL be updated in this same candidate:

- add `INV-C33` for governed ORDO reference evidence;
- add `INV-C34` for governed ORDO spatial-unit/boundary identity;
- strengthen `INV-C28` to include the persisted non-forecast scenario contract;
- strengthen `INV-M08` so ISI-24A tests become part of ORDO test authority.

No new customer-facing surface is introduced by 24A, so ORDO Help/User Guide/XAI completion remains owned by 24D.

## Non-goals

ISI-24A MUST NOT add:

- forecast execution;
- ARIMA or ETS;
- automatic model selection;
- rolling-origin/backtesting execution;
- causal/policy-effect estimation;
- citizen scoring or eligibility automation;
- automatic policy recommendations;
- invented weights or thresholds;
- full GIS geometry/spatial-join engine;
- ORDO Help/User Guide completion;
- ORDO XAI completion;
- shared AI/MLOps promotion logic;
- API or Streamlit routes for the new registries;
- reporting-adapter changes;
- dependency or workflow changes;
- production-server changes.

No automatic policy recommendation is introduced or authorized by ISI-24A.

## Exact mutable surface

Exactly these 19 repository paths may change:

1. `automation/STATUS.md`
2. `automation/specs/ISI-24A-ORDO-GOVERNED-EVIDENCE-SCENARIO-GIS-CONTRACTS.md`
3. `automation/tasks.json`
4. `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
5. `migrations/versions/20260916_0030_ordo_governed_evidence_gis_contracts.py`
6. `src/domains/ordo/models.py`
7. `src/domains/ordo/schemas.py`
8. `src/domains/ordo/service.py`
9. `src/domains/ordo/analytics_models.py`
10. `src/domains/ordo/analytics_schemas.py`
11. `src/domains/ordo/analytics_service.py`
12. `tests/test_isi_17_harness_contract.py`
13. `tests/test_isi_24a_reference_evidence_contract.py`
14. `tests/test_isi_24a_reference_lifecycle.py`
15. `tests/test_isi_24a_scenario_contract.py`
16. `tests/test_isi_24a_gis_contract.py`
17. `tests/test_isi_24a_governance_contract.py`
18. `tests/test_isi_23c_migration_contract.py`
19. `tests/test_isi_23e_simpa_closeout.py`

The two ISI-23 historical test files are a recovery-only compatibility expansion: they may change only to stop freezing mutable global Alembic/current-phase state while preserving their own immutable accepted-slice contracts.

No API, Streamlit, reporting-adapter, dependency-lock, workflow or server path is mutable in 24A.

## Acceptance

A successful final 24A candidate run MUST prove:

- exact immutable baseline HEAD and `origin/main`;
- exact eight-path R0 partial postimage before recovery, reconstructed independently from baseline bytes and the original R0 deterministic transformer;
- no staged content before, during or after recovery;
- exact final 19-path dirty surface;
- reference evidence lifecycle and SHA/provenance contract;
- GIS boundary/version/CRS/geometry/provenance contract;
- scenario version/input-snapshot/non-forecast/non-causal contract;
- deterministic canonical scenario snapshot hash;
- actual governed analytical-source identity extraction;
- truthful legacy scenario migration semantics;
- canonical SYSTEM INVENTORY synchronization;
- backward compatibility with ISI-10/11/12 ORDO/reporting tests;
- governance compatibility;
- historical ISI-23C/23E tests assert immutable own-slice contracts without freezing the mutable global Alembic head or current-phase ledger;
- policy pass;
- Alembic offline migration pass;
- full Python regression pass;
- native PostgreSQL pass;
- live migration pass;
- `git diff --check` pass;
- stable candidate manifest across independent analyzer runs;
- no Codex, staging, commit, push or production-server mutation.

## Phase boundary

24B owns spatial processing and statistical/time-series contracts. 24C owns forecasting/backtesting/intervals/diagnostics/`NOT_ESTIMATED`. 24D owns ORDO Help/User Guide/XAI. 24E owns ORDO final closeout.
