from pathlib import Path


UI = Path("src/streamlit_app/simpa_analytics_workspace.py")


def test_four_lifecycle_meanings_and_reference_state_are_visible():
    text = UI.read_text()
    for phrase in (
        "DRAFT = authored/test work, not institutionally validated.",
        "PROPOSED = controlled testing only, not validated or approved.",
        "VALIDATED = human-approved after the required deterministic reference gate.",
        "RETIRED = historical and reproducible, not eligible for new production calculations.",
    ):
        assert phrase in text
    assert 'item.get("reference_check_status")' in text
    assert 'item.get("reference_check_fingerprint")' in text
    assert "PROPOSED = controlled testing only" in text


def test_evidence_remains_before_methodology_and_ai():
    text = UI.read_text()
    evidence = text.index('"Governed analytical artefakt"')
    methodology = text.index('st.markdown("### Metodološki status")')
    ai = text.index('st.markdown("### Lokalna AI podržana sinteza")')
    assert evidence < methodology < ai


def test_help_is_not_falsely_completed_in_23a():
    text = UI.read_text()
    assert "Detailed SIMPA Help/User Guide remains planned for ISI-23E." in text
    master = Path("docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    help_row = next(line for line in master.splitlines() if line.startswith("| INV-A18 "))
    assert "| PLANNED |" in help_row
