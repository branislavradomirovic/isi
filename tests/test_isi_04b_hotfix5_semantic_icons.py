from __future__ import annotations

import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.public.semantic_icons import activity_icon, document_icon, semantic_icon


ROOT = Path(__file__).resolve().parents[1]


def _sprite_ids() -> set[str]:
    text = (ROOT / "src/public/static/img/icons.svg").read_text(encoding="utf-8")
    return set(re.findall(r'<symbol\s+id="([^"]+)"', text))


def test_every_seeded_domain_item_has_a_specific_existing_icon():
    registry = json.loads((ROOT / "data/public/domain_sections.json").read_text(encoding="utf-8"))
    sprite = _sprite_ids()
    failures = []
    for section in registry["sections"]:
        for item in section["items"]:
            label = item["translations"]["sr-Latn"]["label"]
            icon = semantic_icon(
                section["section_key"],
                item["item_key"],
                item["domain_code"],
                label,
                item["item_kind"],
            )
            if icon not in sprite or icon == "domain":
                failures.append((section["section_key"], item["item_key"], label, icon))
    assert not failures, failures


def test_document_and_activity_icon_policies_are_semantic():
    assert document_icon("Strategija") == "strategy"
    assert document_icon("Smernice") == "guideline"
    assert document_icon("Izveštaj") == "report"
    assert activity_icon("Konferencija") == "conference"
    assert activity_icon("Radionica") == "workshop"
    assert activity_icon("Javni dijalog") == "dialogue"
    assert activity_icon("Obuka") == "training"


def test_domain_template_uses_semantic_policy_not_visual_kind_heuristic():
    text = (ROOT / "src/public/templates/partials/domain_sections.html").read_text(encoding="utf-8")
    assert "semantic_icon(section.key" in text
    assert "section.visual_kind in ['timeline'" not in text
    assert "set icon='network'" not in text


def test_all_hotfix5_templates_parse():
    env = Environment(loader=FileSystemLoader(str(ROOT / "src/public/templates")))
    for name in (
        "base.html",
        "index.html",
        "platform.html",
        "activities.html",
        "documents.html",
        "library.html",
        "inclusive_development.html",
        "partials/header.html",
        "partials/domain_sections.html",
    ):
        env.get_template(name)
