from pathlib import Path

REQUIRED = [
    "src/public/templates/partials/seo_meta.html",
    "src/public/templates/errors/404.html",
    "src/public/static/css/public-readiness.css",
    "src/public/static/js/public-readiness.js",
    "src/public/readiness_routes.py",
    "src/public/error_handlers.py",
    "docs/qa/ISI-04C-BROWSER-QA-MATRIX.md",
]

for name in REQUIRED:
    path = Path(name)
    if not path.exists() or path.stat().st_size == 0:
        raise SystemExit(f"missing readiness artifact: {name}")

base = Path("src/public/templates/base.html").read_text()
header = Path("src/public/templates/partials/header.html").read_text()
css = Path("src/public/static/css/public-readiness.css").read_text()
js = Path("src/public/static/js/public-readiness.js").read_text()

checks = {
    "seo partial": 'partials/seo_meta.html' in base,
    "favicon manifest": '/site.webmanifest' in Path("src/public/templates/partials/seo_meta.html").read_text(),
    "aria current": 'aria-current="page"' in header,
    "mobile breakpoint": '@media (max-width: 980px)' in css,
    "mobile compact breakpoint": '@media (max-width: 680px)' in css,
    "reduced motion": 'prefers-reduced-motion: reduce' in css,
    "escape nav": "event.key === 'Escape'" in js,
}
failed = [label for label, ok in checks.items() if not ok]
if failed:
    raise SystemExit("readiness audit failed: " + ", ".join(failed))
print("Public readiness static audit PASS")
