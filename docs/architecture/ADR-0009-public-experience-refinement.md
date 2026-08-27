# ADR-0009 — Public Experience Refinement and Source-Preserving Catalog Indexes

## Status
Accepted for ISI-04B visual refinement. Public content remains draft-only.

## Context
Browser QA confirmed that the new ISI public direction is correct, but the first implementation remained too text-heavy. The legacy home body also exposed two retired initiatives (ANCSEE and WBSIB) that are no longer in scope for the new landing page. Documents and Library needed stronger organisation, visual hierarchy and search. Inclusive Development needed to become a complete explanatory page connected to ISI tools.

## Decision
1. The home page no longer replays the raw legacy home `body_html`. It uses curated institutional presentation plus the structured ISI-04B sections. The historical legacy source remains preserved in the database/migration archive; it is simply not rendered on the new landing page.
2. ANCSEE and WBSIB are excluded from the new landing-page scope.
3. SIMPA and ORDO receive original static SVG brand marks maintained inside the public application assets. They remain subordinate to the ISI institutional brand but have clear visual identity.
4. Structured domain sections are rendered as visual systems (network, timeline, pillars, indicator grid, trust cards, outcomes and cycles) using a reusable inline SVG icon sprite rather than plain numbered text lists.
5. The Documents page builds a read-only presentation index from links already present in migrated `body_html`. It groups those links by inferred source institution and provides client-side search/filtering. The index never invents a document title or URL.
6. Institution groups use neutral source badges (UN, EU, RS, UN+, ISI) rather than counterfeit or approximate official logos. The UI has a dedicated mark slot so approved official brand assets can replace these badges later.
7. The Library page similarly indexes existing migrated links and nearby migrated images. Missing cover art falls back to an ISI editorial cover rather than a broken image. Topic collections and client-side search are presentation metadata only.
8. Inclusive Development becomes a curated institutional explainer that references SIMPA, ORDO, Documents and Library as ISI tools/resources.
9. No new Alembic migration is required. Existing knowledge and public-section schema remains at `20260827_0004`.

## Safety boundaries
- all `PublicPage` and `PublicPageSection` rows remain `draft`;
- no production publication or redirect activation;
- no embeddings/vector/chunk storage;
- no remote content mutation;
- no fabricated document or publication URLs;
- no automatic commit or push.

## Follow-up
ISI-04C remains responsible for final institutional polish, SEO, accessibility, metadata completeness, responsive QA and publication readiness.
