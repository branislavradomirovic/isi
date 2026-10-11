"""Bounded text-only evidence presentation; never infer numerical semantics."""

from __future__ import annotations

from typing import Any
import streamlit as st


def evidence_rows(value: Any, *, maximum: int = 200, max_depth: int = 8) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def visit(item, path, depth):
        if len(rows) >= maximum:
            return
        if isinstance(item, (dict, list)):
            if depth >= max_depth:
                rows.append({"Polje": path, "Vrednost": "Detalji izvan dubine prikaza — nisu protumačeni"})
            elif not item:
                rows.append({"Polje": path, "Vrednost": "Prazna struktura"})
            else:
                pairs = item.items() if isinstance(item, dict) else enumerate(item)
                for key, child in pairs:
                    visit(child, f"{path}.{key}" if path else str(key), depth + 1)
                    if len(rows) >= maximum:
                        break
        else:
            text = "Nije navedeno" if item is None else str(item)
            rows.append(
                {"Polje": path or "Vrednost", "Vrednost": text[:4000] + (" … [skraćeno]" if len(text) > 4000 else "")}
            )

    visit(value, "", 0)
    if len(rows) >= maximum:
        rows.append(
            {
                "Polje": "Granica prikaza",
                "Vrednost": f"Prikaz najviše {maximum} polja; ovo nije potvrda kompletnosti dokaza.",
            }
        )
    return rows


def render_evidence(title: str, value: Any) -> None:
    st.markdown("#### " + title)
    st.dataframe(evidence_rows(value), width="stretch", hide_index=True)
