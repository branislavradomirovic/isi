from src.streamlit_app.selection import Selection, default_selection, selection_is_accessible


def _context(products):
    return {
        "initial_route": {
            "mode": "selector" if len(products) > 1 else "workspace",
            "organization_id": "org-1",
            "product_code": products[0]["code"],
            "workspace_id": products[0]["workspaces"][0]["id"] if len(products) == 1 else None,
        },
        "organizations": [
            {
                "id": "org-1",
                "name": "Org",
                "products": products,
            }
        ],
    }


def _product(code):
    return {
        "code": code,
        "workspaces": [{"id": f"{code.lower()}-ws", "name": f"{code} Main"}],
    }


def test_single_product_routes_directly_without_cross_product_choice():
    context = _context([_product("SIMPA")])
    selection = default_selection(context)
    assert selection == Selection("org-1", "SIMPA", "simpa-ws")
    assert selection_is_accessible(context, selection)


def test_dual_product_context_can_remember_accessible_product():
    context = _context([_product("SIMPA"), _product("ORDO")])
    selection = default_selection(context, product_code="ORDO", workspace_id="ordo-ws")
    assert selection == Selection("org-1", "ORDO", "ordo-ws")
    assert selection_is_accessible(context, selection)


def test_cross_tenant_or_unknown_product_selection_is_not_accessible():
    context = _context([_product("SIMPA")])
    assert not selection_is_accessible(context, Selection("other-org", "SIMPA", None))
    assert not selection_is_accessible(context, Selection("org-1", "ORDO", None))
