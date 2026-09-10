# ISI-17 Acceptance Summary

- Task: `ISI-17-AUTONOMOUS-DEVELOPMENT-HARNESS`
- Final state: `MERGED`.
- Baseline: `dce074a744bc3055e1f4a827e0ca8d2073ebe44f`.
- Implementation PR: #4 (`codex/implement-isi-17-ci-for-autonomous-development` -> `codex/isi-17-autonomous-development-harness`), final head `8f78f7c8bd6717927dd335c9ae4378d5fb5cbb44`.
- Parent integration PR: #3 (`codex/isi-17-autonomous-development-harness` -> `main`), final head `a07b7e67dcdf4dd5ecc654fd2cb84d91bb617660`.
- Main merge commit: `1e4d23543520c7c69ac96e1e79a83ad750b82fae`.
- PR #4 acceptance: run #31 / `34463553604` — `success`.
- PR #3 acceptance: run #33 / `34463767042` — `success`.
- Main post-merge acceptance: run #34 / `34463983460` — `success`.
- Independent re-review: `REVIEW_VERIFIED / no unresolved technical blocker`.
- Server verification: `DEFERRED_SERVER_VERIFICATION`.

## Final CI evidence

Every blocking gate passed on the final implementation/integration path: `policy`, `quality`, `tests`, `architecture-security`, `migration`, `native-postgres`, `compose`, `supply-chain`, `build`, and aggregate `acceptance`.

The ordinary pytest artifact records 320 tests: 304 passed, 16 environment-gated native PostgreSQL tests skipped, 0 failed, 0 errors. The dedicated native PostgreSQL artifact records 18 tests: 18 passed, 0 skipped, 0 failed, 0 errors against ephemeral PostgreSQL 17. The native database coverage is therefore blocking rather than accepted through skip-only behavior.

## Review remediation closed

The independent-review findings were closed before merge:

- binding `AGENTS.md` architecture, server-lock, test-integrity, methodology and isolation invariants are validated rather than checking file existence alone;
- negative policy regressions reject remote shell/copy, deployment tooling, direct current-site contact and infrastructure mutation from autonomous CI tooling;
- native PostgreSQL acceptance is a blocking gate and runs against a fresh PostgreSQL 17 service;
- historical/public fixtures are reconstructed from committed snapshots and media uses an in-process `httpx.MockTransport`, with no production/server network I/O;
- PEP-517 build bootstrap versions are exact and `pip-tools` regeneration provenance is documented;
- CI concurrency cancels obsolete runs for the same PR/ref without weakening current-head gates;
- SIMPA and ORDO Help/User Guide deliverables are registered in the roadmap and methodology remains explicitly DRAFT/PROPOSED until human/user-testing approval.

The final native PostgreSQL regression fix scopes the legacy-import assertion to pages mapped from `PublicLegacySource`, preserves shared-AI embedding tables introduced by ISI-07, and verifies the finalized redirect state exactly against the generated redirect summary after ISI-03C finalization.

## Known non-blocking warning

Some superseded intermediate workflow runs failed while the CI implementation was being repaired. Those runs are historical and do not represent the final state. GitHub-hosted actions also emit a Node 20 deprecation warning while currently being forced onto Node 24; this is not a present acceptance failure.

## No-server confirmation

No remote access, deployment, DNS/ingress mutation, production credential use, production data access, SMTP change, production backup/restore, or server Ollama change was performed. Current-server verification remains deferred to ISI-28 and requires separate explicit owner approval.
