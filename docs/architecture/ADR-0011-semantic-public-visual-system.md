# ADR-0011 — Semantic public visual system

## Decision
Public list/card iconography is selected from domain meaning, not from layout type. The shared icon vocabulary is provider-free, local SVG, accessible through the existing sprite, and stable for templates/tests.

The official ISI source asset remains immutable. A transparent web derivative is generated at install time for presentation only. SIMPA and ORDO marks are local first-party platform assets and remain visually subordinate to the ISI parent identity.

Activities use migrated images when available and local editorial SVG illustrations when not. This avoids broken placeholders and avoids presenting generated documentary photography as evidence of a real event.

## Consequences
- Public sections become easier to scan and learn.
- SIMPA/ORDO domain concepts are visually distinguishable.
- Future content items can reuse a single semantic icon policy.
- No new database schema is required.
