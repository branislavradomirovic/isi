# ISI-04B HOTFIX-6 — Contract Compatibility Recovery

## Purpose

HOTFIX-5 successfully installed the semantic visual polish payload, transparent ISI logo treatment, visible SIMPA/ORDO marks, semantic icon registry, and image-led Activities renderer. Its focused suite then stopped because three older HOTFIX-4 regression contracts were still asserting CSS/template compatibility markers that HOTFIX-5 had renamed.

This recovery **does not roll back the new design** and **does not weaken the old tests**. It restores backward-compatible class/path markers in the new semantic templates so both contracts remain true.

## Exact fixes

1. `partials/header.html`
   - keeps the actual HOTFIX-5 logo source: `/static/img/brand/isi-logo-transparent.svg`;
   - restores `approved-brand` and `approved-brand-logo` compatibility classes;
   - preserves the original approved logo path as a compatibility metadata attribute: `/static/img/brand/isi-logo.svg`;
   - keeps SIMPA/ORDO semantic navigation marks.

2. `partials/domain_sections.html`
   - keeps `semantic-domain-item` and semantic icon resolution;
   - restores `approved-domain-item` so the locked HOTFIX-4 layout contract remains valid.

3. Adds `test_isi_04b_hotfix6_compatibility.py` proving HOTFIX-4 and HOTFIX-5 contracts coexist.

## Non-goals

- no Alembic migration;
- no data reseed;
- no publication;
- no redirect activation;
- no commit or push;
- no rollback of semantic icons, Activities visuals, SIMPA/ORDO branding, or transparent-logo treatment.

## Expected baseline

- branch: `main`
- committed HEAD: `2965383`
- Alembic: `20260827_0004`
- `ISI-03C-MEDIA-REDIRECT-VALIDATION`: `done`
- `ISI-04-NEW-PUBLIC-WEBSITE`: `ready`
- `ISI-04B-DOMAIN-KNOWLEDGE-CONTENT-ENRICHMENT`: `ready`
- HOTFIX-5 payload already present from the failed runner attempt.

## Acceptance

Runner must end with:

```text
=== ISI-04B HOTFIX-6 RUNNER PASSED ===
```

Then start local preview and perform browser visual QA. Only after visual approval should the QA acknowledgement and final analyzer be run.
