# ISI-28 privacy and operations baseline

Status: **OWNER-APPROVED POLICY TARGETS — ENFORCEMENT NOT FULLY VERIFIED** (2026-10-06).
Prepared under the owner's instruction to propose and implement the missing
policies. This is the concrete deployment target, not a claim of present server
configuration or a universal legally mandated retention schedule. It must be
reconciled with actual processing, contracts and applicable obligations before
public notices describe it as operating.

## Confirmed contact and unresolved responsibilities

The owner confirmed the Institute name **Institut za socijalnu inkluziju**, the
operator brand **GoraNova**, and interim privacy contact
**institutzasocijalnuinkluziju@gmail.com**. The legal entity behind GoraNova for
this project and registered addresses remain unknown. GoraNova's published
[terms](https://www.goranova.org/terms/) identify it as a business unit and defer
the contracting entity to the particular engagement. Do not substitute the
brand for a verified legal controller/processor identity.

Before publication, assign named operational owners for the mailbox, security
incident response, backups/restoration and hosting administration. Document
controller/processor roles per public website, account/security, support and
organization workspace processing. Do not assume that a technical operator is
a controller for every purpose or that the Institute is a public authority.

## Proposed retention schedule

| Category | Proposed target and trigger | Required enforcement/evidence |
|---|---|---|
| Public reverse-proxy access/error logs | 30 days from event | ISI-specific rotation; exclude credentials, query tokens and bodies; verify actual log fields and oldest retained file |
| Application diagnostics | 30 days from event | Existing redaction plus bounded rotation; no raw prompts, document contents or session tokens |
| Security/audit events | 180 days from event, unless a documented incident/legal hold requires limited extension | Review event classes, foreign-key/provenance requirements and scoped deletion before scheduling; retain no more identifiers than needed |
| Expired/revoked authentication tokens and sessions | Remove obsolete token/session records within 30 days after expiry/revocation, subject to audit-reference integrity | Expiry is not physical deletion; current token expiry controls alone do not prove this target. Implement/review a bounded cleanup only after schema/retention audit |
| Closed accounts | Disable access/revoke sessions promptly; review deletion or pseudonymization within 30 days of closure | Preserve required organization audit references; never cascade-delete institutional records without scoped authority |
| Routine support email | 12 months after the issue closes | Mailbox owner reviews monthly; apply purpose-based shorter deletion and recorded legal-hold exceptions |
| Data-rights requests | Minimum case record for 24 months after closure | Retain request date, action and response evidence; avoid identity-document copies unless demonstrably necessary; review legal basis/period before activation |
| Backups | Rolling 35-day recovery window | ISI-only encrypted/protected backups with lifecycle expiry, access restrictions and restore rehearsal; deletion requests must be reapplied after restoration before reopening access |
| SIMPA/ORDO workspace source/derived data | Explicit organization/product/workspace policy and institutional agreement; no invented platform-wide duration | Use existing governed retention state, legal hold and request/approve/execute purge boundaries; no blanket auto-delete of institutional data |
| Temporary exports and failed-job scratch data | Remove within 7 days after expiry/completion unless an approved workflow requires otherwise | Inventory actual paths and ownership first; do not delete shared storage or unrelated products |

A legal hold is scoped, documented, time-reviewed and access-restricted. It
must not silently turn all retention into indefinite storage. A proposed
cleanup is not enabled until its dependencies, dry-run counts and recovery
behavior are verified. Existing data-platform approvals and provenance remain
authoritative; this document does not authorize bulk deletion.

## Requests, incidents and provider register

The mailbox owner records a minimal case ID and receipt date, verifies identity
proportionately, determines the correct controller and tracks the response.
Access/correction/deletion/restriction/objection/portability requests are assessed
against their applicable conditions. The Serbian Commissioner describes a
30-day response period, with a possible justified 60-day extension; any extension
and reasons must be handled within the applicable statutory process. See the
[Commissioner's guidance](https://poverenik.rs/zastita-podataka/kako-da-ostvarite-svoja-prava/?script=lat).
The internal operational target is acknowledgment within three working days;
it is not presented as a statutory deadline or an already staffed service.

For a suspected incident: contain affected ISI access, preserve minimal evidence
in protected storage, record awareness time, scope and affected categories,
notify the responsible controller/operator, assess notification obligations
promptly, and document the decision and remediation. Legal reporting deadlines
must be established from the applicable law/role; no public statement should
claim that a response team or process is live before responsibility is assigned.

Maintain a processor/subprocessor register covering hosting, backup locations,
SMTP delivery, the approved Gmail support/privacy mailbox, monitoring and any
external AI services actually used. Record legal names, purposes, countries,
access locations, agreements, transfer safeguards, retention and change dates.
Self-hosted PostgreSQL/Redis/MinIO are components, not automatically third-party
processors. Sensitive SIMPA processing retains the existing local-only AI policy.
No customer data enters shared knowledge or an external AI service merely
because a provider is configured.

## Production acceptance evidence

Before final publication/deployment closeout, retain sanitized evidence of:
actual controller/operator identities; provider/data-flow register; cookie and
browser-storage inventory; deployed retention settings and cleanup mechanisms;
backup/restore and expiry controls; named operational owners; request/incident
procedures; appropriate legal review and DPO determination. Public text must
reflect only the confirmed processing. Do not label this baseline implemented
or server-verified until these controls operate and have been checked.

## Operational policy activation contract — 6 October 2026

Owner approved these operational policy targets. Approval does not establish
that every technical enforcement mechanism or human duty is active.

| Responsibility | Accountable role | Procedure / activation evidence |
|---|---|---|
| Release/cutover and acceptance | ISI project owner | Exact candidate/checkpoint approval; approved maintenance boundary; rollback decision |
| Infrastructure, backups and recovery | GoraNova operations role | Daily backup success review, weekly inventory, monthly isolated restore; secondary protected copy location still pending |
| Security incident handling | GoraNova incident coordinator role | Record detection time; assess scope; contain ISI only; preserve minimal evidence; notify project owner/controller; assess statutory notice obligations |
| Privacy requests and mailbox | Institute privacy coordinator role | Receipt register; acknowledgment target three working days; identity verification; controller routing; statutory response tracking |
| Workspace retention and legal holds | Each organization’s authorized data-governance role | Existing request/approve/execute boundaries; no blanket deletion or automatic override of holds |

These are role assignments, not invented personnel or a staffed 24/7 service.
Duty-holder names, access authorization, monitored channels and handover
acknowledgment must be recorded before the related operational acceptance.
SMTP is pending; no automatic outbound alerts or delivery are claimed.

Backup targets: daily consistent database/object checkpoint, 35-day recovery
window, protected ISI-only storage and a separate encrypted copy outside this
host. Target RPO 24 hours and target RTO 4 hours are planning targets; measured
restore evidence is required before advertising them. Preserve pre-cutover
checkpoints until explicit release-owner disposition; automated cleanup may
only target verified generated ISI backups and must honor holds.

Incident procedure: identify/triage, contain affected ISI access, preserve
protected evidence without secrets or document payloads, assess impact and
controller notification, eradicate cause, restore from verified state, validate
all boundaries, then record a review and corrective actions. Legal reporting
obligations depend on applicable facts and roles; public placeholders do not
resolve them. Privacy processing follows receipt, proportionate identity check,
scoped assessment/approval, execution, response and minimal closure record.

Monitoring acceptance must cover API/UI, worker liveness and queue age/failures,
PostgreSQL/Redis/MinIO reachability, disk capacity, backup age/result and
certificate expiry. Checks are ISI-scoped and do not restart other products.
Alerts are not operational until a real monitored destination and duty holder
are verified. No retention purge is scheduled before bounded dry-run, foreign
key/provenance audit, hold handling and recovery coverage.

References: [NIST CSF 2.0 Small Business Guide](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=957322),
[NIST contingency planning](https://csrc.nist.gov/pubs/sp/800/34/r1/upd1/final),
[Serbian Commissioner duties](https://poverenik.rs/zastita-podataka/obaveze-rukovaoca/).
These inform controls; they are not an ISI certification.
