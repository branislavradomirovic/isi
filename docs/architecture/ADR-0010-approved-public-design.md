# ADR-0010 — Approved ISI public design implementation

## Status
Accepted for ISI-04B visual implementation.

## Decision
The public site follows the approved institutional design system: ISI is the parent brand; SIMPA and ORDO are distinct flagship platforms. The UI uses a warm editorial background, dark institutional green, SIMPA teal and ORDO muted gold, serif display typography, compact explanatory graphics, and structured cards only where they improve comprehension.

The existing user-owned ISI logo under `assets/ISILogo` is the authoritative public brand asset. The implementation copies it into the public static tree without modifying the source and records a SHA-256 manifest. SIMPA and ORDO retain dedicated SVG marks.

## Scope corrections
- ANCSEE and WBSIB are legacy initiatives and are not rendered on the new landing page.
- Documents are grouped by source institution and remain grounded in migrated source links.
- Library search and collections operate only on migrated resources; missing covers receive an ISI visual fallback rather than fabricated publications.
- Inclusive Development explicitly references SIMPA, ORDO, documents, library and domain-organised knowledge.
- Rich domain sections use compact visual grammars instead of large empty text cards.

## Non-goals
This task does not publish draft content, activate redirects, change AI/RAG storage, or perform production cutover.
