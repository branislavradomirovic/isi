"""Presentation and transient-state rules; backend remains access authority."""
from __future__ import annotations

from html import escape
from typing import Any, MutableMapping


AUTH_KEYS = frozenset({
    "isi_access_token", "isi_app_context", "isi_selected_org_id",
    "isi_selected_product", "isi_selected_workspace_id",
    "isi_org_selector", "isi_workspace_selector",
})


def clear_workspace_state(state: MutableMapping[str, Any]) -> None:
    """Run before widgets render (or in their callback), never retain payloads."""
    for key in list(state):
        if key not in AUTH_KEYS:
            del state[key]


def navigation_items(shell: dict[str, Any]) -> list[dict[str, Any]]:
    product = shell.get("product", {}).get("code")
    items = [item for item in shell.get("navigation", []) if item.get("enabled")]
    # Preserve legacy API navigation; there is no SIMPA scenario domain contract.
    items = [item for item in items if item["code"] != "scenarios" or (
        product == "ORDO" and "analysis.read" in shell["product"].get("permission_codes", [])
    )]
    items += [
        {"code": "isi_help", "label_sr": "ISI Help · Pomoć"},
        {"code": "account_security", "label_sr": "Bezbednost naloga"},
    ]
    if product in {"SIMPA", "ORDO"}:
        items.append({"code": f"{product.lower()}_help", "label_sr": f"{product} Help"})
    return items


def context_markup(shell: dict[str, Any], nav_code: str) -> str:
    labels = {item["code"]: item["label_sr"] for item in navigation_items(shell)}
    parts = (
        shell.get("organization", {}).get("name", ""),
        shell.get("product", {}).get("code", ""),
        (shell.get("workspace") or {}).get("name", "Radni prostor nije izabran"),
        labels.get(nav_code, "Pregled"),
    )
    return '<nav class="isi-context" aria-label="Aktivni radni kontekst">' + (
        '<span aria-hidden="true"> / </span>'.join(f"<strong>{escape(str(part))}</strong>" for part in parts)
    ) + '</nav>'
