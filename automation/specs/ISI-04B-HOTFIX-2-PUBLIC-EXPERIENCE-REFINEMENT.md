# ISI-04B HOTFIX-2 — Public Experience Refinement

## Trigger
Manual browser review accepted the general ISI-04 visual direction but requested a more professional editorial presentation: less plain text/listing, more diagrams/icons/typography, dedicated SIMPA and ORDO identities, better Documents and Library organisation/search, removal of retired ANCSEE/WBSIB landing content, and a completed Inclusive Development page.

The previous ISI-04B runner also stopped after applying Alembic `20260827_0004` because a clean CLI process did not register the `core_organizations` ORM target before seeding. HOTFIX-2 therefore includes the already-prepared HOTFIX-1 ORM bootstrap repair so the user does not need to run two recovery packages.

## Scope
- retain Alembic `20260827_0004`;
- repair clean-process knowledge model registry bootstrap;
- seed the existing domain knowledge/public-section payload idempotently;
- remove raw legacy home-body replay from the landing page;
- keep ANCSEE and WBSIB out of new landing scope;
- add original SIMPA and ORDO SVG brand marks;
- add reusable SVG icon system;
- upgrade structured SIMPA/ORDO sections to visual diagrams/cards/timelines;
- add source-preserving Documents grouping and search;
- add Library search, collections, cover-image handling and generated fallback covers;
- complete Inclusive Development with ISI tool references;
- preserve draft-only publication state.

## Non-goals
- no production publish/cutover;
- no official third-party institution logo ingestion in this task;
- no invented document/publication records;
- no RAG embeddings or vector search;
- no final SEO/accessibility sign-off (ISI-04C);
- no commit or push.

## Browser QA
After the runner passes, inspect at minimum:
- `/`
- `/simpa/`
- `/ordo/`
- `/dokumenti/`
- `/biblioteka/`
- `/inkluzivni-razvoj/`

Do not record the visual QA pass until these pages are reviewed.
