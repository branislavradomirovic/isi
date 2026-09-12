from pathlib import Path
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.api.dependencies import get_db
from src.api import data_routes
from src.core.database import Base


def test_analytical_routes_are_authenticated_and_server_authorized():
    source = Path("src/api/data_routes.py").read_text()
    for route in ("/analytical-datasets", "/snapshots", "/analytical-features", "/versions",
                  "/transition", "/lineage", "/analytical-ai/eligibility"):
        assert route in source
    for function in (data_routes.post_analytical_dataset, data_routes.post_analytical_snapshot,
                     data_routes.post_analytical_feature, data_routes.post_analytical_feature_version):
        assert 'permission_code="data.governance.manage"' in __import__("inspect").getsource(function)

    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    app.dependency_overrides[get_db] = lambda: (yield from _yield_session(factory))
    scope = {"organization_id": str(uuid.uuid4()), "workspace_id": str(uuid.uuid4()), "product_code": "SIMPA"}
    try:
        with TestClient(app) as client:
            assert client.get("/api/v1/data/analytical-datasets", params=scope).status_code == 401
            assert client.post("/api/v1/data/analytical-ai/eligibility", json={**scope,
                "artifact_type": "snapshot", "artifact_id": str(uuid.uuid4()), "action": "LOCAL_ANALYSIS",
                "namespace": f"ORG-{scope['organization_id']}/SIMPA"}).status_code == 401
    finally:
        app.dependency_overrides.clear()


def _yield_session(factory):
    with factory() as db:
        yield db


def test_data_workspace_contains_stable_human_review_contract():
    ui = Path("src/streamlit_app/data_workspace.py").read_text()
    api = Path("src/streamlit_app/data_api.py").read_text()
    for label in ("Analytical datasets", "Feature registry", "Lineage / provenance",
                  "AI / RAG eligibility", "Human review"):
        assert label in ui
    assert "data.governance.manage" in ui
    for helper in (
        "list_analytical_datasets", "list_analytical_snapshots", "list_analytical_features",
        "list_analytical_feature_versions", "get_analytical_lineage", "evaluate_ai_eligibility",
    ):
        assert f"data_api.{helper}" in ui
        assert f"def {helper}" in api
    for endpoint in (
        "/api/v1/data/analytical-datasets/{dataset_id}/snapshots",
        "/api/v1/data/analytical-features/{feature_id}/versions",
        "/api/v1/data/analytical-snapshots/{snapshot_id}/lineage",
        "/api/v1/data/analytical-ai/eligibility",
    ):
        assert endpoint in api
    for field in (
        "version_no", "state", "classification", "privacy_category", "ai_use_policy",
        "methodology_reference", "methodology_version", "invalidated", "invalidation_reason",
        "fingerprint", "source_versions", "dependent_feature_versions", "source_fingerprint",
        "allowed", "reason_code", "requires_separate_approval", "human_review_required",
        "provenance_fingerprint",
    ):
        assert field in ui
    assert 'namespace=f"ORG-{organization_id}/{product_code}"' in ui
