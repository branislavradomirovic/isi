from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_official_logo_uses_transparent_derivative_without_modifying_source():
    manifest = json.loads((ROOT / "data/public/isi_brand_manifest.json").read_text(encoding="utf-8"))
    source = ROOT / manifest["source_path"]
    transparent = ROOT / manifest["transparent_served_path"]
    assert source.exists()
    assert transparent.exists()
    assert _sha(source) == manifest["source_sha256"]
    assert _sha(transparent) == manifest["transparent_served_sha256"]
    assert manifest["transparent_served_url"] == "/static/img/brand/isi-logo-transparent.svg"

    header = (ROOT / "src/public/templates/partials/header.html").read_text(encoding="utf-8")
    css = (ROOT / "src/public/static/css/semantic-polish.css").read_text(encoding="utf-8")
    assert "/static/img/brand/isi-logo-transparent.svg" in header
    assert "mix-blend-mode: multiply" in css


def test_simpa_ordo_marks_are_visible_in_header_home_and_platform():
    header = (ROOT / "src/public/templates/partials/header.html").read_text(encoding="utf-8")
    home = (ROOT / "src/public/templates/index.html").read_text(encoding="utf-8")
    platform = (ROOT / "src/public/templates/platform.html").read_text(encoding="utf-8")
    for path in ("/static/img/simpa-mark.svg", "/static/img/ordo-mark.svg"):
        assert path in header
        assert path in home
        assert path in platform
    assert (ROOT / "src/public/static/img/simpa-mark.svg").stat().st_size > 200
    assert (ROOT / "src/public/static/img/ordo-mark.svg").stat().st_size > 200


def test_retired_initiatives_absent_from_public_design_templates():
    public_templates = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (ROOT / "src/public/templates").rglob("*.html")
    ).casefold()
    for token in (
        "ancsee",
        "academic network for cooperation",
        "wbsib",
        "western balkan social inclusion barometer",
    ):
        assert token not in public_templates
