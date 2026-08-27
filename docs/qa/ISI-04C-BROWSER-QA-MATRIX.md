# ISI-04C Browser QA Matrix

Manual sign-off is required after the runner passes.

## Viewports

| Browser | Desktop | Tablet | Mobile |
| --- | --- | --- | --- |
| Chrome | 1440x900 | 1024x768 | 390x844 |
| Safari | 1440x900 | 1024x768 | 390x844 |
| Firefox | 1440x900 | 1024x768 | 390x844 |

## Pages

- `/`
- `/simpa/`
- `/ordo/`
- `/aktivnosti/`
- `/dokumenti/`
- `/biblioteka/`
- `/inkluzivni-razvoj/`
- representative legacy/institutional page
- one English route under `/en/`
- a nonexistent public route for the branded 404

## Checks

- Header never overlaps content and the official ISI logo has no white-box artifact.
- SIMPA/ORDO navigation marks and flagship lockups remain visible and legible.
- Mobile nav opens, closes, closes with Escape and restores focus to the toggle.
- No horizontal page overflow at the three target widths.
- Headings remain readable; cards collapse in a logical order.
- Keyboard Tab order follows visual/document order.
- Every interactive element has a visible focus indicator.
- Active navigation announces the current page.
- Search controls have an accessible text label.
- Meaningful activity images have descriptive alt text; purely decorative art has empty alt text.
- `prefers-reduced-motion` removes nonessential transitions/animation.
- `/robots.txt`, `/sitemap.xml`, `/site.webmanifest`, `/favicon.ico` return 200.
- Preview pages contain `noindex,nofollow`.
- Canonical and language alternate links are correct.
- Public 404 is branded; `/api/v1/definitely-missing` remains JSON 404.

## Acceptance

Run `record-ISI-04C-VISUAL-QA-PASS.sh` only after all applicable checks pass.
