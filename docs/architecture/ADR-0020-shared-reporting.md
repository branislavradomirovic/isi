# ADR-0020 — Shared Reporting with Domain Adapters

## Decision
Use one shared reporting persistence/lifecycle engine under `src/platform/reporting`, with separate SIMPA and ORDO reporting adapters under their domain packages.

## Why
Report identity, versioning, provenance, review, publication and export are platform concerns. Indicator semantics, monitoring interpretation and scenario semantics are domain concerns. Putting both into a generic JSON reporting service would either duplicate infrastructure or leak one product's ontology into the other.

## Dependency direction
Domain adapters may depend on their own domain models and on shared AI job records solely to verify accepted human review. The shared reporting core does not import SIMPA or ORDO models.

## Version model
A report is a stable registry object. A report version is an immutable content/provenance snapshot. Lifecycle transitions mutate only status/timestamps, not content. New evidence creates a new version.

## Publication
Only `approved` versions can become `published`. A later publication marks the previous published version `superseded`; history is retained.

## AI
Reporting performs no new model inference. It may carry forward already-persisted AI structured output only when both domain synthesis review and shared AI human-review state are accepted. This keeps reporting downstream of human accountability.

## Exports
JSON, Markdown and HTML are deterministic first-class artefacts. They are stored with SHA-256. Production-grade PDF rendering is intentionally deferred until a renderer, fonts, page templates and visual acceptance criteria are explicitly selected.
