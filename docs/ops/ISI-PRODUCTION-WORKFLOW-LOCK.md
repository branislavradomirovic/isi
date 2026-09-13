# ISI Production Workflow Lock

> **HISTORICAL / SUPERSEDED - DO NOT EXECUTE.**
>
> The former ISI-15 -> ISI-16 server deployment sequence is not the current workflow. The canonical authority is `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`. The server is frozen through ISI-27; only a fresh explicit owner approval for ISI-28 may authorize server/DNS/ingress/SMTP/production-secret/data/Ollama mutation.

This file remains only as a historical pointer because older specifications/runbooks referenced its path. Historical operational detail is preserved in Git history and must not be treated as current authority.

Current development workflow: MasterPlan-first bootstrap -> legacy/drift audit -> locked contract -> implementation on canonical main -> runner -> independent analyzer -> assistant human review -> owner-approved exact staging -> direct main commit/push -> exact-main GitHub Actions.
