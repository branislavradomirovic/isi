# ADR-0015 — Shared AI Foundation

## Decision
ISI uses one shared provider-independent AI orchestration layer for SIMPA and ORDO. Domain intelligence remains separated by product scope, prompt registry, policy and RAG namespace.

## Context
SIMPA and ORDO need common model access, prompt lifecycle, job execution, embeddings, audit and observability. Duplicating these capabilities would create inconsistent security and lifecycle behavior. Combining domain prompts or private retrieval spaces would create the opposite risk: semantic and tenant leakage.

## Consequences
- one gateway, one job lifecycle, one model/prompt registry infrastructure;
- organization/product/workspace scope is mandatory for private execution;
- `PUBLIC/ISI`, `PUBLIC/SIMPA`, `PUBLIC/ORDO` are explicit public namespaces;
- private namespaces are `ORG-<uuid>/<product>` and cannot cross product or tenant boundaries;
- sensitive SIMPA requests are local-only;
- Ollama is the first concrete provider, not a hard-coded architectural dependency;
- external providers can be added only behind policy and gateway contracts;
- development stub is forbidden in production;
- AI output is advisory and may require explicit human review;
- pgvector is opportunistically enabled when the PostgreSQL extension is available, with portable embedding metadata retained regardless.
