# ISI-27C R2 — limited minimal-runtime base proposal

## Decision status

APPROVED AND IMPLEMENTED — the owner authorized this exact bounded runtime-base slice on 2026-10-04. The image/runtime and deterministic gates passed, and the reviewed implementation is accepted on main `b6f0bfaf453360da72f866d4bbd1d47b51655bf4` with candidate fingerprint `7dc381dd31d94e6ada447c7cffc945399bddbe4a7ec138ec88ae69e77e9be8ea`. CI_VERIFIED and SERVER_VERIFIED remain false. This approval does not authorize bypassing 27D or ISI-28.

Canonical main baseline: `16a928b20907d570df2cf05101a969e1f0cda736`.
Preserve the valid unstaged 27C R1 candidate and all accepted predecessor work.

## Actual blocker and alternatives checked

The real Trivy 0.75.0 scan of Python 3.11-slim / Debian 13.7 failed HIGH/CRITICAL
acceptance. Stable Debian has no fix for the observed util-linux, ncurses and
systemd source-package advisories. Debian bookworm was checked in the same
primary tracker and is also affected; changing only the Debian tag does not
resolve those findings. A narrow urllib3 2.7.0 -> 2.8.0 correction and removal of
build-only pip/setuptools/wheel are in the R1 candidate. Python dependency audit
now reports no known vulnerabilities. No finding is ignored or downgraded.

Primary records:
- https://security-tracker.debian.org/tracker/CVE-2026-76642
- https://security-tracker.debian.org/tracker/CVE-2026-78408
- https://security-tracker.debian.org/tracker/CVE-2025-69720
- https://security-tracker.debian.org/tracker/CVE-2026-16742
- https://github.com/urllib3/urllib3/security/advisories

## Proposed supplier and exact initial input

Use the publicly accessible `cgr.dev/chainguard/wolfi-base` with observed immutable
index digest `sha256:9c2092b053779e14c82fb50f77b37bcc38b7d2c83972352d5813280f9d035b03`.
Read-only package query on that digest confirmed its own repository is
`https://apk.cgr.dev/chainguard` and available packages include:

| Package | Observed version |
|---|---|
| python-3.11 | 3.11.17-r1 |
| py3.11-pip (builder only) | 26.2.1-r2 |
| libstdc++ | 16.2.0-r1 |
| libgcc | 16.2.0-r1 |
| ca-certificates-bundle (runtime) | 20260909-r2 |
| tzdata (runtime, required by the existing UTC timezone contract) | 2026e-r0 |

Supplier references:
- https://github.com/wolfi-dev/os
- https://github.com/wolfi-dev/os/blob/main/python-3.11.yaml
- https://edu.chainguard.dev/chainguard/containers/concepts/choosing-a-base-container/

This is a proposed community-accessible runtime foundation, not an Enterprise
support/SLA purchase and not evidence of zero vulnerabilities. Use one supplier
repository; do not mix Alpine, Debian or other distributions' libraries/packages.
Resolve and record the complete installed APK set, supplier SBOM/package hashes,
architecture and actual image digest. Pin explicitly requested versions. If the
pinned input is withdrawn, incompatible or vulnerable, fail and revise the
contract transparently rather than silently following `latest` or Python 3.13+.

## Exact authorized surface if approved

- this proposal and `automation/specs/ISI-27C-R1-REPRODUCIBLE-RELEASE-SUPPLY-CHAIN.md`
- `docker/Dockerfile`: same app image and service entrypoints; staged builder and
  minimal runtime, pinned supplier digest/Python packages, isolated Python 3.11
  virtual environment, existing locks and application package
- `docker/runtime-base.lock.json`: exact supplier/base/requested package identity
  plus scope of transitive installed-package evidence
- `tools/release/build.py`, `tools/release/sbom.py`: validate actual Wolfi image
  OS/platform/OCI metadata and installed SBOM without weakening vulnerability gates
