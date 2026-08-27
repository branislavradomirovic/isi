# ADR-0007 — Public Website Rendering

## Decision
The new `isi.rs` public website is rendered by FastAPI/Jinja from the PostgreSQL public-content model established in ISI-03. Templates own layout and presentation; editorial/domain content remains database-backed.

## Preview and publication
Draft content is available only when `PUBLIC_PREVIEW_DRAFTS=true` and `ISI_ENV` is not `production`. Production always requires `status='published'`.

## Media
Verified legacy media is served from the existing content-addressed `var/media/public` store under `/media/`.

## Flagship hierarchy
ISI is the institution. SIMPA and ORDO are flagship platforms. They share the ISI platform core but retain separate domain semantics and visual accents.

## Non-goals
No redirect cutover, no production publication, no public CMS administration, no SIMPA/ORDO authenticated domain functionality, and no replacement of the Streamlit authenticated application in this task.
