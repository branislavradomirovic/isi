# ISI-04B HOTFIX-1 — Knowledge Model Registry Bootstrap

## Trigger
The ISI-04B migration reached `20260827_0004`, but the native PostgreSQL seed CLI failed with `sqlalchemy.exc.NoReferencedTableError` because `knowledge_sources.organization_id` references `core_organizations.id` while the clean CLI process had not registered the identity model metadata.

## Root cause
The unit seed test imported `src.platform.models` before seeding, masking the production-like CLI bootstrap gap. The CLI imported `src.knowledge.seed` directly. SQLAlchemy therefore knew about `knowledge_sources` but not its external FK target table when mapper dependency sorting ran during `Session.flush()`.

## Fix
1. Register the direct ORM dependency from `src.knowledge.models` to `src.platform.identity.models.Organization`.
2. Make the seed CLI explicitly import the platform aggregate model registry before performing ORM work.
3. Add an isolated-subprocess regression test that starts with a clean Python process and exercises the same seed path without relying on test-suite import order.

## Safety
- no new migration
- Alembic remains `20260827_0004`
- do not roll back the already-applied migration
- seed remains idempotent
- all public pages and enriched sections remain draft
- no embeddings, vector or chunk tables
- no publication, redirect activation, commit or push

## Acceptance
- isolated clean-process model-registry regression passes
- domain/source/section seed completes against native PostgreSQL
- repeated seed completes idempotently
- native PostgreSQL ISI-04B acceptance passes
- full pytest suite passes
- visual QA remains pending after technical recovery
