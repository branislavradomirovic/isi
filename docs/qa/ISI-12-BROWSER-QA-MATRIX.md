# ISI-12 Browser QA Matrix

Use the dual demo account and also check one product-only negative control.

## Shared shell
- Login succeeds and opens one browser tab.
- `Izveštaji` is a real module, not the old ISI-12 placeholder.
- Product switching SIMPA <-> ORDO preserves the selected organization/workspace context without showing the other product's report sources.

## SIMPA
- Create a `Monitoring summary` from a real SIMPA analytics snapshot.
- Draft shows content and provenance checksums.
- Evidence-quality values are labelled as coverage/quality, never social-risk or municipality scores.
- Submit -> approve -> publish is visibly explicit.
- Review trail is visible.
- HTML/Markdown/JSON download artefact is available only after approval.

## ORDO
- Create a `Destination snapshot` from a real ORDO analytics snapshot.
- If a scenario assessment exists, `Scenario review` is available for that source.
- Scenario review visibly states evidence-only / `forecast_performed=false`.
- No invented forecast effect appears.
- Submit -> approve -> publish is visibly explicit.
- Provenance contains ORDO sources only.

## Isolation
- SIMPA-only account cannot access ORDO reporting API or report registry.
- Switching products never shows report sources or versions from the other product.

## Visual quality
- No traceback/raw JSON dump in normal UI.
- Provenance is readable and not hidden.
- Lifecycle/status is obvious.
- Report content is editorial/institutional, not a generic admin table dump.
- Export action clearly identifies format and immutable SHA-256.

Record visual QA only after all checks are accepted.
