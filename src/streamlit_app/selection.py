from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Selection:
    organization_id: str
    product_code: str
    workspace_id: str | None


def organization_by_id(context: dict[str, Any], organization_id: str | None) -> dict[str, Any] | None:
    return next(
        (item for item in context.get("organizations", []) if str(item.get("id")) == str(organization_id)),
        None,
    )


def product_by_code(organization: dict[str, Any], product_code: str | None) -> dict[str, Any] | None:
    return next(
        (item for item in organization.get("products", []) if item.get("code") == product_code),
        None,
    )


def default_selection(
    context: dict[str, Any],
    *,
    organization_id: str | None = None,
    product_code: str | None = None,
    workspace_id: str | None = None,
) -> Selection | None:
    organizations = context.get("organizations", [])
    if not organizations:
        return None

    org = organization_by_id(context, organization_id)
    if org is None:
        route_org_id = context.get("initial_route", {}).get("organization_id")
        org = organization_by_id(context, route_org_id)
    if org is None:
        org = organizations[0]

    products = org.get("products", [])
    if not products:
        return None

    product = product_by_code(org, product_code)
    if product is None:
        route_product = context.get("initial_route", {}).get("product_code")
        product = product_by_code(org, route_product)
    if product is None:
        product = products[0]

    workspaces = product.get("workspaces", [])
    selected_workspace_id = None
    workspace_ids = [str(item["id"]) for item in workspaces]
    if workspace_id and str(workspace_id) in workspace_ids:
        selected_workspace_id = str(workspace_id)
    else:
        route_workspace = context.get("initial_route", {}).get("workspace_id")
        if route_workspace and str(route_workspace) in workspace_ids:
            selected_workspace_id = str(route_workspace)
        elif len(workspaces) == 1:
            selected_workspace_id = str(workspaces[0]["id"])

    return Selection(
        organization_id=str(org["id"]),
        product_code=str(product["code"]),
        workspace_id=selected_workspace_id,
    )


def selection_is_accessible(context: dict[str, Any], selection: Selection) -> bool:
    org = organization_by_id(context, selection.organization_id)
    if org is None:
        return False
    product = product_by_code(org, selection.product_code)
    if product is None:
        return False
    if selection.workspace_id is None:
        return True
    return any(str(item["id"]) == str(selection.workspace_id) for item in product.get("workspaces", []))
