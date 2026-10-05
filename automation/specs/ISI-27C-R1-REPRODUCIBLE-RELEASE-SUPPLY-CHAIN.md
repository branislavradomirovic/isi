# ISI-27C R1 — reproducible release and supply-chain assurance

## Status and baseline

Locked implementation contract, canonical main
`16a928b20907d570df2cf05101a969e1f0cda736`, clean and equal to GitHub main.
27B is accepted on that SHA: regression 1071 passed / 43 intentional native skips,
native PostgreSQL 45 passed / 0 skipped, PostgreSQL/object restore PASS, all 10
performance scenarios accepted. Independent analysis/review PASS. Pack SHA256
`9da45b26e811b6320c951e4285f83353aa306413c96052d5a75112b5ec67c8c1`, candidate
fingerprint `d97b16ce6f3cd179d8fca5b05e838d6644a6eda1bdff61c2399c4b0952e22a86`.
Archive comparison proves the accepted commit exactly matches the reviewed files.
Owner approved continued implementation, reviewed-candidate commit/push and final
deployment. Hosted dispatch retains the explicit 27D checkpoint and usage gate.

## Bootstrap, dependency and drift classification

DONE: 27A, public remediation, 27B local/review/main acceptance.
MISSING: portable immutable artifact, exact image SBOM, signed provenance and
blocking image scan; current exact-main hosted acceptance; current server audit.
The last hosted acceptance remains run 35238623960 on predecessor 5937daa2.
GitHub Free/private was verified through authenticated Billing web: 51/2000
minutes and 0/0.5GB storage. Refresh immediately before/after any hosted cycle.

Historical tests freezing live 27B status are REMOVE_BEFORE_NEXT_SLICE. Replace
only mutable checkpoint assertions with strict serial dependency/evidence guards;
preserve immutable predecessor facts and all tampering/negative controls.
Old release/deployment scripts are REQUIRED_COMPATIBILITY until named ISI-28
replacement. Pre-acceptance R1 specs/analyzers become LEGITIMATE_HISTORY with
truthful accepted-main annotations. Generated acceptance output is ignored and
not a runtime dependency. No domain/auth/data/AI boundary is redefined.

## Objective and exact mutable surface

- this contract
- automation/specs/ISI-27C-R2-MINIMAL-RUNTIME-BASE-PROPOSAL.md (owner-approved bounded implementation)
- docker/runtime-base.lock.json
- tools/qa/check_runtime_image.py
- tests/test_isi_27c_runtime_image_contract.py
- automation/specs/ISI-27B-ACCEPTANCE-EVIDENCE.json
- automation/specs/ISI-27B-R1-RC-EVIDENCE-GOVERNANCE-PACK.md
- automation/specs/ISI-PUBLIC-PORTAL-AUDIT-REMEDIATION-R1.md (accepted-history annotation only)
- tools/release/build.py
- tools/release/sbom.py
- tools/release/provenance.py
- tools/release/governance.py
- tools/release/assemble.py
- tools/release/allowed_signers
- tools/release/build_server_release.sh
- tools/qa/run_isi27c.py
- tools/qa/analyze_isi27c.py
- tests/test_isi_27c_release_supply_chain.py
- tests/fixtures/isi27_signature_message.json
- tests/fixtures/isi27_signature_message.json.sig
- tests/test_isi_27_scope_contract.py
- tests/test_isi_27a_shared_help_contract.py
- tests/test_isi_26_governance_contract.py
- tests/test_isi_17_harness_contract.py
- .github/workflows/ci.yml
- .gitignore
- .dockerignore (exclude generated test/image/scanner output)
- docker/Dockerfile (OCI source identity and removal of build-only vulnerable tooling)
- requirements.lock (urllib3 security fix only)
- requirements.runtime.lock (matching urllib3 security fix only)
- docs/release/ISI-RELEASE-SUPPLY-CHAIN.md
- docs/ops/ISI-DEVELOPMENT-WORKSTATION-REQUIREMENTS.md
- docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md
- TECHNICAL_DOCUMENTATION.md
- automation/STATUS.md
- automation/tasks.json

Canonical system inventory impact: INV-M20 acceptance update, new INV-M21
release/supply-chain authority, existing aggregate CI/build/deployment tool rows
reconciled with their actual ownership. No new customer-facing capability.

## Required implementation and acceptance

1. Clean canonical main only; portable Python-standard-library hashing,
   deterministic git archive + gzip with fixed metadata; exclusive new output
   directory. Exact SHA/tree, no ignored environments or credentials.
2. CycloneDX dependency-lock SBOM with explicit lock-only scope; independent real
   Trivy image SBOM including OS and installed library components.
