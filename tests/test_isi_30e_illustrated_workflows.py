import json
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from src.streamlit_app import help_manual as h

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "automation/contracts/ISI-30E-ASSET-PLAN.json"


def test_locked_new_workflows_and_screen_identity():
    plan = json.loads(PLAN.read_text())
    data = h.manual()
    assert len(plan["chapters"]) == 16 and len(plan["assets"]) == 101
    assert len(data["topics"]) == 36 and len(data["chapters"]) == 19
    for c in plan["chapters"]:
        chapter = data["chapters"][c["code"]]
        assert chapter["products"] == c["products"] and chapter["guide"] == c["guide"]
        assert len(chapter["sections"]) == 10
        assert set(n for n in c["screens"] if data["assets"][n]["view"] == "DESKTOP") <= set(chapter["screens"])
        assert all(data["assets"][n]["view"] == "DESKTOP" for n in chapter["screens"])
        assert sorted(n for values in chapter["screen_sections"].values() for n in values) == sorted(chapter["screens"])
    for name, item in plan["assets"].items():
        assert len(item["source_sha256"]) == 64
        assert all(c in "0123456789abcdef" for c in item["source_sha256"])
        assert item["source"].startswith("automation/evidence/ISI-30")
        assert data["assets"][name]["kind"] == "SYNTHETIC"
        assert h.image_bytes(name, data["assets"][name]).startswith(b"\xff\xd8")


def test_shared_private_workflow_selection_and_public_absence():
    at = AppTest.from_string(
        "from src.streamlit_app.shared_help_workspace import render_shared_help\nrender_shared_help()"
    ).run(timeout=30)
    assert not at.exception and len(at.selectbox[0].options) == 12
    assert at.selectbox[1].label == "Detaljan korisnički tok" and at.selectbox[1].value is None
    for key in at.selectbox[1].options:
        at.selectbox[1].select(key).run(timeout=30)
        assert not at.exception and at.get("image")
    public = AppTest.from_string(
        "from src.streamlit_app.shared_help_workspace import render_shared_help\nrender_shared_help(public=True)"
    ).run()
    assert not public.exception and len(public.selectbox) == 1 and len(public.selectbox[0].options) == 6


@pytest.mark.parametrize(
    "product,allowed,forbidden",
    [
        ("SIMPA", "SIMPA_METHOD", "ORDO_METHOD"),
        ("ORDO", "ORDO_METHOD", "SIMPA_METHOD"),
    ],
)
def test_product_specific_workflow_access(product, allowed, forbidden):
    assert allowed in h.chapters(product) and forbidden not in h.chapters(product)
    at = AppTest.from_string(
        f'from src.streamlit_app.help_manual import render_chapter\nrender_chapter("{forbidden}",product="{product}")'
    ).run()
    assert not at.exception and at.info and not at.get("image")


def test_stale_current_directions_removed_and_pending_truth_retained():
    data = h.manual()
    source = (ROOT / "src/streamlit_app/shared_help_workspace.py").read_text()
    assert "Nova verzija koristi najnoviji ponuđeni snapshot" not in source
    assert "Potvrdite opoziv izabrane druge aktivne sesije" in source
    assert "A07 ostaje neprodukcijski" not in source
    assert "kasniji 27D/ISI-28" not in source
    assert "Ovaj UI nema pune forme" not in source
    assert "governed API lifecycle" not in source
    assert "API-only" not in json.dumps(data["topics"]["ISI-H07"], ensure_ascii=False)
    for product in ("simpa", "ordo"):
        assert "SHAP je pending 29D" not in (ROOT / f"src/streamlit_app/{product}_help_workspace.py").read_text()
    security = data["chapters"]["SECURITY"]
    assert "SMTP" in str(security) and "MFA" in str(security)
    assert "nije institucionalno odobrenje" in str(data["chapters"]["SHELL"]).lower()


def test_current_report_has_all_reviewed_action_screens():
    c = h.manual()["chapters"]["LINKED"]
    assert c["guide"] == "ISI-REPORTING-WORKFLOWS-GUIDE.md"
    for token in [
        "explicit-selection",
        "linked-inputs",
        "draft-evidence",
        "review-confirmation",
        "publish-confirmation",
        "export",
        "readonly",
        "ordo-context",
    ]:
        assert any(token in n for n in c["screens"])
    assert "claim" in str(c) and "pregled" in str(c).lower()
