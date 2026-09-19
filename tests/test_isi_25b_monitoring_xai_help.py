from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import src.platform.models  # noqa: F401
from src.core.database import Base
from src.platform.access.models import Product
from src.platform.ai.evaluation import (
    create_evaluation_run,
    finalize_evaluation_run,
    load_evaluation_manifest,
    register_evaluation_dataset,
)
from src.platform.ai.governance import register_model
from src.platform.ai.models import AIDriftSnapshot
from src.platform.ai.monitoring import capability_status, classify_drift
from src.platform.ai.xai import UNAVAILABLE_XAI, evaluation_explanation
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


ROOT = Path(__file__).resolve().parents[1]


def _profile():
    return SimpleNamespace(metric_definitions={
        "grounded_factuality": {"direction": "higher", "drift_warning_delta": 0.1, "drift_blocker_delta": 0.2}
    })


def test_drift_statuses_are_deterministic_and_bounded():
    profile = _profile()
    assert classify_drift(observed_metrics={}, reference_metrics={}, threshold_profile=profile)[0] == "insufficient_evidence"
    assert classify_drift(observed_metrics={"grounded_factuality": 0.95}, reference_metrics={"grounded_factuality": 1.0}, threshold_profile=profile)[0] == "ok"
    assert classify_drift(observed_metrics={"grounded_factuality": 0.85}, reference_metrics={"grounded_factuality": 1.0}, threshold_profile=profile)[0] == "warning"
    assert classify_drift(observed_metrics={"grounded_factuality": 0.7}, reference_metrics={"grounded_factuality": 1.0}, threshold_profile=profile)[0] == "blocker"


def test_toward_zero_drift_uses_magnitude_not_sign():
    profile = SimpleNamespace(metric_definitions={
        "bias": {"direction": "toward_zero", "drift_warning_delta": 0.2, "drift_blocker_delta": 0.5}
    })
    improved = classify_drift(
        observed_metrics={"bias": -0.1}, reference_metrics={"bias": 0.8}, threshold_profile=profile
    )
    worsened = classify_drift(
        observed_metrics={"bias": -0.8}, reference_metrics={"bias": 0.1}, threshold_profile=profile
    )
    assert improved[0] == "ok" and improved[1]["bias"]["deterioration"] < 0
    assert worsened[0] == "blocker" and worsened[1]["bias"]["deterioration"] > 0


def test_xai_marks_unsupported_semantics_unavailable():
    for key in ("confidence", "probability", "calibration", "feature_importance", "shap", "uncertainty"):
        assert UNAVAILABLE_XAI[key]["state"] == "unavailable"


def test_read_model_has_required_provenance_and_runtime_states():
    monitoring = (ROOT / "src/platform/ai/monitoring.py").read_text(encoding="utf-8")
    xai = (ROOT / "src/platform/ai/xai.py").read_text(encoding="utf-8")
    for marker in ("champion_registration_id", "challenger_registration_ids", "rollback_registration_id",
                   "circuit_state", "latest_drift_status", "fallbacks", "requires_human_review"):
        assert marker in monitoring
    for marker in ("model_registration", "prompt_identity", "policy_identity", "benchmark_identity",
                   "final_human_review", "authority_distinction", "unsupported_xai"):
        assert marker in xai
    assert '"scheduler": None' in monitoring and '"automatic_training": False' in monitoring


def test_shared_ai_guide_and_matrix_are_complete_without_overclaiming_isi27():
    guide = (ROOT / "docs/help/ISI-AI-USER-GUIDE.md").read_text(encoding="utf-8")
    matrix = (ROOT / "docs/help/ISI-HELP-COVERAGE-MATRIX.md").read_text(encoding="utf-8")
    for marker in ("when to use each function", "Roles and permissions", "Conceptual workflow", "Registration lifecycle",
                   "Synthetic example", "Common blockers", "Security, privacy and methodology limits",
                   "Provenance and XAI", "Explicit non-goals", "review_required", "online learning"):
        assert marker.lower() in guide.lower()
    assert "ISI-25B shared AI material actions" in matrix
    assert "REMOVE_IN_NAMED_PHASE(ISI-27)" in matrix
    assert "global matrix honestly remains PARTIAL" in matrix


