# ISI-27A-R1A-R2 — Ignored-Evidence Preflight Recovery

## Status
Recovery-only continuation of the unstaged ISI-27A R1A candidate after the R1A-R1 preflight false-negative.

## Baseline
- Accepted main SHA: `39dc1d59a74a03c86f68df093cc07e32d41d028c`
- Accepted main tree: `3c7027b375b041043f7305cdab008aee35f16ef7`
- Parent candidate: ISI-27A-R1A no-Codex inherited Help convergence.
- R1A prestate fingerprint captured by the previous runner: `c4d13bb5ce3b212be97ef5f9cc7a51d656e7e409541f2e05814d9fac8c8f295e`.

## Root cause
R1A-R1 incorrectly tried to discover `automation/evidence/.../R1A/` with Git status commands. The repository `.gitignore` contains `evidence/`, so those deterministic transient files are intentionally invisible to `git diff` / `git ls-files --others` even when they physically exist. The R1A runner wrote the transient evidence before its focused test failed.

## Objective
Correct only the recovery preflight/evidence observation model, restore the canonical task `spec` pointer to the full R1 implementation contract, preserve R1A as recovery provenance, then complete deterministic local acceptance without Codex.

## Exact mutable surface
The prestate is the exact 31-path R1A candidate. This recovery may add only:
- `automation/specs/ISI-27A-R1A-R2-IGNORED-EVIDENCE-PREFLIGHT-RECOVERY.md`

It may additionally modify only the already-candidate path:
- `automation/tasks.json`

Final Git-visible candidate surface: exactly 32 paths.

## Canonical spec authority
`automation/tasks.json` must point `ISI-27A-SHARED-HELP-RELEASE-UX-COMPLETENESS.spec` to:
`automation/specs/ISI-27A-R1-SHARED-HELP-RELEASE-UX-COMPLETENESS.md`.
R1A and R1A-R2 are recovery/provenance authorities, not replacements for the complete task specification.

## Ignored evidence authority
The R1A transient evidence directory is not a Git candidate surface. Preflight must inspect it directly on the filesystem and accept only the exact expected R1A failed-focused-test evidence:
- `README.txt`
- `boundaries.txt`
- `focused-tests.log`
Unexpected files or directories fail closed. The log must identify the canonical-spec-pointer focused-test failure. After successful recovery acceptance, the evidence is copied to the user-local recovery output and removed from the working repository tree.

## Locked boundaries
- No Codex call.
- No stage, commit or push.
- No GitHub Actions dispatch.
- No server/DNS/SMTP/deployment/model/data mutation.
- No runtime/auth/domain/Help implementation edits.
- No dependency, migration, workflow, Compose or release-tool edit.
- Public self-registration remains `NOT_PRESENT`; onboarding remains invitation-only.
- `CI_VERIFIED=NO`; `SERVER_VERIFIED=NO`.

## Acceptance
1. Exact baseline/main/direct-remote equality.
2. One worktree, empty stash and index.
3. Exact 31-path R1A Git-visible candidate.
4. Direct-filesystem validation of ignored R1A transient evidence.
5. R1 frozen bytes remain equal to the R1A captured prestate where R1A was not authorized to mutate.
6. Four inherited Help tests retain the accepted R1A convergence and no domain/runtime semantics change.
7. Restore canonical R1 task-spec pointer and install this recovery authority.
8. Exact final Git-visible surface = 32 paths.
9. Focused 27A/inherited convergence tests pass.
10. Compile, Ruff, mypy, policy and `git diff --check` pass.
11. One full local pytest suite passes.
12. Index remains empty; no stage/commit/push, hosted Actions or server mutation.
13. Produce deterministic candidate fingerprint and human-review bundle.
