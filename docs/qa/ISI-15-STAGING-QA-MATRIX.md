# ISI-15 Automated Production-Readiness Matrix

| Area | Required evidence |
|---|---|
| Workflow | `docs/ops/ISI-PRODUCTION-WORKFLOW-LOCK.md` exists and forbids local Docker runtime |
| Task state | ISI-14 done; ISI-15 ready; ISI-16 planned |
| Native DB | local development PostgreSQL reachable and Alembic `20260828_0013` |
| Runtime config | production deployment settings fail closed when S3/SMTP/RQ/proxy requirements are incomplete |
| Storage | S3 adapter unit/contract tests pass |
| SMTP | verification/reset/invitation delivery adapter contracts pass; production tokens are not disclosed |
| Queues | data and AI RQ backend contracts pass |
| API | `/api/v1/health` and `/api/v1/readiness` registration contracts pass |
| Public safety | committed legacy migration artifacts remain accepted; no draft publication/cutover is performed |
| Regression | full suite passes via `python -m pytest` |
| Dependencies | `pip check` passes |
| Deployment source | staging/server-reference Compose/proxy files pass static contracts only; no local runtime launch |
| Server preflight | read-only preflight script inventories Docker, ports, edge proxy, resources, Compose projects and Ollama without reading `.env` |
| Server install | deferred to ISI-16 after preflight; must be scoped to independent ISI resources |
| Manual QA | not an owner gate; colleagues test only after automated server acceptance |
| Git | no script commits, pushes, resets, cleans, or configures remotes |