def test_capability_status_and_xai_select_only_authorized_workspace_evidence():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        marker = uuid.uuid4().hex
        db.add_all([Product(code="SIMPA", name="SIMPA"), Product(code="ORDO", name="ORDO")])
        user = User(email=f"{marker}@example.test", display_name="Reader")
        organization = Organization(slug=f"org-{marker}", name="Organization")
        db.add_all([user, organization])
        db.flush()
        actor = Membership(user_id=user.id, organization_id=organization.id)
        db.add(actor)
        db.flush()
        workspaces = [Workspace(
            organization_id=organization.id, product_code="SIMPA", slug=f"simpa-{index}",
            name=f"SIMPA {index}", created_by_membership_id=actor.id,
        ) for index in range(2)]
        db.add_all(workspaces)
        db.flush()
        registration = register_model(
            db, organization_id=organization.id, workspace_id=workspaces[0].id,
            product_code="SIMPA", capability_key="simpa.monitor", product_scope="SIMPA",
            model_family="statistical_ml", model_key="monitor-model", version="1",
            lifecycle_state="challenger", actor_id=actor.id, provenance={"source": "synthetic"},
        )
        dataset = register_evaluation_dataset(
            db, manifest=load_evaluation_manifest("tests/evals/SIMPA-EVAL-v1.json"),
            product_code="SIMPA", actor_id=actor.id,
        )
        runs = []
        for index, workspace in enumerate(workspaces):
            run = create_evaluation_run(
                db, organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
                dataset_id=dataset.id, model_registration_id=registration.id,
                baseline_registration_id=None, prompt_version_id=None, policy_profile_id=None,
                input_fingerprint=str(index + 1) * 64, environment_fingerprint="e" * 64,
                provenance={"workspace": index}, actor_id=actor.id,
            )
            finalize_evaluation_run(db, run=run, status="completed")
            runs.append(run)
        now = datetime.now(timezone.utc)
        db.add_all([
            AIDriftSnapshot(
                organization_id=organization.id, workspace_id=workspaces[0].id,
                product_code="SIMPA", capability_key="simpa.monitor",
                model_registration_id=registration.id, threshold_profile_id=uuid.uuid4(),
                window_start=now - timedelta(days=2), window_end=now - timedelta(days=1),
                metrics={}, provenance={}, fingerprint="a" * 64, status="ok",
                created_by_membership_id=actor.id,
            ),
            AIDriftSnapshot(
                organization_id=organization.id, workspace_id=workspaces[1].id,
                product_code="SIMPA", capability_key="simpa.monitor",
                model_registration_id=registration.id, threshold_profile_id=uuid.uuid4(),
                window_start=now - timedelta(days=1), window_end=now,
                metrics={}, provenance={}, fingerprint="b" * 64, status="blocker",
                created_by_membership_id=actor.id,
            ),
        ])
        db.flush()
        status = capability_status(
            db, organization_id=organization.id, workspace_id=workspaces[0].id,
            product_code="SIMPA", capability_key="simpa.monitor",
        )
        assert status["latest_drift_status"] == "ok"
        assert status["latest_evaluation_run_id"] == str(runs[0].id)
        explanation = evaluation_explanation(
            db, run_id=runs[0].id, organization_id=organization.id,
            workspace_id=workspaces[0].id, product_code="SIMPA",
        )
        assert explanation["drift_state"] == "ok"
        with pytest.raises(ValueError, match="evaluation_run_not_found"):
            evaluation_explanation(
                db, run_id=runs[0].id, organization_id=organization.id,
                workspace_id=workspaces[1].id, product_code="SIMPA",
            )


