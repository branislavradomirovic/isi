# ISI-06 HOTFIX-1 — Local QA Launcher Recovery

## Purpose
Recover the ISI-06 one-command local QA launcher after the first launcher reached READY and then failed while trying to copy stop/status scripts.

## Root cause
The original launcher executed `cd "$REPO"` before resolving `dirname "$0"`. Because it was invoked as `./run-ISI-06-LOCAL-QA.sh`, `dirname "$0"` remained `.` and later resolved against the repository directory, not the package directory. The final `cp` therefore searched for `stop-ISI-06-LOCAL-QA.sh` inside the repository and failed.

## Recovery design
- Do not rerun or rollback migration `20260828_0005`.
- Do not modify shared-data models, routes, storage, ingestion, or authorization behavior.
- Install versioned local-QA scripts under `tools/qa/`.
- Resolve `SCRIPT_DIR` before changing directory.
- Stop/status scripts are referenced in place; no runtime copying into the repository root.
- On launcher failure, only PIDs created by this launcher are stopped.
- Keep ISI-06 task `ready` pending browser/data QA.

## Acceptance
- Alembic remains `20260828_0005 (head)`.
- Existing ISI-06 implementation is detected.
- shell syntax passes.
- launcher regression test passes.
- full repository test suite passes.
- `git diff --check` passes.
- no commit or push.
