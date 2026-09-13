# ISI Release Policy

This policy is subordinate to the canonical MasterPlan.

## Development-to-main policy

Normal industrialization development uses one canonical local repository, one worktree and direct `main`; a feature branch or pull request is not required and must not be introduced without an explicit owner exception.

Every change still requires a locked specification/scope, deterministic acceptance, independent analysis where defined, assistant human review, explicit owner approval before exact-file staging, direct commit/push to `main`, and `ISI required acceptance` completed/success on the exact main SHA. Required checks are blocking and may not be weakened to accept a defect.

## Release-candidate policy

ISI-27 owns the industrial release-candidate/acceptance pack. Release candidates derive from exact CI-verified main commits and use immutable identity, checksums, release notes/changelog, migration/compatibility/known-limitations records, security/privacy/methodology acceptance, backup/restore proof and rollback instructions. Signed provenance/SBOM/attestations and image vulnerability enforcement are ISI-27 target controls.

## Production deployment policy

Only owner-approved ISI-28 may perform current-server deployment, DNS/ingress, real SMTP, production secret/data or server Ollama mutation. Deployment is release-based rather than a casual production `git pull`. Historical ISI-15/ISI-16 deployment documents are not current execution authority.
