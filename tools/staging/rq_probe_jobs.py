from __future__ import annotations


def probe(label: str) -> dict[str, str]:
    return {"status": "ok", "label": str(label)}
