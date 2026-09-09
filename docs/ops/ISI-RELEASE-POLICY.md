# ISI Release Policy

All changes use a dedicated branch, reviewed pull request, task specification, deterministic acceptance, and recorded evidence. Required checks are blocking and may not be bypassed or changed to allowed-to-fail to merge a defect.

Release candidates derive from reviewed commits on the protected default branch. A release uses an immutable, unique tag, release notes/changelog describing changes, migrations, compatibility and known limitations, and artifacts tied to the exact commit with SHA-256 checksums. Deployment is allowed only from an owner-approved release candidate; a casual production `git pull` is not the operating model.

The release record must identify source SHA, tag, builder/workflow, artifact checksums, approvals, migration plan and rollback procedure. Rollback instructions must cover application artifacts and database compatibility/backups before deployment approval. Production secrets never enter artifacts or release notes.

Signed tags/releases, generated SBOMs, artifact attestations and image vulnerability enforcement are mandatory target controls for ISI-27. Until then, checksums and immutable commit identity are required, and the missing signing/SBOM provenance must be stated as deferred rather than implied.
