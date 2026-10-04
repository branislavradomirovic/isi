# ISI Public Legal Notices Draft R1

## Status

Drafting artifact completed on 2026-10-04. **Publication and production deployment are blocked** until the owner completes `docs/legal/ISI-LEGAL-NOTICES-RELEASE-CHECKLIST.md`, obtains legal review, and the 27B → 27C → 27D → 28 release sequence is satisfied.

## Authority and scope

Owner instruction: prepare Terms and Privacy independently, using industry-standard structure, and proceed toward deployment. This contract narrows the work to a fact-grounded internal SR-Latn draft with an EN working translation and a publication checklist. It does not authorize inventing the controller's legal identity, lawful bases, vendors, data location, retention schedule, cookie behavior, governing forum, or rights contact. It does not authorize publishing an unverified legal notice or bypassing the release gates.

### Deliverables

- `docs/legal/ISI-PUBLIC-TERMS-DRAFT.md`
- `docs/legal/ISI-PRIVACY-NOTICE-DRAFT.md`
- `docs/legal/ISI-LEGAL-NOTICES-RELEASE-CHECKLIST.md`

### Exact mutable surface

These three governance/legal drafting documents only. Public routes, templates, page seeds/content, migrations, robots/sitemap, cookies, server configuration, production data, and customer-facing behavior are unchanged by this drafting task.

### Canonical system inventory impact

**NONE.** This candidate creates internal, unpublished drafting material only; it does not add a customer surface or change product, service, data, privacy, hosting, or deployment boundaries. If finalized legal pages are added to the public portal, reconcile the public-surface inventory row in that implementation candidate.

## Evidence and content rules

- Repository observations are labeled as as-built evidence, not proof of production behavior.
- Legal identity, controller/processor roles, purpose-specific lawful bases, cookie/local-storage inventory, processor/subprocessor list, transfer locations, retention periods, DPO status, operational controls, content rights, and dispute forum remain explicit owner-verification items.
- The public general contact email is present in the footer, but its authority for legal/privacy notices is unverified.
- The draft distinguishes the public website, platform identity/security, and customer-entered SIMPA/ORDO workspace data.
- The draft does not claim that ISI owns third-party publications, that the platform is cookie-free, that data stays in Serbia, or that any unverified security control is live.
- Serbian is the controlling drafting language; the English content is marked a working translation pending owner/legal decision.
- No public text or user-specific legal representation may be inferred from repository code alone.

## Acceptance

- [x] Both Terms and Privacy drafts cover Serbian Latin and English working translation.
- [x] Required publication facts are explicit and bracketed rather than fabricated.
- [x] Privacy draft covers data categories, purposes, lawful-basis confirmation, retention, processors, transfers, cookies, rights, security, DPO determination, children, and controller roles.
- [x] Terms draft covers scope, permitted use, content rights, research/analytics context, third-party links, accessibility, liability limits subject to applicable law, changes, and governing law placeholders.
- [x] Publication checklist says drafts remain internal and identifies release order.
- [x] `git diff --check` passes; no application behavior or production state changed.

## Legal research reference

The current Serbian Law on Personal Data Protection, Official Gazette of the Republic of Serbia No. 87/2018, was consulted in the official Legal Information System: <https://pravno-informacioni-sistem.rs/SlGlasnikPortal/eli/rep/sgrs/skupstina/zakon/2018/87/13/reg>. The Serbian Commissioner’s current guidance on data-subject rights and data-protection-officer designation was consulted at <https://poverenik.rs/zastita-podataka/kako-da-ostvarite-svoja-prava/?script=lat> and <https://poverenik.rs/pojasnjenje-i-obaveze-lica-za-zastitu-po/?script=lat>. Confirm the law’s current consolidated status and the Institute’s case-specific obligations at legal review/publication time.

## Release boundary

This task does not grant permission to publish, seed production CMS content, stage/commit/push, dispatch hosted acceptance, or mutate the live server. Production deployment remains subject to the ISI-27 dependencies and exclusive ISI-28 authority in the Master Plan and repository instructions.
