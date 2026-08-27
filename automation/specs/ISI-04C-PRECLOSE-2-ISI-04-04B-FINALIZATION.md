# ISI-04C PRE-CLOSE-2 — ISI-04 / ISI-04B Finalization

## Purpose

Correct the pre-close task-ID mismatch from PRE-CLOSE-1 and formally close the already browser-approved ISI-04 and ISI-04B work without changing the accepted visual design.

## Exact task IDs

- `ISI-04-NEW-PUBLIC-WEBSITE`
- `ISI-04B-DOMAIN-KNOWLEDGE-CONTENT-ENRICHMENT`

The previous pre-close runner incorrectly searched for the shortened IDs `ISI-04` and `ISI-04B`. This package uses the exact IDs already used by the ISI-04B runners.

## Allowed mutations

- copy this closeout specification to `automation/specs/`
- create `docs/design/ISI-04-04B-VISUAL-QA-ACCEPTANCE.md`
- add one finalization regression test
- change only the two task statuses above from `ready` to `done`

## Non-goals

- no design changes
- no route/content changes
- no database changes or migrations
- no publication/cutover
- no commit/push
- no reset/restore/clean

## Preconditions

- main branch
- Alembic `20260827_0004`
- `ISI-03C-MEDIA-REDIRECT-VALIDATION` is `done`
- both exact ISI-04/04B task IDs are `ready` or already `done`
- HOTFIX-8 visual baseline exists

## Acceptance

- exact task IDs are `done`
- browser visual QA acceptance record exists and is `PASS`
- focused finalization test passes
- full test suite passes
- Alembic remains `20260827_0004`
- `git diff --check` passes
