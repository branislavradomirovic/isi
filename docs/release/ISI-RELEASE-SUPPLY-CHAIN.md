# ISI release supply-chain contract

27C builds development evidence; 27D accepts the exact committed main release.
No local candidate, unsigned bundle or source-only archive authorizes deployment.

## Source and image

`python -m tools.release.build --output <new-directory>` requires clean canonical
main and an empty index. It produces a deterministic committed source archive,
lock-only CycloneDX SBOM and source manifest. Output is exclusive and never
replaces an earlier artifact. Source-only output is explicitly not release-qualified.

The manually dispatched required acceptance workflow retains every inherited
quality, policy, domain/security, migration, native PostgreSQL, recovery, Compose,
dependency/SAST/secret and build gate. Performance evidence and release-bundle
assembly are additional blocking gates. Trivy 0.75.0 uses the pinned official
v0.36.0 action. HIGH/CRITICAL installed-image vulnerabilities, including unfixed
findings, block. No ignore list or soft-failure path is provided.

The image archive, OCI source/revision, actual image/config digest, platform,
Trivy JSON and installed-image CycloneDX SBOM are recorded together. The lock
SBOM describes declared pinned dependencies; it does not replace the installed
OS/library inventory. The bundle binds the real RC evidence pack to the same
source SHA/tree and candidate fingerprint.

## Provenance and trust

The hosted job uploads unsigned bundle metadata after all upstream jobs succeed.
The large image archive is retained once in `isi-exact-image`, avoiding duplicate
storage against the verified GitHub Free 0.5GB allowance. 27D downloads both
artifacts from the same successful exact-SHA run, restores `image.tar.gz` into
the bundle, then verifies every bound digest before signing.
The manifest binds every payload digest. An in-toto statement binds the manifest
and source/image identities. At 27D the owner-authorized local release process
validates the actual successful workflow/SHA and signs the statement through the
existing SSH agent, namespace `isi-release`. No private key enters CI, source,
fixtures, screenshots or evidence. `allowed_signers` pins the owner's existing
GitHub public keys; an untrusted bundle cannot supply its own trust authority.

`python -m tools.release.provenance <bundle> --sign-public-key <local-public-key>`
first validates the unsigned bundle, signs and independently verifies the result.
Verification rejects unexpected files, symlinks, path traversal, missing files,
changed digests, unsigned provenance and invalid/untrusted signatures.

This is ISI owner-signed provenance. It is not a SLSA certification or a GitHub
Enterprise artifact attestation. GitHub Free/private does not provide that
Enterprise feature. No private repository metadata is submitted to public Rekor.

## Acceptance and retention

Local runner and independent analyzer record regression/native/recovery,
performance, quality, policy, Compose and image evidence against unchanged source.
The separate 27D checkpoint requires exact-main hosted success plus Actions
usage observations before and after. CI artifacts use one-day image/bundle
retention; download, verification and local retention occur during that cycle.
The ISI-28 contract owns server audit, migration, rollback and server acceptance.
Krcuga and OralScanXAI remain outside the deployment target.
