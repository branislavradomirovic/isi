# ISI Public Portal Audit Remediation R1

Status: **IMPLEMENTED / REVIEW_VERIFIED UNSTAGED CANDIDATE**
Baseline: `main` `3e652e392624b3903498a1c2a00024306e6308d1`
Approval: owner approved the read-only audit findings and `PROPOSED_REMEDIATION_SCOPE`, then directed implementation.
Canonical system inventory impact: **NONE**. This change stays within the existing public website presentation/catalog boundary and adds no service, data owner, integration, security boundary, or deployment component.

## Objective

Repair the accepted public-portal audit findings with minimal changes, preserve migrated source data and URLs, and rerun relevant existing ISI-04C readiness checks (favicon, robots, sitemap, manifest, SEO, public/API 404 behavior, accessibility and responsive layout). Do not change public production data or deploy.

## Locked implementation surface

- `src/public/catalog_service.py`
- `src/public/routes.py`
- `src/public/templates/partials/footer.html`
- `src/public/templates/index.html`
- `src/public/templates/inclusive_development.html`
- `src/public/static/css/semantic-polish.css`
- `src/public/readiness_routes.py` (read-only inspection; edit only if an acceptance defect is proven)
- `src/public/templates/partials/seo_meta.html` (read-only inspection; edit only if an acceptance defect is proven)
- `tests/test_isi_04c_public_portal_remediation.py`
- `tests/test_isi_04c_seo_routes.py`
- `tests/test_isi_04c_readiness_contract.py` (read-only inspection; edit only if an acceptance defect is proven)
- `tests/test_isi_27a_public_help_contract.py` (template-render fixture compatibility only)
- `automation/specs/ISI-PUBLIC-PORTAL-AUDIT-REMEDIATION-R1.md`
- `automation/tasks.json`
- `automation/STATUS.md`
- `tools/qa/run_isi_public_portal_remediation.py`
- `tools/qa/analyze_isi_public_portal_remediation.py`

Any further path requires an explicit scope reconciliation before editing.

Acceptance evidence: `automation/evidence/ISI-PUBLIC-PORTAL-AUDIT-REMEDIATION-R1/acceptance.json`.

## Approved work

1. Parse the icon-only anchors in the preserved legacy Documents page by pairing each anchor only with its adjacent, structurally associated document heading. Preserve the source href/title, existing URL validation, duplicate handling and item cap. Do not invent or rewrite content.
2. Remove English links to absent `/en/dokumenti/`, `/en/biblioteka/` and `/en/inkluzivni-razvoj/` routes. Resolve each to a published English translation when present; otherwise route to its published Serbian page and visibly identify the Serbian-language destination. Do not write translations or mutate content records.
3. At narrow mobile widths, keep the Documents page title on one line and prevent the decorative illustration from clipping the viewport.
4. Verify existing readiness behavior: favicon, `robots.txt`, sitemap, web manifest, canonical/hreflang/OG/Twitter/robots metadata, public HTML 404 and API JSON 404, focus/reduced-motion/target-size contracts, safe external links and desktop/mobile layout. Fix only defects in these existing contracts.

### Documents decision

No second migration is in this candidate. The preserved source snapshot contains 26 title/URL pairs whose anchors are icon-only; the public catalog parser discarded them because it required anchor text. The local candidate now renders all 26 from that existing content. This is a parser/rendering defect, not evidence that 26 new records need to be authored. Production database content is neither directly queried outside the public route nor changed here; after deployment, acceptance must confirm that the published page body still contains the same 26 source links.

### OralScanXAI readiness items mapped to ISI

The applicable shared portal checks in this task cover branded page identity and favicon, `robots.txt`, sitemap, manifest, SEO metadata, branded public 404, contact link, responsive behavior and public/private route boundaries through the existing full regression suite. No ISI Terms/Privacy destination or owner-approved legal text was found in the public templates or ISI-04C contract; this task does not invent or publish legal copy. A server-side Nginx package is outside this task because ISI's shared-edge/server changes are reserved for ISI-28.

## Explicitly out of scope

- Publish or migrate document/library content, edit production data, change external source URLs, or claim external documents are reachable without live evidence.
- Translate pages or add new public routes/content.
- Add legal terms/privacy pages or publish legal claims without owner-approved source text.
- Change event dates/editorial state; the past April 2026 event remains an editorial review finding.
- Change SIMPA/ORDO behavior, domain or authorization boundaries, public/authenticated boundaries, schemas, migration, production deployment, DNS, ingress, secrets or server state.
- Stage, commit, push, dispatch hosted Actions, or claim `CI_VERIFIED` / `SERVER_VERIFIED`.

## Acceptance

- Focused tests prove all 26 source document title/URL pairs render, icon-only links without a structurally paired document title are excluded, and no titles or URLs are fabricated.
- English home/footer/knowledge links use published English routes where they exist and otherwise have a working Serbian destination marked as Serbian.
- Mobile CSS constrains the Documents title and art at 390px-class viewports; desktop layout remains intact. Inspect local preview at desktop and 390px mobile.
- Existing readiness tests pass and strengthen response types/content for favicon and manifest, production/non-production robots, published-only sitemap, SEO, 404, accessibility, and external-link behavior.
- Full available local regression passes; `git diff --check` passes; independent analyzer reports only locked paths; candidate remains unstaged and uncommitted.
- Master Plan roadmap/phase status is unchanged. `TECHNICAL_DOCUMENTATION.md` is unchanged because no architecture/runtime/deployment boundary changes.

## Execution boundaries

Run only in the canonical repository on `main`, with the original baseline and `origin/main` unchanged during candidate validation. The runner and analyzer are read-only with respect to Git control state.

## Owner-authorized finalization continuation — 2026-10-04

The owner explicitly requested implementation of all proposed remaining work, final deployment, and alignment of local/GitHub/server source. This authorizes the outer assistant to finalize reviewed local candidates by exact-file staging and direct main commit/push. The original no-Git-mutation boundary applies to the implementation runner/analyzer, not this later owner-directed finalization. Production still follows 27B, 27C, 27D acceptance and controlled ISI-28 deployment.

The four separately approved unpublished legal-draft paths are allowed companion documents in this candidate: `automation/specs/ISI-PUBLIC-LEGAL-NOTICES-DRAFT-R1.md`, `docs/legal/ISI-PUBLIC-TERMS-DRAFT.md`, `docs/legal/ISI-PRIVACY-NOTICE-DRAFT.md`, and `docs/legal/ISI-LEGAL-NOTICES-RELEASE-CHECKLIST.md`. This reconciliation adds no runtime path or published legal statement. The analyzer continues to reject every other unapproved path.
