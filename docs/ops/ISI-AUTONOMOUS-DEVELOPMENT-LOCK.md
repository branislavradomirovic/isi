# ISI Autonomous Development Lock

This document is subordinate to the canonical MasterPlan and mirrors its autonomous-development boundary.

## Development control plane

- Canonical local repo: `/Users/branislavradomirovic/Applications/Python/ISI`; normal branch `main`; exactly one worktree.
- Normal workflow is owner-driven direct-main. Branches/PRs require an explicit owner exception.
- Every new chat/task must complete the MasterPlan-first bootstrap and legacy/drift audit before implementation.
- ISI Codex may run only through `codex-isi`; generic `codex` is forbidden.
- Candidates remain unstaged/uncommitted through runner, independent analyzer and assistant human review. Exact staging/commit/push requires explicit owner approval.
- Repository acceptance is exact-main GitHub Actions `ISI required acceptance` = `completed / success` on the exact committed SHA.

## Hard production boundary

Autonomous agents and CI must not use SSH/SCP, deploy to the server, mutate DNS/ingress, change production SMTP/Ollama, access production credentials/secrets/institution data, or execute production data migrations. Workflows receive no production secrets. Server tooling stays quarantined until explicitly approved ISI-28.

## Evidence-backed states

- `IMPLEMENTED`: exact unstaged/uncommitted candidate passed required local/task gates.
- `REVIEW_VERIFIED`: assistant human review of the exact candidate/final SHA has no unresolved blocker.
- `OWNER_APPROVED_MAIN_COMMIT`: owner explicitly approved exact staging/commit/push.
- `CI_VERIFIED`: required GitHub checks passed on the exact committed main SHA.
- `COMPLETE`: implementation, review, owner-approved main commit/push and exact-main CI are complete.
- `SERVER_VERIFIED`: separately approved server acceptance passed.
- `DEFERRED_SERVER_VERIFICATION`: the task deliberately performed no server action.
