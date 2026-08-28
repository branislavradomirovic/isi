# ADR-0016 — SIMPA domain foundation

Status: Accepted for ISI-08 implementation.

## Decision
SIMPA receives its own domain schema under `src/domains/simpa` and `simpa_*` database tables. Shared identity, data, jobs and AI infrastructure remain in `core_*` tables.

## Boundary
A SIMPA domain request is valid only when the selected workspace belongs to the requested organization and has product code `SIMPA`. ORDO membership does not grant access to SIMPA domain endpoints.

## Indicator methodology
The initial registry contains source-derived indicator concepts only. All entries start as `conceptual`; there is no production formula or model claim in ISI-08.

## Privacy
ISI-08 stores no person-level beneficiary identity model. Indicator observations are designed for aggregate or otherwise approved values with provenance.

## Consequences
ISI-09 can implement validated calculations and SIMPA analytics without weakening tenant/product isolation or duplicating the shared data layer.
