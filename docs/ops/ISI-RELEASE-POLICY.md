# ISI Release Policy

This policy is subordinate to the canonical MasterPlan.

## Development-to-main policy

Normal industrialization development uses one canonical local repository, one worktree and direct `main`; a feature branch or pull request is not required and must not be introduced without an explicit owner exception.

Every change still requires a locked specification/scope, deterministic local acceptance, independent analysis where defined, assistant human review and explicit owner approval before exact-file staging and direct commit/push to `main`. Development pushes do not automatically start full GitHub-hosted CI. For an explicitly approved acceptance/release checkpoint, GitHub Actions usage is checked, `ISI required acceptance` is manually dispatched with `workflow_dispatch` against the exact main SHA, every required check remains blocking, and Actions usage is checked again after the cycle. Required checks may not be weakened to accept a defect.

## GitHub Actions cost and acceptance policy

Full GitHub-hosted CI is reserved for explicitly approved acceptance, release-candidate or production checkpoints. Local tests, deterministic package runners and analyzers are the development validation lane. The canonical full acceptance workflow defaults to manual `workflow_dispatch`; automatic `push:`, `pull_request:`, `schedule:` or equivalent billable triggers require fresh explicit owner approval. GitHub Actions usage is checked before and after every approved acceptance/release cycle.

## Release-candidate policy

ISI-27 owns the industrial release-candidate/acceptance pack. Release candidates derive from exact CI-verified main commits and use immutable identity, checksums, release notes/changelog, migration/compatibility/known-limitations records, security/privacy/methodology acceptance, backup/restore proof and rollback instructions. Signed provenance/SBOM/attestations and image vulnerability enforcement are ISI-27 target controls.

## Production deployment policy

Only owner-approved ISI-28 may perform current-server deployment, DNS/ingress, real SMTP, production secret/data or server Ollama mutation. Deployment is release-based rather than a casual production `git pull`. Historical ISI-15/ISI-16 deployment documents are not current execution authority.
