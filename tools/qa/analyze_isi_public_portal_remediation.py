from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "3e652e392624b3903498a1c2a00024306e6308d1"
ALLOWED = {
    "automation/STATUS.md",
    "automation/specs/ISI-PUBLIC-PORTAL-AUDIT-REMEDIATION-R1.md",
    "automation/tasks.json",
    "src/public/catalog_service.py",
    "src/public/routes.py",
    "src/public/static/css/semantic-polish.css",
    "src/public/templates/index.html",
    "src/public/templates/inclusive_development.html",
    "src/public/templates/partials/footer.html",
    "tests/test_isi_04c_public_portal_remediation.py",
    "tests/test_isi_04c_seo_routes.py",
    "tests/test_isi_27a_public_help_contract.py",
    "tools/qa/analyze_isi_public_portal_remediation.py",
    "tools/qa/run_isi_public_portal_remediation.py",
    "automation/specs/ISI-PUBLIC-LEGAL-NOTICES-DRAFT-R1.md",
    "docs/legal/ISI-LEGAL-NOTICES-RELEASE-CHECKLIST.md",
    "docs/legal/ISI-PRIVACY-NOTICE-DRAFT.md",
    "docs/legal/ISI-PUBLIC-TERMS-DRAFT.md",
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).rstrip("\n")


def main() -> int:
    if git("branch", "--show-current") != "main":
        raise SystemExit("FAIL: candidate is not on canonical main")
    if git("rev-parse", "HEAD") != BASELINE or git("rev-parse", "origin/main") != BASELINE:
        raise SystemExit("FAIL: baseline or local origin/main ref changed")

    status = git("status", "--porcelain=v1", "--untracked-files=all")
    changed: set[str] = set()
    staged: list[str] = []
    for line in status.splitlines():
        code, path = line[:2], line[3:]
        if code[0] not in {" ", "?"}:
            staged.append(path)
        changed.add(path)
    if staged:
        raise SystemExit(f"FAIL: staged changes found: {staged}")
    unexpected = sorted(changed - ALLOWED)
    if unexpected:
        raise SystemExit(f"FAIL: changes outside the locked surface: {unexpected}")
    for line in status.splitlines():
        if line.startswith("??"):
            path = line[3:]
            if any(row.endswith((b" ", b"\t")) for row in (ROOT / path).read_bytes().splitlines()):
                raise SystemExit(f"FAIL: trailing whitespace in new file: {path}")

    snapshot = json.loads((ROOT / "data/migration/legacy_isi/snapshots/f9b1f91356a536111f721822.json").read_text())
    from src.public.catalog_service import document_catalog_from_html

    items = [item for group in document_catalog_from_html(snapshot["body_html"]) for item in group.items]
    if len(items) != 26:
        raise SystemExit(f"FAIL: expected 26 preserved document entries, got {len(items)}")

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=False)
    if diff_check.returncode:
        raise SystemExit("FAIL: git diff --check")

    digest = hashlib.sha256()
    for path in sorted(changed):
        digest.update(path.encode())
        digest.update(b"\0")
        digest.update((ROOT / path).read_bytes())
        digest.update(b"\0")
    print(json.dumps({"result": "PASS", "changed_paths": sorted(changed), "document_items": len(items), "candidate_fingerprint": digest.hexdigest()}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