@pytest.mark.parametrize(
    ("observed", "reference"),
    [
        (True, 1.0),
        (1.0, False),
        (float("nan"), 1.0),
        (1.0, float("inf")),
    ],
)
def test_fhr3_r3_drift_non_finite_or_boolean_evidence_never_reports_ok(observed, reference):
    profile = SimpleNamespace(
        metric_definitions={
            "quality": {
                "direction": "higher",
                "drift_warning_delta": 0.1,
                "drift_blocker_delta": 0.2,
            }
        },
        minimum_thresholds={},
        minimum_deltas={},
        hard_gates={},
        resource_limits={},
        failure_threshold=2,
        cooldown_seconds=30,
    )
    status, detail = classify_drift(
        observed_metrics={"quality": observed},
        reference_metrics={"quality": reference},
        threshold_profile=profile,
    )
    assert status == "insufficient_evidence"
    assert detail["reason"].startswith("required_metric_invalid:quality")


@pytest.mark.parametrize(
    "definition",
    [
        {"direction": "higher", "drift_warning_delta": "nan", "drift_blocker_delta": 0.2},
        {"direction": "higher", "drift_warning_delta": 0.2, "drift_blocker_delta": "nan"},
        {"direction": "higher", "drift_warning_delta": -0.1, "drift_blocker_delta": 0.2},
        {"direction": "higher", "drift_warning_delta": 0.3, "drift_blocker_delta": 0.2},
    ],
)
def test_fhr3_r3_malformed_drift_thresholds_fail_closed(definition):
    profile = SimpleNamespace(
        metric_definitions={"quality": definition},
        minimum_thresholds={},
        minimum_deltas={},
        hard_gates={},
        resource_limits={},
        failure_threshold=2,
        cooldown_seconds=30,
    )
    status, detail = classify_drift(
        observed_metrics={"quality": 0.5},
        reference_metrics={"quality": 1.0},
        threshold_profile=profile,
    )
    assert status == "insufficient_evidence"
    assert detail["reason"].startswith("threshold_profile_invalid:")


def test_fhr3_r5_capability_status_hides_cross_product_fallback_target():
    from src.platform.ai.governance import list_fallbacks, register_fallback

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        marker = uuid.uuid4().hex
        db.add_all([Product(code="SIMPA", name="SIMPA"), Product(code="ORDO", name="ORDO")])
        user = User(email=f"{marker}@example.test", display_name="Fallback Reader")
        organization = Organization(slug=f"org-{marker}", name="Organization")
        db.add_all([user, organization])
        db.flush()
        actor = Membership(user_id=user.id, organization_id=organization.id)
        db.add(actor)
        db.flush()
        simpa_workspace = Workspace(
            organization_id=organization.id, product_code="SIMPA", slug=f"simpa-{marker}",
            name="SIMPA", created_by_membership_id=actor.id,
        )
        ordo_workspace = Workspace(
            organization_id=organization.id, product_code="ORDO", slug=f"ordo-{marker}",
            name="ORDO", created_by_membership_id=actor.id,
        )
        db.add_all([simpa_workspace, ordo_workspace])
        db.flush()
        source = register_model(
            db, organization_id=organization.id, workspace_id=ordo_workspace.id,
            product_code="ORDO", capability_key="shared.monitor", product_scope="SHARED",
            model_family="llm", model_key=f"shared-{marker}", version="1",
            lifecycle_state="challenger", actor_id=actor.id, provenance={"source": "synthetic"},
        )
        target = register_model(
            db, organization_id=organization.id, workspace_id=ordo_workspace.id,
            product_code="ORDO", capability_key="shared.monitor", product_scope="ORDO",
            model_family="llm", model_key=f"ordo-{marker}", version="1",
            lifecycle_state="challenger", actor_id=actor.id, provenance={"source": "synthetic"},
        )
        register_fallback(
            db, source_registration_id=source.id, target_registration_id=target.id, priority=1,
            trigger_codes=["model_unavailable"], semantically_equivalent=True,
            requires_human_review=True, provenance="synthetic", actor_id=actor.id,
            organization_id=organization.id, workspace_id=ordo_workspace.id, product_code="ORDO",
        )
        assert list_fallbacks(db, product_code="SIMPA", source_registration_id=source.id) == []
        status = capability_status(
            db, organization_id=organization.id, workspace_id=simpa_workspace.id,
            product_code="SIMPA", capability_key="shared.monitor",
        )
        assert status["fallbacks"] == []
