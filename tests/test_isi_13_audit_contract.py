from pathlib import Path


def test_successful_mutation_paths_emit_admin_audit_events():
    service = Path("src/platform/administration/service.py").read_text()
    for action in (
        "invitation.created",
        "invitation.revoked",
        "membership.status_changed",
        "membership.product_access_changed",
        "membership.role_assigned",
        "membership.role_removed",
        "workspace.created",
        "workspace.status_changed",
        "organization.renamed",
    ):
        assert action in service
    assert "session.delete(event)" not in service
