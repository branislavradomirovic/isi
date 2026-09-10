# ISI-19 — Backup, Restore & Disaster Recovery Automation

## Status
`SPEC_READY`

## Baseline
`b0487d8e9187c6b06efe5fab463875f8d989042c` (`main`, ISI-18 merged; post-merge CI run #47 / `34485496540` successful).

## Dependencies
- `ISI-18-OBSERVABILITY-OPERATIONAL-DIAGNOSTICS` merged and post-merge CI verified.
- Existing ISI-17 deterministic CI, architecture/security, native PostgreSQL, migration, Compose, supply-chain and build gates remain binding.
- No production credentials, production backup media or current-server access are required.

## Objective
Provide deterministic, integrity-verifiable and CI-rehearsed backup/restore/disaster-recovery capability for the ISI platform's PostgreSQL data and application-managed object storage without touching the current production server.

## Existing architecture
- PostgreSQL 17 is the relational data platform.
- Application-managed binary/object data uses the existing `StorageBackend` abstraction with local filesystem and S3-compatible implementations.
- Redis/RQ is operational queue infrastructure and is not an authoritative durable data source for recovery.
- FastAPI, Streamlit, PostgreSQL, Redis/RQ, S3-compatible storage and the shared AI gateway remain unchanged unless separately owner-approved.
- ISI is the institutional platform; SIMPA and ORDO are the only current domain applications.

## Locked boundaries
- No COSMOS runtime, application, domain, route, tenant, namespace, product or menu layer.
- No SSH/SCP, deployment, DNS/ingress, production SMTP, production secrets/data, production monitoring host or server Ollama action.
- No production backup creation, deletion, retention mutation, restore or recovery rehearsal.
- Recovery tooling must be fail-closed and operate only on explicitly supplied non-production/synthetic targets in this task.
- SIMPA and ORDO tenant/domain isolation must survive backup and restore unchanged.

## Required behavior
1. Introduce a versioned recovery manifest format containing at minimum manifest schema version, backup identifier, creation timestamp, source descriptor, artifact inventory, byte size, SHA-256 digest, tool/schema metadata and verification state.
2. Implement PostgreSQL logical-backup creation and restore tooling compatible with PostgreSQL 17. The implementation may use a pinned PostgreSQL 17 client or a pinned PostgreSQL 17 container, but must not depend on a production host.
3. PostgreSQL restore must support a fresh empty target and fail closed on command failure, incompatible manifest metadata, missing artifact, digest mismatch or restore verification failure.
4. Implement object-storage backup/restore for application-managed storage using explicit scoped keys. CI recovery rehearsal must cover the local storage backend; the S3-compatible backend must have deterministic adapter/contract coverage and may additionally use a synthetic MinIO-compatible fixture if introduced without production coupling.
5. Preserve object keys and byte content exactly across backup/restore, with SHA-256 verification before accepting restored state.
6. Add optional encryption hooks as an interface/command boundary. The default CI path must not require a production KMS, vault or secret-manager. Unencrypted synthetic fixtures are permitted only when the manifest explicitly records encryption state.
7. Add retention-policy hooks that calculate eligible backup sets without deleting anything by default. Any destructive delete action must require an explicit non-production opt-in and must be separately testable.
8. Provide deterministic restore verification that checks PostgreSQL migration head/schema viability, selected relational invariants, object inventory/digests and SIMPA/ORDO isolation contracts.
9. Provide a synthetic full recovery rehearsal that creates non-production fixture data, backs up PostgreSQL and object storage, destroys only the synthetic recovery target, restores into a fresh target, verifies integrity and exits non-zero on any mismatch.
10. Recovery rehearsal must be idempotent, non-interactive, cleanup its own synthetic resources and never contact the current server.
11. Document rollback-safe migration/recovery ordering, preflight checks, abort conditions and evidence capture.
12. Document proposed RPO/RTO targets by deployment class. They must be explicitly labelled `PROPOSED` / `NOT SERVER-VALIDATED` until owner acceptance and ISI-28 evidence.
13. Add machine-readable ISI-19 evidence summarizing baseline/head, CI run, recovery rehearsal results, artifact digests, review state and `DEFERRED_SERVER_VERIFICATION`.
14. Synchronize `automation/tasks.json`, `automation/STATUS.md`, the PR body and `automation/evidence/ISI-19/` as the task changes state.

## Impact
- Database/migrations: no application schema change is required unless a narrowly justified recovery-metadata table is introduced; any such migration must pass existing Alembic gates and native PostgreSQL tests.
- API: no public recovery API is required. Any diagnostic exposure must be non-secret and read-only.
- UI: no end-user recovery UI is required.
- Workers: no production backup scheduler is required; reusable non-production-safe command/service boundaries may be introduced.
- Configuration: only non-secret recovery configuration with safe defaults; no production credential material.

## Security and privacy
- Backup artifacts are sensitive by default and must not be written to logs.
- Manifests may contain identifiers and hashes required for recovery, but no passwords, tokens, database URLs with credentials, raw authorization headers or application payload excerpts.
- Recovery commands must reject obviously production-marked targets unless a later explicitly approved server phase introduces a controlled override.
- Tests must prove digest mismatch/corruption is detected and sensitive values are not emitted in logs/evidence.
- Backup/restore must not weaken tenant, product, entitlement or SIMPA/ORDO isolation controls.

## Tests
- Manifest schema/version and deterministic serialization tests.
- SHA-256 and corruption-detection tests.
- PostgreSQL command construction and failure-path tests.
- Native PostgreSQL 17 backup/restore integration test on synthetic data.
- Local object-storage backup/restore round-trip tests.
- S3-compatible storage recovery adapter contract tests without real credentials.
- Retention dry-run/non-destructive default tests.
- Encryption-hook state/metadata tests.
- Synthetic full recovery rehearsal with integrity assertions.
- Regression coverage for SIMPA/ORDO isolation after recovery.
- Server-freeze/static-policy tests proving no production/server command path was added to CI.
- Existing tests must not be weakened, deleted, skipped or xfailed to obtain green status.

## Exact acceptance commands
```bash
python -m tools.ci.policy_check
python -m pytest -q tests/test_isi_19_backup_restore_contract.py tests/test_isi_19_recovery_rehearsal.py
tools/ci/isi19_recovery_rehearsal.sh
tools/ci/run_isi17_acceptance.sh
git diff --check
```

The authoritative GitHub Actions run on the exact final PR head must also pass every blocking job inherited from ISI-17, including native PostgreSQL 17, migrations, Compose, supply-chain, build and aggregate acceptance.

## Evidence
Required under `automation/evidence/ISI-19/`:
- `acceptance-summary.md`
- `results.json`
- recovery-manifest example using synthetic identifiers only
- full-recovery rehearsal summary
- RPO/RTO and recovery-policy status
- baseline/final SHA and exact CI run ID/number
- reviewer state
- warnings/deferrals
- explicit `DEFERRED_SERVER_VERIFICATION`

## Non-goals
- Production/server backup execution.
- Production restore or disaster declaration.
- Production storage lifecycle deletion.
- DNS/ingress/SMTP/secret-manager/server-Ollama changes.
- Replacing PostgreSQL, Redis/RQ or the existing storage abstraction.
- Treating Redis/RQ transient queue state as an authoritative recovery dataset.

## Forbidden changes
- No SSH/SCP or current-server contact.
- No production credentials, production data or production backup media in repository, CI, logs or evidence.
- No weakening of ISI-17 CI/security gates.
- No destructive retention behavior enabled by default.
- No cross-tenant or SIMPA/ORDO data mixing during backup/restore.
- No claim of `SERVER_VERIFIED` or production-tested RPO/RTO before ISI-28.

## Completion definition
`IMPLEMENTED` requires the specified recovery code, tests, documentation and evidence templates to exist and the task-specific local/CI-compatible acceptance paths to pass.

`CI_VERIFIED` requires the complete blocking GitHub Actions workflow to pass on the exact synchronized final PR head, including the native PostgreSQL recovery path and aggregate acceptance.

`REVIEW_VERIFIED` requires independent review of the exact CI-verified head with no unresolved technical blocker.

`MERGED` requires the accepted PR to be merged to `main` and the post-merge main CI to pass before ISI-20 begins.

## Deferred server verification
`DEFERRED_SERVER_VERIFICATION` — current-server backup, restore, capacity, RPO/RTO and operational recovery verification are intentionally deferred to ISI-28 and require fresh explicit owner approval.