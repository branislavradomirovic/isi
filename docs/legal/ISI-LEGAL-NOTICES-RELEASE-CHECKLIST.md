# ISI legal notices — publication checklist

**Current status: OWNER-AUTHORIZED PLACEHOLDER PUBLICATION CANDIDATE.** The historical drafts remain internal; publish only the reviewed versioned payload described below. Unknown legal facts remain openly marked.

## Confirmed owner input and current evidence — 2026-10-05

- [x] Institute name: Institut za socijalnu inkluziju (owner confirmed).
- [x] Operator brand: GoraNova (owner confirmed); exact project legal entity/address still required.
- [x] Interim privacy contact approved: institutzasocijalnuinkluziju@gmail.com.
- [ ] Mailbox monitoring/response owner assigned and operationally verified.
- GoraNova `/terms/` and `/privacy/` defer the contracting legal entity to the project agreement; they do not supply its registered address.
- The Institute's linked Statut PDF returned HTTP 403 on the current read-only check. No registered address is inferred.
- Concrete proposed operational periods/processes are in `docs/ops/ISI-28-PRIVACY-OPERATIONS-BASELINE.md`; live enforcement is unverified because SSH authentication was rejected.
- Local portal wiring supports published localized legal-page footer/sitemap discovery; no draft legal content has been seeded or published.

## Facts to confirm

- [ ] Full legal name, legal form, registration number, tax identifier and registered office of the entity operating isi.opus.rs and ISI Platform.
- [ ] Official general contact and separate privacy/data-rights contact; postal channel for formal requests.
- [ ] Whether the displayed Gmail address is controlled, monitored, and approved for legal/privacy requests.
- [ ] Controller/processor/joint-controller roles for the public website, user identity, organizations, SIMPA/ORDO workspace inputs, support, and security logs.
- [ ] Data categories and purposes for each real production flow; lawful basis for each purpose; whether any special-category or child data is processed and by whom.
- [ ] Invitation/account eligibility, required fields, support and deletion/account-closure workflow.
- [ ] Current public/app/proxy cookies, local storage, embedded resources, analytics, anti-abuse and monitoring tools; consent behavior where required.
- [ ] Actual provider legal names, service roles, data locations, subprocessors, access controls, processing agreements and international transfers.
- [ ] Approved retention/deletion schedule covering application records, access/security logs, email/support, object storage and backups.
- [ ] Operational security claims that can be evidenced after ISI-28 verification; incident contact and breach workflow.
- [ ] Whether a data protection officer is legally required; if appointed, validate its official contact details.
- [ ] Content ownership/licensing/attribution rules for Institute and third-party publications.
- [ ] Terms questions: permitted reuse, accessibility/support contact, applicable law, dispute venue, liability wording, platform/customer agreements, change/acceptance process.
- [ ] Serbian counsel review; determine whether an English translation is needed and which text controls.
- [ ] Publication mechanism for the CMS-backed portal, route/canonical/alternate metadata, sitemap/robots behavior, and proof the published versions match approved text.

## Repository evidence used for this draft

- The public site is rendered from published database-backed pages; it currently has no Terms/Privacy route or footer link in the application templates.
- Current application behavior is invite-only for user accounts; public self-registration is explicitly absent from the system inventory.
- As-built identity includes email and display name, while passwords are stored as hashes. Authentication stores token hashes, expiry/revocation and security metadata; session creation currently clears raw IP/user-agent fields and stores privacy hashes/device label.
- Platform processing is organization-scoped and product-separated between SIMPA and ORDO. Organization-entered content may need additional purpose, category, role, AI-use and retention notices from the relevant organization/controller.
- Static public templates/scripts reviewed in this draft did not show analytics or advertising tags. This is not a production cookie audit.
- Repository technical documentation states production server, provider, retention and live security verification remain in ISI-28.

## Publication decision

Keep these Markdown drafts internal. Once the checklist is complete and approved, implement the finalized SR/EN content through the established public content management/seed process, link it in both footer locales, add route and SEO/sitemap coverage, and run targeted public/private boundary, accessibility, desktop/mobile, cookie, route and production-artifact checks. This work must be included in the approved release candidate and may only be deployed under the current ISI-28 gate after ISI-27B, ISI-27C and ISI-27D are complete.

## Owner-authorized placeholder publication — 6 October 2026

The owner explicitly authorized visible placeholders for missing facts and
publication of SR/EN notices. This supersedes the earlier complete-facts
publication gate for this release only. Canonical public payload is
`data/public/legal_notices.json`; earlier drafts remain LEGITIMATE_HISTORY.
The payload states unknowns and SMTP pending openly, does not certify legal
compliance, and describes retention as targets rather than proven enforcement.
Publication uses `tools/publish_isi_legal_notices.py` with an approved SHA256
and refuses existing-content collisions. Source acceptance and final image
deployment gates remain mandatory. Publication is not yet executed.
