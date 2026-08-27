from __future__ import annotations

from pathlib import Path

import streamlit as st


ASSET_DIR = Path(__file__).resolve().parent / "assets"


def apply_shell_css() -> None:
    css = (ASSET_DIR / "app-shell.css").read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