- `tools/qa/run_isi27c.py`, `tools/qa/analyze_isi27c.py`: extend exact surface and
  add actual runtime compatibility results with immutable report hashes
- `tools/qa/check_runtime_image.py`: disposable image compatibility runner
- `tests/test_isi_27c_release_supply_chain.py` and
  `tests/test_isi_27c_runtime_image_contract.py`: supplier/version/metadata,
  compatibility and negative controls
- `.github/workflows/ci.yml`: add runtime compatibility to the existing manual
  build gate and retain every inherited aggregate dependency
- `docs/release/ISI-RELEASE-SUPPLY-CHAIN.md`
- `docs/ops/ISI-DEVELOPMENT-WORKSTATION-REQUIREMENTS.md`
- `docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md`
- `TECHNICAL_DOCUMENTATION.md`, `automation/STATUS.md`, `automation/tasks.json`

No unrelated dependency updates, application refactor, schema/API changes,
product/domain semantics, AI providers, background scheduling, production users,
secrets, ingress, DNS, SMTP or server data changes belong to R2.

## Compatibility and acceptance contract

1. Python remains 3.11.x; FastAPI, Streamlit, NumPy/SciPy/statsmodels, PyArrow,
   psycopg, Redis/RQ, boto3 and all remaining application locks retain their
   existing versions except the already scoped urllib3 security correction.
2. Keep current `/app`, `python`, `alembic`, API/Streamlit ports/base path, worker
   modules and Compose commands. Preserve existing service identity/volume
   ownership contract; any production UID change belongs to ISI-28 review.
3. Build-only package tools stay out of the runtime virtual environment; no
   compiler or distro package mixing is introduced to make wheels import.
4. Execute real image import/SSL/locale/timezone and command checks; start API and
   Streamlit in disposable local services with synthetic configuration; check
   health/public routing/static readiness and invitation-only boundaries. Test
   scientific binary imports and a deterministic non-domain numerical operation.
5. Execute unchanged full regression, native PostgreSQL/migrations/restore,
   object restore, all performance scenarios, Compose, quality, policy, audit,
   SAST and secret gates. Run image-level test probes on the actual final image,
   separately from development/test-tool layers.
6. Real Trivy 0.75.0 image scan and SBOM must bind the same final image/config
   digest/source fingerprint. HIGH/CRITICAL, including unfixed, still block.
   No ignore/VEX exemption, skip, weakened assertion or soft failure is introduced.
7. Actual amd64 verification is mandatory for the known target; arm64 must be
   assessed before claiming cross-workstation/container portability. Record
   unsupported architecture honestly instead of assuming wheel compatibility.
8. Read-only independent analysis and assistant review must pass before the
   already authorized exact-file main commit/push. 27D hosted exact-main
   checkpoint and usage pre/post checks remain separate. Only ISI-28 may deploy.
9. The immutable source archive and exact image bundle retain owner-signed
   provenance and original source/data/auth/methodology boundaries. Preserve
   prior image/archive as rollback evidence; no destructive Docker/Git cleanup.

Canonical system inventory impact: revise the existing image/build/runtime
supplier rows and INV-M21/INV-K15/INV-J32 as-built only after actual implementation
and validation. This proposal alone does not claim the new base is installed.

## Implementation and stop conditions

The approved implementation is the multi-stage Docker build using the immutable Wolfi base digest, explicitly pinned Python 3.11 and pip packages, and an isolated runtime virtual environment. The runtime stage excludes build-only pip/setuptools/wheel packages. The exact runtime also pins certificate and timezone data so the existing SSL and UTC contracts are available in the minimal image. `docker/runtime-base.lock.json` records the supplier and explicit pins; actual transitive OS and Python components remain bound by the final image SBOM and digest. An unavailable pinned package, incompatible binary wheel, failed runtime check, new HIGH/CRITICAL vulnerability, unclassified supplier boundary or failed acceptance stops promotion and deployment. This slice does not certify production readiness or bypass 27D/ISI-28.