3. Image identity/OCI revision and image archive digest bound to exact source.
   Trivy 0.75.0, official action pinned to commit
   ed142fd0673e97e23eac54620cfb913e5ce36c25 (v0.36.0). HIGH/CRITICAL image findings
   block, including unfixed findings; inherited dependency/SAST/secret gates stay
   blocking. No broad exclusions, soft failure or automatic CI trigger. The
   owner-approved exact historical Gitleaks fingerprint exception recorded in
   the ISI-27D scope lock applies only to its enumerated findings; it does not
   exclude paths, rules, commits or any other finding.
4. Manifest binds RC pack, source archive, both SBOM scopes, image identity/scan
   and checksums. Owner-signed in-toto provenance via existing SSH identity,
   namespace isi-release, pinned existing GitHub owner public keys. Never claim
   GitHub Enterprise artifact attestation or SLSA certification. Private keys
   remain machine-local; unit fixtures contain public message/signature only.
5. Manual hosted workflow consolidates actual upstream reports and uploads an
   unsigned candidate bundle. 27D downloads, checks actual exact-SHA job success,
   signs and independently verifies it before release acceptance. No production
   key/secret is added to hosted CI. Image artifact retention is bounded.
6. Unit negative controls cover dirty/non-main source, invalid/missing locks,
   artifact tampering, identity/scan/pack mismatch, missing signature, immutable
   output and serial governance transitions. Local deterministic archive repeat,
   real signing verification, full regression, native/migration/recovery,
   compose/quality/policy and image scan are required as available.
7. Independent analyzer remains read-only, validates exact mutable surface and
   source fingerprint plus real gate/artifact hashes. Human review precedes
   authorized exact staging/main commit/push. CI_VERIFIED and SERVER_VERIFIED
   remain false until real later checkpoint results.

## Boundaries and handoff

No runtime domain calculation, model promotion, methodology, schema, enrollment,
tenant/product authorization, provider, worker or scheduler changes. No server,
central ingress, DNS, SMTP, production secret/data or Ollama access. ISI-28 remains
the sole deployment phase after 27D; Krcuga/OralScanXAI remain strict non-targets.
Terms/Privacy publication is a separate owner-approved portal content slice and
must be included in the final exact-source acceptance before production cutover.

## Observed security drift and bounded correction — 2026-10-04

Real Trivy 0.75.0 scan of the current Python 3.11/Debian 13.7 candidate
failed the HIGH gate. urllib3 2.7.0 is affected by CVE-2026-97687/97689;
upstream 2.8.0 fixes these (and a moderate streaming issue). Both locks receive
only that security update. Vulnerable base build-only setuptools/wheel tooling
is removed after installation; runtime dependencies and Python stay unchanged.
No broad dependency upgrade is authorized or performed.

Stable Debian util-linux/ncurses/systemd source-package advisories also have
unfixed HIGH findings. Classify REMOVE_BEFORE_NEXT_SLICE: retain actual scan,
resolve or obtain a separately justified runtime-base contract before 27C
acceptance. Do not mark this candidate accepted, ignore findings, enable 27D/28
or deploy while the image gate fails. The failed image is development evidence.
Primary references: https://github.com/urllib3/urllib3/security/advisories and
https://security-tracker.debian.org/tracker/CVE-2026-76642 ;
https://security-tracker.debian.org/tracker/CVE-2025-69720 .

## Approved runtime-base R2 implementation

After the Debian image gate failed, the owner approved bounded implementation of
`ISI-27C-R2-MINIMAL-RUNTIME-BASE-PROPOSAL.md`. The R2 exact surface extends this
R1 acceptance contract. Source, installed-image SBOM, vulnerability scan, actual
runtime image and all inherited gates must pass before 27C can be accepted.
The R2 exact-image and full local acceptance evidence is retained by candidate
fingerprint under `automation/evidence/ISI-27C/`; the scan/runtime, all local
gates, independent analysis and human review passed. The implementation is
accepted on main `b6f0bfaf453360da72f866d4bbd1d47b51655bf4` (tree
`8d52631012121c078d077a39d75e201d4ffadcbd`, candidate fingerprint
`7dc381dd31d94e6ada447c7cffc945399bddbe4a7ec138ec88ae69e77e9be8ea`). 27C is
not CI_VERIFIED or SERVER_VERIFIED. 27D is the next specification-ready gate;
ISI-28 remains locked until 27D closeout and separate owner approval.

## Owner-approved 27D historical secret-scan fingerprint exception — 2026-10-05

During the first 27D run (#91, source SHA
`61a11c1ff839e66a458ac77ed05d4c860214f267`), Gitleaks reported 11
`generic-api-key` findings in repository history. The owner approved a baseline
for only those context-reviewed findings. `.gitleaksignore` records the exact
commit/path/rule/line fingerprints; `tests/test_isi_27d_gitleaks_baseline.py`
locks that list to exactly those 11 entries. Full-history scanning remains
enabled. Any finding not matching one of those exact fingerprints remains a
blocking failure; dependency, SAST and image-scan gates are unaffected. The
baseline has not yet been verified by a subsequent hosted acceptance run.
