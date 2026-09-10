# ISI-19 Recovery Runbook

Status: **PROPOSED / NOT SERVER-VALIDATED**

This runbook defines the repository-side recovery contract for the ISI platform. It is intentionally limited to non-production and synthetic recovery verification until ISI-28 is explicitly approved by the owner.

## Recovery scope

Authoritative durable recovery scope is PostgreSQL plus application-managed object storage. Redis/RQ queue state is transient operational state and is not restored as authoritative data. ISI remains the institutional platform; SIMPA and ORDO remain separate domain products and must preserve their existing tenant/product/workspace boundaries after recovery.

## Proposed service targets

These targets are planning values only and have not been validated against the current server:

| Deployment class | Proposed RPO | Proposed RTO | Validation state |
|---|---:|---:|---|
| Development / CI | 24 hours | 4 hours | CI-rehearsed only |
| Staging | 12 hours | 2 hours | NOT SERVER-VALIDATED |
| Production | 4 hours | 2 hours | PROPOSED; validation deferred to ISI-28 |

No target above is an operational guarantee. Production values must be replaced or accepted only after measured server-side backup, restore, storage-capacity and operational evidence under ISI-28.

## Preflight

1. Confirm the target is explicitly non-production for ISI-19. Abort if the target is production-marked or ambiguous.
2. Confirm the selected recovery manifest schema/tool versions are supported.
3. Verify every artifact exists and matches recorded byte size and SHA-256 digest before restore.
4. Confirm the database target is fresh/empty or otherwise explicitly prepared for the rehearsal.
5. Confirm PostgreSQL client/server compatibility and a single Alembic head.
6. Confirm object-storage destination is isolated from production and from unrelated tenant/product data.
7. Capture the candidate manifest, artifact digests, source commit and planned verification steps before mutation.

## Recovery order

1. Freeze writes to the isolated recovery target.
2. Validate the manifest and all backup artifact digests.
3. Restore PostgreSQL into a fresh target.
4. Verify Alembic head/schema viability and selected relational invariants.
5. Restore only the explicitly listed object keys.
6. Verify object byte content and SHA-256 values after write-back.
7. Re-run SIMPA/ORDO isolation checks and other required acceptance tests.
8. Record machine-readable evidence before the target is released for any further non-production use.

## Abort conditions

Abort immediately on unsupported manifest metadata, missing artifact, size or digest mismatch, PostgreSQL command failure, migration-head mismatch, relational verification failure, object-key mismatch, object-content mismatch, cross-tenant/product mixing, or any target that is not explicitly approved as non-production for ISI-19. Do not continue by suppressing or bypassing a failed gate.

## Rollback-safe behavior

ISI-19 never restores into the current server. Synthetic recovery creates isolated targets and removes only resources it created itself. Retention calculation is dry-run by default. Deletion requires explicit non-production opt-in and candidates must resolve below the configured backup root. If a rehearsal fails, discard the isolated target, retain evidence needed to diagnose the failure, correct the implementation and repeat from a fresh target.

## Evidence

For each accepted rehearsal record the source baseline/head, manifest schema/tool versions, artifact inventory and SHA-256 digests, PostgreSQL 17 restore result, migration-head verification, relational isolation result, object-storage restore result, CI run, review state and the explicit state `DEFERRED_SERVER_VERIFICATION`. Never include credentials, credential-bearing database URLs, raw application payload excerpts, authorization headers or production backup media.

## ISI-28 handoff

Production backup schedule, capacity, encryption/KMS integration, real retention policy, measured RPO/RTO, restore permissions, operational ownership and server rollback procedures remain deferred. They may be verified only after a new explicit owner approval for ISI-28.
