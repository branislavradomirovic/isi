from src.api.administration_routes import router


def test_administration_api_surface():
    paths = {(route.path, tuple(sorted(route.methods or []))) for route in router.routes}
    required = {
        "/api/v1/administration/snapshot",
        "/api/v1/administration/invitations",
        "/api/v1/administration/invitations/{invitation_id}/revoke",
        "/api/v1/administration/members/{membership_id}/status",
        "/api/v1/administration/members/{membership_id}/product-access",
        "/api/v1/administration/members/{membership_id}/roles",
        "/api/v1/administration/members/{membership_id}/roles/{assignment_id}",
        "/api/v1/administration/workspaces",
        "/api/v1/administration/workspaces/{workspace_id}/status",
        "/api/v1/administration/organization",
    }
    assert required.issubset({path for path, _ in paths})
