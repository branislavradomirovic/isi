# ISI-27D exact-main acceptance closeout — 2026-10-05

Status: **CI_VERIFIED / REVIEW_VERIFIED** for exact RC `2b1f2ef20a2310df23947f2ac2128d16f81a98ea` only.
Owner authorization: “Saglasan, nastavi do pune produkcije”, followed by
“nastavi dalje sa radom”. Server verification is still outstanding.

- Source tree: `a6dd8b4e0d858e7b9230ea6960f812fb6a5e3783`.
- Candidate fingerprint: `58879fc465c2eb78e2cf8c3785a0efcb553b4fd2a3358b248aadd8558d5ee06a`.
- Workflow: ISI required acceptance, manual release-candidate checkpoint
  [#93](https://github.com/branislavradomirovic/isi/actions/runs/37277358285), all 12 jobs completed/success.
- Regression: 1,118 passed; 43 existing native-runner skips. Dedicated native
  PostgreSQL lane: 45 passed, zero skips. Migration, recovery, performance,
  architecture/security, policy, quality, Compose and actual image scans passed.
- Manifest: `8f30a95106f1b1757cac3aa3f2c17e4560cd1bafe2beb5d84a667242ddfedd8b`.
- Source/image/report identities and all payload checksums were validated, then
  provenance was signed through the existing owner SSH agent in `isi-release`.
  Independent OpenSSH verification against repository pinned public trust passed.
- Actions: precheck 158/2000 minutes; postcheck 191/2000 minutes. Both showed
  0/0.5 GB storage (rounded/lagged display, not proof of zero stored artifacts).
- Immutable local evidence: `automation/evidence/ISI-27D/checkpoint-93/`.

## Whole-phase gap and legacy reconciliation

27A Help/auth/public UX, 27B methodology/model/evidence pack, 27C immutable
source/image/SBOM/scan/signature and 27D exact-main hosted acceptance are DONE.
SIMPA/ORDO remain separate; no methodology promotion or live institutional
validation is inferred from synthetic acceptance.

| Finding | Classification | Disposition |
|---|---|---|
| Failed checkpoints #91/#92 | LEGITIMATE_HISTORY | Preserve evidence; superseded by successful #93 |
| Eleven approved historical Gitleaks fingerprints | REQUIRED_COMPATIBILITY | Exact findings only; full-history scan stays enabled |
| Historical ISI-15/16 server scripts/config | REMOVE_IN_NAMED_PHASE(ISI-28) | Audit only; do not execute as current deployment authority |
| Stale current-phase pointers | REMOVE_BEFORE_NEXT_SLICE | Update task/status/MasterPlan/technical reference in this closeout |
| Terms/Privacy publication | REMOVE_IN_NAMED_PHASE(ISI-28) | Separate content gate; factual identity/provider/policy confirmation still needed before final public release |
| Live providers, backups, capacity, methodology state | REMOVE_IN_NAMED_PHASE(ISI-28) | Fresh server/operational evidence required |

Canonical system inventory impact: NONE for this closeout: INV-M20/M21,
INV-K15 and INV-J32 already describe the accepted evidence/artifact mechanisms.
No runtime component or ownership is changed. ISI-28 will reconcile relevant
server/public/legal inventory rows from observed state.

Bookkeeping commits do not inherit exact-SHA CI verification. Any final source
change included in deployment requires a matching accepted/signed release.
