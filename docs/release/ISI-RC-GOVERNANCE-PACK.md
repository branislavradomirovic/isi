# ISI RC governance pack

## Release scope and notes

ISI contains SIMPA and ORDO over shared infrastructure, with separate domain,
organization, workspace, knowledge and AI policy boundaries. This release
consolidates accepted ISI-25/26/27A contracts and public portal remediation.
27B adds evidence tools only. It changes no domain calculation or runtime API.
Public documents remain an index of 26 preserved external source links; files
have not been silently migrated. EN knowledge links explicitly identify SR
fallback when a published English counterpart does not exist.

## Methodology-state acceptance

The generated SIMPA artifact consolidates current lifecycle, reference suite,
statistical target/diagnostic/calibration and Help/XAI tests. VALIDATED remains
a human decision after deterministic reference PASS. No LISI formulas, citizen
scoring, eligibility automation or causal conclusion is introduced.

The separate ORDO artifact consolidates evidence/methodology lifecycle,
GIS/statistical contracts, deterministic forecast/backtest/uncertainty,
permission-separated customer workflow and Help/XAI. Scenarios are assumptions,
not forecasts; impact remains NOT_ESTIMATED / NO_APPROVED_RESPONSE_MODEL without
an approved response model. No automatic model selection or promotion occurs.

Both artifacts describe repository contract acceptance with synthetic fixtures.
They do not enumerate or validate production methodology versions. Live state
and institution-specific approvals must be checked separately during ISI-28.

## Model and evaluation provenance

The pack binds registry, evaluation, promotion and policy source hashes plus
both frozen product-specific evaluation fixtures to the exact source candidate.
SIMPA-EVAL-v1 and ORDO-EVAL-v1 foundation fixtures are synthetic contract evidence,
not production-quality model evaluation or a promotion authorization. Accepted
ISI-25 human promotion, champion/challenger, fallback and namespace boundaries
remain authoritative. No provider or model is deployed by generating a pack.

## Security and privacy

Current regression consolidates ISI-20 RBAC/authentication/session/security
controls and ISI-21 privacy/retention/export/AI eligibility contracts. Native
PostgreSQL coverage supplies database-specific proof independently. Logs and
reports contain only synthetic fixtures; production tokens, institution data
and dumps are excluded. This is control acceptance, not certification of legal
compliance or server configuration. Terms/Privacy publication has a separate
fact-grounded content gate; operator/provider contracts are operational matters.

## Migration and recovery

The runner creates disposable PostgreSQL 17, tests the complete Alembic chain,
imports offline preserved fixtures, then executes current native suites.
ISI-19 separately dumps/restores a synthetic PostgreSQL database and verifies
scoped SIMPA/ORDO object-storage recovery. Only the summary and report hashes
enter the RC pack. Real production backup, restore and data integrity remain
ISI-28 gates. A successful synthetic restore does not prove a live backup.

## Performance and compatibility

The complete inherited ISI-26 catalogue runs against this candidate. Correctness
and resilience remain blocking; timing is UNCALIBRATED where calibration is
absent, portable resource evidence remains UNAVAILABLE, and production capacity
is unverified. FastAPI, Streamlit, existing API/schema/auth contracts, PostgreSQL
17 and Compose remain supported. No broad dependency upgrades are part of 27B.
Historical observation-derived analytical runs remain read-only compatibility;
new analytical work must consume governed snapshots/features.

## Known limitations and release handoff

- Full hosted CI must accept the exact committed RC during 27D. Local evidence
  alone cannot establish CI_VERIFIED.
- 27C must bind archive, SBOM, signature/provenance and image vulnerability gates.
- Real-provider MFA, SMTP delivery, runtime/provider configurations and server
  capacity are not verified by this repository pack.
- ISI-28 must audit the current server and finalize a current deployment contract
  before mutation. Old ISI-15/16 scripts remain historical compatibility.
- Shared central Nginx routes use isi_ingress with isi-api/isi-streamlit and
  endpoint https://isi.opus.rs:8445/. Krcuga :8443 and OralScanXAI :8444 must stay
  healthy before and after the controlled change.

## Rollback

Before ISI-28 cutover, record the running source/image identity, immutable prior
release path, central-ingress configuration identity, PostgreSQL migration head
and verified database/object-store backups. Retain the previous immutable release.
On failed health/auth/domain/worker/data-integrity acceptance, restore the prior
runtime artifact and matching configuration through the owner-approved contract.
Do not automatically downgrade schemas: assess compatibility and restore the
verified backup only through the recorded recovery procedure. Route rollback
must be limited to ISI and followed by all three service health checks. Record
deployed artifact hashes and actual rollback outcome; never infer server success
from CI. Current status: DEFERRED_SERVER_VERIFICATION.
