# ISI target-server deployment runbook

This runbook is subordinate to `docs/ops/ISI-PRODUCTION-WORKFLOW-LOCK.md`.

## Locked target

- SSH: `ubuntu@94.230.189.146`, port `222`.
- Operational root: `/home/ubuntu/ISI`.
- Compose project: `isi`.
- Pre-cutover loopback endpoint: `https://127.0.0.1:8445` on the server only.
- Public production endpoint after ISI-16: `https://isi.rs` and `https://www.isi.rs` through `central-ingress`.

## Release model

The local repository currently has no Git remote configured, so deployment uses immutable Git archives rather than server-side `git pull`.

After the local implementation is green and the owner manually commits it:

1. `tools/release/build_server_release.sh` requires a clean worktree and archives exactly `HEAD`.
2. The archive is SHA-256 checksummed.
3. `tools/release/deploy_server_release.sh` sends it over SSH port 222.
4. The release is extracted below `/home/ubuntu/ISI/releases/<git-sha>/`.
5. Real runtime secrets remain below `/home/ubuntu/ISI/runtime/`, outside every release.
6. Server deployment builds the image, starts only the ISI project, runs Alembic, then automated acceptance.
7. `/home/ubuntu/ISI/current` changes only after the automated acceptance succeeds.

No deployment script commits, pushes, resets, cleans, changes Git remotes, prunes Docker, modifies Krcuga/OralScan, or changes public DNS.

## Pre-cutover acceptance

ISI-15 server acceptance is completely automated and includes:

- PostgreSQL/Redis readiness;
- Alembic head `20260828_0013`;
- local TLS edge health/readiness;
- production-mode public draft leakage safety;
- SIMPA-only, ORDO-only, and dual-product auth context smoke through temporary preproduction identities;
- S3 write/read/hash/idempotency/persistence;
- Mailpit capture of verification/reset/invitation mail;
- RQ execution through both `isi-data` and `isi-ai` queues;
- AI worker connectivity to the existing host Ollama runtime;
- restart/persistence rehearsal;
- PostgreSQL + object-storage backup and isolated restore rehearsal.

The owner performs no manual browser acceptance.

## ISI-16 boundary

Only after ISI-15 server acceptance is green may ISI-16 prepare a fresh production DB/bucket/Redis namespace, install real SMTP values, provision TLS, extend central-ingress, and change DNS.
