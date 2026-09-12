# ISI-21 Data Governance & Privacy Controls — As-Built Completion Contract

State: **COMPLETE / CI_VERIFIED**.

## Historical note

This document is an **as-built completion contract authored during ISI-21 closeout after implementation and exact-main CI acceptance**. It records the delivered and verified behavior; it does not claim that a dedicated ISI-21 task specification existed before implementation.

The owner-facing roadmap and task registry were stale while ISI-21A, ISI-21B, and ISI-21C were implemented through controlled direct-main gates. This closeout makes repository bookkeeping match canonical history without changing runtime behavior.

## Canonical implementation chain

Baseline immediately before ISI-21A: `2ce1e5f54aa71beb0275553b427a0f11e0822612`.

- ISI-21A — `012c2f0ce0c04e92dc8240e12fab9a0005eef376` — `Implement ISI-21A data governance foundation`.
- ISI-21B — `5421e65066ee1dfe841a0d4fcc96d95159859848` — `Implement ISI-21B governance privacy enforcement`.
- ISI-21B native PostgreSQL fixture repair — `dbe301dfe5db9743e9f3dfb8d605b89953de1949` — `Fix ISI-21B native PostgreSQL reference catalog fixture`.
- ISI-21C — `ac42601dc5cb67bf98603022febe8de276844ca3` — `Implement ISI-21C analytical data governance`.

Canonical ISI-21 implementation tree after ISI-21C: `6f7744c72b877b7808e22a0412084cdfca6aec03`.

## Migration chain

ISI-21 extends the single Alembic chain with:

- `20260912_0017` — data governance and retention foundation;
- `20260912_0018` — governed retention, purge, anonymization, and export enforcement;
- `20260912_0019` — governed analytical datasets, snapshots, features, and typed lineage.

`20260912_0018` remains historical after `20260912_0019`; tests must verify history without pinning an obsolete head.

## Delivered scope

### ISI-21A — governance foundation

The shared data platform gained conservative governance primitives for source data, including classification, privacy category, processing purpose, data-owner/steward references, versioned retention policy/state, AI-use policy, export policy, governance state/revision, and safe backfill defaults for existing source/version records.

Defaults are fail-closed: unclassified/unknown data is not silently treated as approved for AI use or export.

### ISI-21B — privacy and retention enforcement

The platform gained governed retention/hold/purge state transitions, content-state handling, anonymization records and human review state, controlled export permissions and assurance, immutable export manifests, purge-driven governance invalidation, storage-delete safety, and bounded privacy-safe audit behavior.

Authorization and tenant/workspace/product scope checks remain server-side. Export capability is explicit; sensitive flows fail closed and do not expose storage internals as an authorization oracle.

### ISI-21C — analytical data governance

The platform gained governed analytical dataset identities, versioned snapshots, feature registry/versions, typed source-to-snapshot and snapshot-to-feature lineage, lifecycle/revision/fingerprint controls, invalidation state, inherited classification/privacy/AI-use restrictions, and bounded AI-eligibility evaluation.

Analytical service boundaries reuse canonical scope validation and prevent cross-organization, cross-workspace, and cross-product consumption. SIMPA lineage cannot be silently consumed in ORDO scope and vice versa.

AI eligibility is fail-closed and provenance-aware. A training policy that requires separate approval remains separate approval; ISI-21 does not promote it into automatic model-training authorization.

## Locked architectural and safety boundaries

- ISI remains the institutional platform; SIMPA and ORDO are the only current domain applications.
- No COSMOS runtime/application/domain layer is introduced.
- FastAPI + Streamlit + PostgreSQL + Redis/RQ + S3-compatible storage + shared AI gateway remain the baseline architecture unless a later owner-approved ADR changes it.
- Numerical analytics remain deterministic/versioned statistical or ML computation, not silent LLM arithmetic.
- RAG/document AI must retain provenance and tenant/product namespace isolation.
- LLM/VLM behavior remains bounded synthesis/explanation and human-reviewed decision support.
- SIMPA remains aggregate/system-level and must not automate citizen eligibility, benefit, or risk decisions.
- ORDO forecast and scenario semantics remain distinct; unsupported scenario impact remains `NOT_ESTIMATED`.
- No server deployment, DNS/ingress mutation, production SMTP/secrets/data mutation, or server Ollama mutation is part of ISI-21.

## Local review and acceptance

ISI-21C was validated through a locked 17-file implementation surface. The corrected H1 runner passed exact-surface, byte-stability, policy, focused migration, focused ISI-21C, ISI-21A/21B regression, shared-data regression, architecture/security regression, offline migration, complete non-native pytest, and diff checks.

The independent R2 analyzer then passed exact 17-file surface, locked R1 candidate, exact one-file historical migration-test repair, semantic contract, policy, focused suites, offline migration, full non-native pytest, and final repository guards.

A final one-byte EOF whitespace normalization in `tests/test_isi_21c_migration_contract.py` was proven byte-for-byte, re-staged alone, passed `git diff --cached --check`, and passed the focused migration contract before owner approval.

The owner explicitly approved the exact 17-file ISI-21C commit/push. The resulting commit was `ac42601dc5cb67bf98603022febe8de276844ca3` with parent `dbe301dfe5db9743e9f3dfb8d605b89953de1949` and tree `6f7744c72b877b7808e22a0412084cdfca6aec03`.

## Exact-main CI acceptance

Authoritative GitHub Actions: `ISI required acceptance` run #64, run ID `34714098565`, event `push`, exact head SHA `ac42601dc5cb67bf98603022febe8de276844ca3`, conclusion `success`.

All blocking jobs passed: policy, quality, tests, architecture-security, migration, native-postgres, compose, supply-chain, build, and aggregate acceptance. Migration passed both offline and live checks. Supply-chain passed dependency audit, Python SAST, and secret scan.

JUnit artifacts from the authoritative run record:

- full pytest: 448 tests, 0 failures, 0 errors, 24 skipped;
- native PostgreSQL: 26 tests, 0 failures, 0 errors, 1 skipped.

## Deferred checks and non-claims

Server/live-host verification and deployment are `DEFERRED_SERVER_VERIFICATION` and are not implied by ISI-21 completion. No production data migration or live-host mutation was performed as part of this task.

`StarletteDeprecationWarning` for the current TestClient/httpx compatibility layer was observed during local tests and is non-blocking for ISI-21; dependency modernization is separate work and must not be silently mixed into this closeout.

## Next task

`ISI-22-INDUSTRIAL-DATA-PLATFORM` remains `PLANNED` and is the next implementation task only after this closeout bookkeeping/evidence change itself is reviewed, owner-approved, committed/pushed, and exact-head CI verified.
