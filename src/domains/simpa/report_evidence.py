"""SIMPA owns numerical evidence; linked reports never fit a model."""
from src.domains.simpa.attribution_service import verified_input, read


def result_evidence(db, *, result_id, organization_id, workspace_id):
    row, _expected = verified_input(db, result_id=result_id, organization_id=organization_id, workspace_id=workspace_id)
    attribution = read(db, result_id=result_id, organization_id=organization_id, workspace_id=workspace_id)
    return {
        "kind": "simpa_statistical_result", "id": str(row.id),
        "fingerprint": row.result_fingerprint, "result": row.result_detail,
        "xai": attribution, "causal": False,
        "scope_match": "HUMAN_CONTEXT_ONLY_NOT_AUTOMATICALLY_VERIFIED",
    }
