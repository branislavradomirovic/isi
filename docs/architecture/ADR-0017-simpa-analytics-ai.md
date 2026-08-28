# ADR-0017 — SIMPA Analytics and AI

Status: accepted by ISI-09 implementation.

SIMPA analytics is domain-specific and remains isolated from ORDO. Shared identity, data, AI orchestration, provider, audit and job infrastructure are reused.

The analytics layer separates three concepts:

1. source observations — evidence recorded in ISI-08;
2. methodology-governed indicator results — computed only from validated methodology;
3. AI synthesis — narrative decision support that is always provenance-bound and human-reviewed for sensitive SIMPA use.

The monitoring quality score measures evidence readiness only. It is not a social-risk score.

Sensitive SIMPA AI requests must use the shared local-only policy. SIMPA never calls Ollama directly.
