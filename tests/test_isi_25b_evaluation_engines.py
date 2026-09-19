from __future__ import annotations

import math
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import src.api.ai_routes as ai_routes
import src.platform.models  # noqa: F401
from src.core.database import Base
from src.platform.access.models import Product
from src.platform.ai.evaluation import (
    AIEvaluationError,
    aggregate_evaluation_metrics,
    append_evaluation_result,
    append_evaluation_review,
    benchmark_execution_provenance,
    benchmark_input_fingerprint,
    canonical_benchmark_execution_cases,
    cases_sha256,
    create_evaluation_run,
    evaluate_classification,
    evaluate_llm_case,
    evaluate_regression,
    evaluate_retrieval,
    evaluate_vlm_case,
    finalize_evaluation_run,
    governed_execution_cases,
    load_evaluation_manifest,
    register_evaluation_dataset,
    register_promotion_benchmark,
)
from src.platform.ai.governance import fingerprint, register_model
from src.platform.ai.models import AIEvaluationResult
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


def _values(rows):
    return {row["metric_key"]: row for row in rows}


def test_regression_metrics_are_deterministic_and_typed():
    rows = _values(evaluate_regression([1, 2, 3], [2, 2, 1]))
    assert rows["mae"]["value"] == 1
    assert math.isclose(rows["rmse"]["value"], math.sqrt(5 / 3))
    assert rows["bias"]["value"] == -1 / 3
    assert all(len(row["fingerprint"]) == 64 and row["support"] == 3 for row in rows.values())


def test_classification_and_brier_are_bounded():
    rows = _values(evaluate_classification([1, 1, 0, 0], [1, 0, 1, 0], [0.9, 0.4, 0.7, 0.1]))
    assert rows["precision"]["value"] == rows["recall"]["value"] == rows["f1"]["value"] == 0.5
    assert math.isclose(rows["brier"]["value"], 0.2175)
    assert _values(evaluate_classification([1], [1]))["brier"]["state"] == "unavailable"


def test_retrieval_metrics_and_empty_cases():
    cases = [{"relevant_ids": ["a", "b"], "retrieved_ids": ["x", "a", "b"],
              "allowed_namespace": "SIMPA:org-a", "retrieved_namespaces": ["SIMPA:org-a"] * 2}]
    rows = _values(evaluate_retrieval(cases, k=2))
    assert rows["recall_at_k"]["value"] == 0.5
    assert rows["mrr"]["value"] == 0.5
    assert 0 < rows["ndcg_at_k"]["value"] < 1
    assert rows["namespace_isolation"]["value"] is True
    assert all(row["state"] == "unavailable" for row in evaluate_retrieval([], k=10))


def test_llm_factuality_structure_provenance_human_rubric_and_latency():
    reviewer_id = uuid.uuid4()
    case = {
        "atomic_claims": [{"supported": True}, {"supported": False}],
        "structured_output": {"status": "ok"},
        "schema": {"required": ["status"], "properties": {"status": {"enum": ["ok"]}}},
        "source_refs": ["s1"], "cited_refs": ["s1"], "instruction_contract_passed": True,
        "serbian_human_rubric": {
            "authorized": True, "scores": [4, 5], "maximum": 5,
            "reviewer": "caller-claim-is-not-authority",
            "evidence_reference": "synthetic://rubric/review-1",
        },
        "latency_ms": 50,
    }
    rows = _values(evaluate_llm_case(case, authorized_reviewer_membership_id=reviewer_id))
    assert rows["grounded_factuality"]["value"] == 0.5
    assert rows["unsupported_claim_rate"]["value"] == 0.5
    assert rows["structured_required_fields"]["value"] is True
    assert rows["provenance_compliance"]["value"] is True
    assert rows["serbian_human_rubric"]["value"] == 0.9
    assert rows["serbian_human_rubric"]["evidence"]["reviewer_membership_id"] == str(reviewer_id)
    assert rows["serbian_human_rubric"]["evidence"]["authorization_source"] == "server_scope_and_permission"
    caller_only = _values(evaluate_llm_case(case))["serbian_human_rubric"]
    assert caller_only["state"] == "unavailable" and caller_only["value"] is None
    assert rows["latency_ms"]["direction"] == "lower"
    assert _values(evaluate_llm_case({}))["serbian_human_rubric"]["state"] == "unavailable"




def test_fhr3_r2_numeric_evidence_rejects_boolean_negative_and_nonfinite_latency():
    for invalid in (True, -1, float("nan"), float("inf")):
        with pytest.raises(AIEvaluationError, match="latency_ms_non_negative_finite_number_required"):
            evaluate_llm_case({"latency_ms": invalid})
    rows = aggregate_evaluation_metrics([{
        "metric_key": "latency_ms", "value": True, "direction": "lower",
        "state": "available", "support": 1, "case_refs": ["case-a"], "fingerprint": "x" * 64,
    }])
    assert rows[0]["state"] == "unavailable"
    assert rows[0]["evidence"]["reason"] == "numeric_component_evidence_required"


def test_fhr3_r2_final_review_requires_nonempty_evidence_reference(benchmark_db):
    db, organization, workspace, actor, registration, dataset, _benchmark = benchmark_db
    run = create_evaluation_run(
        db, organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
        dataset_id=dataset.id, model_registration_id=registration.id, baseline_registration_id=None,
        prompt_version_id=None, policy_profile_id=None, input_fingerprint="a" * 64,
        environment_fingerprint="b" * 64, provenance={}, actor_id=actor.id,
    )
    finalize_evaluation_run(db, run=run, status="completed")
    with pytest.raises(AIEvaluationError, match="final_evaluation_review_evidence_reference_required"):
        append_evaluation_review(
            db, run=run, reviewer_membership_id=actor.id, decision="approved",
            notes="approved", evidence_reference="   ",
        )

def test_vlm_accuracy_and_unavailable_behavior():
    rows = _values(evaluate_vlm_case({
        "expected_fields": {"name": " Novi Sad ", "count": 12},
        "extracted_fields": {"name": "novi sad", "count": 12},
        "source_refs": ["doc:1"], "provenance_valid": True,
    }))
    assert rows["normalized_field_accuracy"]["value"] == 1
    assert rows["numeric_transcription_accuracy"]["value"] == 1
    assert rows["vlm_provenance"]["value"] is True
    assert all(row["state"] == "unavailable" for row in evaluate_vlm_case({}))


def _benchmark_manifest():
    cases = [
        {
            "case_id": case_id, "product_code": "SIMPA", "domain": "SIMPA",
            "capability": "simpa.bias", "language": "sr", "input_version": "1",
            "expected_contract": {"task": "regression", "expected": [0.0]},
            "source_refs": [f"fixture:{case_id}"],
            "sensitivity_class": "synthetic", "methodology_version": "m1",
            "human_gold_state": "approved", "notes": "synthetic",
        }
        for case_id in ("case-a", "case-b")
    ]
    return {
        "dataset_key": "SIMPA-BIAS-PROMOTION", "version": "1", "product_code": "SIMPA",
        "capability_key": "simpa.bias", "model_family": "statistical_ml", "schema_version": "1",
        "case_count": len(cases), "cases_sha256": cases_sha256(cases),
        "source_provenance": "repository synthetic", "sensitivity_class": "synthetic",
        "methodology_version": "m1", "frozen": True, "approval_state": "approved",
        "owner": "test", "cases": cases,
    }


@pytest.fixture
def benchmark_db():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        marker = uuid.uuid4().hex
        db.add_all([Product(code="SIMPA", name="SIMPA"), Product(code="ORDO", name="ORDO")])
        user = User(email=f"{marker}@example.test", display_name="Evaluator")
        organization = Organization(slug=f"org-{marker}", name="Organization")
        db.add_all([user, organization])
        db.flush()
        actor = Membership(user_id=user.id, organization_id=organization.id)
        db.add(actor)
        db.flush()
        workspace = Workspace(
            organization_id=organization.id, product_code="SIMPA", slug="simpa", name="SIMPA",
            created_by_membership_id=actor.id,
        )
        db.add(workspace)
        db.flush()
        registration = register_model(
            db, organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
            capability_key="simpa.bias", product_scope="SIMPA", model_family="statistical_ml",
            model_key="bias-model", version="1", lifecycle_state="candidate", actor_id=actor.id,
            provenance={"source": "synthetic"},
        )
        dataset = register_evaluation_dataset(
            db, manifest=load_evaluation_manifest("tests/evals/SIMPA-EVAL-v1.json"),
            product_code="SIMPA", actor_id=actor.id,
        )
        benchmark = register_promotion_benchmark(
            db, manifest=_benchmark_manifest(), product_code="SIMPA", actor_id=actor.id,
        )
        yield db, organization, workspace, actor, registration, dataset, benchmark


def test_frozen_benchmark_case_set_truth_and_input_identity_fail_closed(benchmark_db):
    db, organization, workspace, actor, registration, dataset, benchmark = benchmark_db
    valid = [
        {"case_id": "case-b", "actual": [1.0]},
        {"case_id": "case-a", "actual": [-1.0]},
    ]
    canonical = canonical_benchmark_execution_cases(benchmark, valid)
    assert [case["case_id"] for case in canonical] == ["case-a", "case-b"]
    assert all(case["expected"] == [0.0] for case in canonical)
    for invalid in (
        [{"case_id": "case-a", "actual": [1.0]}],
        [{"case_id": "case-a"}, {"case_id": "case-a"}],
        valid + [{"case_id": "extra"}],
    ):
        with pytest.raises(AIEvaluationError, match="promotion_benchmark_case_set_mismatch"):
            canonical_benchmark_execution_cases(benchmark, invalid)
    with pytest.raises(AIEvaluationError, match="promotion_benchmark_case_metadata_mismatch"):
        canonical_benchmark_execution_cases(benchmark, [
            {"case_id": "case-a", "expected": [999.0]}, {"case_id": "case-b"},
        ])
    with pytest.raises(AIEvaluationError, match="evaluation_input_fingerprint_benchmark_mismatch"):
        create_evaluation_run(
            db, organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
            dataset_id=dataset.id, benchmark_id=benchmark.id, model_registration_id=registration.id,
            baseline_registration_id=None, prompt_version_id=None, policy_profile_id=None,
            input_fingerprint="a" * 64, environment_fingerprint="b" * 64,
            provenance={"methodology_version": "m1"}, actor_id=actor.id,
        )


def test_multicase_aggregation_is_authoritative_and_manual_append_is_blocked(benchmark_db):
    db, organization, workspace, actor, registration, dataset, benchmark = benchmark_db
    components = []
    for case_id, actual in (("case-a", [1.0]), ("case-b", [-3.0])):
        for metric in evaluate_regression([0.0], actual):
            metric["case_refs"] = [case_id]
            components.append(metric)
    rows = _values(aggregate_evaluation_metrics(components))
    assert set(rows) == {"mae", "rmse", "bias"}
    assert rows["mae"]["value"] == 2.0
    assert rows["bias"]["value"] == -1.0
    assert rows["bias"]["case_refs"] == ["case-a", "case-b"]
    assert rows["bias"]["evidence"]["aggregation_rule"] == "support_weighted_mean"
    run = create_evaluation_run(
        db, organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
        dataset_id=dataset.id, benchmark_id=benchmark.id, model_registration_id=registration.id,
        baseline_registration_id=None, prompt_version_id=None, policy_profile_id=None,
        input_fingerprint=benchmark_input_fingerprint(benchmark), environment_fingerprint="b" * 64,
        provenance={"methodology_version": "m1"}, actor_id=actor.id,
    )
    with pytest.raises(AIEvaluationError, match="promotion_bound_manual_result_append_forbidden"):
        append_evaluation_result(
            db, run=run, result_type="metric", result_key="bias", payload=rows["bias"],
            actor_id=actor.id,
        )
    append_evaluation_result(
        db, run=run, result_type="metric", result_key="bias", payload=rows["bias"],
        actor_id=actor.id, governed_execution=True,
    )
    with pytest.raises(AIEvaluationError, match="duplicate_authoritative_result_key:bias"):
        append_evaluation_result(
            db, run=run, result_type="metric", result_key="bias", payload=rows["bias"],
            actor_id=actor.id, governed_execution=True,
        )



def test_fhr3_primary_evaluator_is_bound_to_registered_model_family(benchmark_db):
    db, organization, workspace, actor, registration, dataset, benchmark = benchmark_db
    run = create_evaluation_run(
        db, organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
        dataset_id=dataset.id, benchmark_id=benchmark.id, model_registration_id=registration.id,
        baseline_registration_id=None, prompt_version_id=None, policy_profile_id=None,
        input_fingerprint=benchmark_input_fingerprint(benchmark), environment_fingerprint="e" * 64,
        provenance={"methodology_version": "m1"}, actor_id=actor.id,
    )
    submitted = [
        {"case_id": "case-a", "actual": [1.0]},
        {"case_id": "case-b", "actual": [-1.0]},
    ]
    assert len(governed_execution_cases(
        db, run=run, submitted_cases=submitted, evaluator_family="statistical_ml"
    )) == 2
    for family in ("llm", "vlm", "embedding", "safety"):
        before = db.query(AIEvaluationResult).count()
        with pytest.raises(AIEvaluationError, match="evaluation_evaluator_family_mismatch"):
            governed_execution_cases(db, run=run, submitted_cases=submitted, evaluator_family=family)
        assert db.query(AIEvaluationResult).count() == before


def test_fhr3_frozen_case_semantics_and_safety_kind_cannot_be_rewritten():
    manifest = _benchmark_manifest()
    manifest["cases"][0]["expected_contract"].update({
        "schema": {"required": ["status"]},
        "allowed_namespace": "SIMPA:org-a:private",
    })
    manifest["cases"].append({
        "case_id": "safety-1", "product_code": "SIMPA", "domain": "SIMPA",
        "capability": "simpa.bias", "language": "sr", "input_version": "1",
        "expected_contract": {"kind": "prompt_injection"}, "source_refs": ["fixture:safety"],
        "sensitivity_class": "synthetic", "methodology_version": "m1",
        "human_gold_state": "approved", "notes": "safety",
    })
    manifest["case_count"] = len(manifest["cases"])
    manifest["cases_sha256"] = cases_sha256(manifest["cases"])
    benchmark = SimpleNamespace(
        frozen=True, approval_state="approved", manifest_json=manifest, model_family="statistical_ml",
        manifest_fingerprint=fingerprint(manifest), cases_sha256=manifest["cases_sha256"],
    )
    submitted = [
        {"case_id": "case-a", "actual": [1.0]},
        {"case_id": "case-b", "actual": [-1.0]},
        {"case_id": "safety-1", "passed": True},
    ]
    merged = canonical_benchmark_execution_cases(benchmark, submitted)
    primary = next(case for case in merged if case["case_id"] == "case-a")
    safety = next(case for case in merged if case["case_id"] == "safety-1")
    assert primary["task"] == "regression"
    assert primary["schema"] == {"required": ["status"]}
    assert primary["allowed_namespace"] == "SIMPA:org-a:private"
    assert safety["kind"] == "prompt_injection"
    for field, bad in (
        ("task", "classification"),
        ("schema", {"required": []}),
        ("allowed_namespace", "ORDO:org-b:private"),
    ):
        changed = [dict(case) for case in submitted]
        changed[0][field] = bad
        with pytest.raises(AIEvaluationError, match="promotion_benchmark_case_metadata_mismatch"):
            canonical_benchmark_execution_cases(benchmark, changed)
    changed = [dict(case) for case in submitted]
    changed[2]["kind"] = "cross_tenant"
    with pytest.raises(AIEvaluationError, match="promotion_benchmark_case_metadata_mismatch"):
        canonical_benchmark_execution_cases(benchmark, changed)
    changed = [dict(case) for case in submitted]
    changed[0]["caller_semantic_override"] = True
    with pytest.raises(AIEvaluationError, match="promotion_benchmark_observation_field_forbidden"):
        canonical_benchmark_execution_cases(benchmark, changed)


def test_fhr3_boolean_evidence_is_strictly_typed():
    with pytest.raises(AIEvaluationError, match="llm_claim_supported_boolean_required"):
        evaluate_llm_case({"atomic_claims": [{"supported": "false"}]})
    with pytest.raises(AIEvaluationError, match="instruction_contract_boolean_required"):
        evaluate_llm_case({"instruction_contract_passed": "false"})
    with pytest.raises(AIEvaluationError, match="vlm_provenance_boolean_required"):
        evaluate_vlm_case({
            "expected_fields": {"value": "x"}, "extracted_fields": {"value": "x"},
            "source_refs": ["fixture:1"], "provenance_valid": "false",
        })
    with pytest.raises(AIEvaluationError, match="safety_passed_boolean_required"):
        from src.platform.ai.evaluation import evaluate_safety_cases
        evaluate_safety_cases([{"kind": "prompt_injection", "passed": "false"}])


def test_fhr3_benchmark_execution_provenance_is_system_derived(benchmark_db):
    db, organization, workspace, actor, registration, dataset, benchmark = benchmark_db
    run = create_evaluation_run(
        db, organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
        dataset_id=dataset.id, benchmark_id=benchmark.id, model_registration_id=registration.id,
        baseline_registration_id=None, prompt_version_id=None, policy_profile_id=None,
        input_fingerprint=benchmark_input_fingerprint(benchmark), environment_fingerprint="e" * 64,
        provenance={"methodology_version": "m1"}, actor_id=actor.id,
    )
    cases = governed_execution_cases(
        db, run=run, evaluator_family="statistical_ml", submitted_cases=[
            {"case_id": "case-a", "actual": [1.0]}, {"case_id": "case-b", "actual": [-1.0]},
        ],
    )
    row = benchmark_execution_provenance(db, run=run, cases=cases)
    assert row["metric_key"] == "benchmark_execution_provenance"
    assert row["value"] is True and row["evidence"]["model_family"] == "statistical_ml"


def test_fhr3_serbian_rubric_authority_is_server_derived(monkeypatch):
    actor_id = uuid.uuid4()
    user_id = uuid.uuid4()
    organization_id = uuid.uuid4()
    context = SimpleNamespace(user=SimpleNamespace(id=user_id))
    cases = [{
        "serbian_human_rubric": {
            "authorized": True, "scores": [5], "maximum": 5,
            "evidence_reference": "synthetic://rubric/1",
        }
    }]
    monkeypatch.setattr(ai_routes, "has_permission", lambda *_args, **_kwargs: False)
    with pytest.raises(AIEvaluationError, match="serbian_human_rubric_requires_authorized_review"):
        ai_routes._authorized_serbian_rubric_reviewer(
            object(), context, organization_id=organization_id, product_code="SIMPA",
            actor_id=actor_id, cases=cases,
        )
    monkeypatch.setattr(ai_routes, "has_permission", lambda *_args, **_kwargs: True)
    assert ai_routes._authorized_serbian_rubric_reviewer(
        object(), context, organization_id=organization_id, product_code="SIMPA",
        actor_id=actor_id, cases=cases,
    ) == actor_id
    cases[0]["serbian_human_rubric"]["evidence_reference"] = ""
    with pytest.raises(AIEvaluationError, match="serbian_human_rubric_requires_authorized_review"):
        ai_routes._authorized_serbian_rubric_reviewer(
            object(), context, organization_id=organization_id, product_code="SIMPA",
            actor_id=actor_id, cases=cases,
        )

def test_terminal_fingerprint_binds_scope_prompt_policy_and_provenance(benchmark_db):
    db, organization, workspace, actor, registration, dataset, _benchmark = benchmark_db
    fingerprints = []
    for index, provenance in enumerate(({"code_sha": "one"}, {"code_sha": "two"})):
        run = create_evaluation_run(
            db, organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
            dataset_id=dataset.id, model_registration_id=registration.id,
            baseline_registration_id=None, prompt_version_id=None,
            policy_profile_id=None, input_fingerprint=f"{index + 1:x}" * 64,
            environment_fingerprint="e" * 64, provenance=provenance, actor_id=actor.id,
        )
        run.baseline_registration_id = uuid.uuid4()
        run.prompt_version_id = uuid.uuid4()
        run.policy_profile_id = uuid.uuid4()
        finalize_evaluation_run(db, run=run, status="completed")
        fingerprints.append(run.result_fingerprint)
    assert fingerprints[0] != fingerprints[1]


def test_malformed_evaluator_evidence_is_bounded():
    with pytest.raises(AIEvaluationError, match="regression_expected_numeric_array_required"):
        evaluate_regression({"not": "an array"}, [1.0])  # type: ignore[arg-type]
    with pytest.raises(AIEvaluationError, match="llm_schema_contract_invalid"):
        evaluate_llm_case({"schema": {"required": "status"}})
    with pytest.raises(AIEvaluationError, match="retrieval_id_arrays_required"):
        evaluate_retrieval([{"relevant_ids": "bad", "retrieved_ids": []}], k=1)


def test_fhr3_r4_frozen_benchmark_cannot_preseed_runtime_observations():
    from src.platform.ai.evaluation import validate_promotion_benchmark_manifest

    for field, value in (
        ("passed", True),
        ("actual", [0.0]),
        ("retrieved_ids", ["doc:1"]),
        ("structured_output", {"status": "ok"}),
        ("extracted_fields", {"count": 1}),
    ):
        manifest = _benchmark_manifest()
        manifest["cases"][0]["expected_contract"][field] = value
        manifest["cases_sha256"] = cases_sha256(manifest["cases"])
        with pytest.raises(AIEvaluationError, match="promotion_benchmark_expected_observation_forbidden"):
            validate_promotion_benchmark_manifest(manifest)

    manifest = _benchmark_manifest()
    manifest["cases"][0]["actual"] = [0.0]
    manifest["cases_sha256"] = cases_sha256(manifest["cases"])
    with pytest.raises(AIEvaluationError, match="promotion_benchmark_canonical_observation_forbidden"):
        validate_promotion_benchmark_manifest(manifest)


def test_fhr3_r4_benchmark_source_references_are_strict_strings():
    from src.platform.ai.evaluation import validate_promotion_benchmark_manifest

    manifest = _benchmark_manifest()
    manifest["cases"][0]["source_refs"] = [1]
    manifest["cases_sha256"] = cases_sha256(manifest["cases"])
    with pytest.raises(AIEvaluationError, match="promotion_benchmark_source_references_invalid"):
        validate_promotion_benchmark_manifest(manifest)


def test_fhr3_r4_llm_schema_types_enums_and_reference_identity_are_fail_closed():
    rows = _values(evaluate_llm_case({
        "structured_output": {"count": "1"},
        "schema": {"required": ["count"], "properties": {"count": {"type": "integer"}}},
    }))
    assert rows["structured_parse"]["value"] is True
    assert rows["structured_required_fields"]["value"] is True
    assert rows["structured_schema_compliance"]["value"] is False

    rows = _values(evaluate_llm_case({
        "structured_output": {"count": True},
        "schema": {"required": ["count"], "properties": {"count": {"type": "integer", "enum": [1]}}},
    }))
    assert rows["structured_enum_compliance"]["value"] is False
    assert rows["structured_schema_compliance"]["value"] is False

    with pytest.raises(AIEvaluationError, match="llm_source_references_string_required"):
        evaluate_llm_case({"source_refs": [1], "cited_refs": [True]})
    with pytest.raises(AIEvaluationError, match="llm_cited_references_string_required"):
        evaluate_llm_case({"source_refs": ["1"], "cited_refs": [True]})


def test_fhr3_r4_vlm_bool_is_not_numeric_and_boolean_only_gold_is_unavailable():
    rows = _values(evaluate_vlm_case({
        "expected_fields": {"count": 1},
        "extracted_fields": {"count": True},
        "source_refs": ["doc:1"],
        "provenance_valid": True,
    }))
    assert rows["numeric_transcription_accuracy"]["value"] == 0.0

    rows = _values(evaluate_vlm_case({
        "expected_fields": {"flag": True},
        "extracted_fields": {"flag": True},
        "source_refs": ["doc:1"],
        "provenance_valid": True,
    }))
    assert rows["numeric_transcription_accuracy"]["state"] == "unavailable"
    assert rows["numeric_transcription_accuracy"]["value"] is None


def test_fhr3_r4_evaluation_registration_identity_is_revalidated(benchmark_db):
    db, organization, workspace, actor, registration, dataset, benchmark = benchmark_db
    registration.version = "tampered-without-fingerprint-refresh"
    db.flush()
    with pytest.raises(AIEvaluationError, match="evaluation_model_registration_fingerprint_mismatch"):
        create_evaluation_run(
            db, organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
            dataset_id=dataset.id, benchmark_id=benchmark.id, model_registration_id=registration.id,
            baseline_registration_id=None, prompt_version_id=None, policy_profile_id=None,
            input_fingerprint=benchmark_input_fingerprint(benchmark), environment_fingerprint="f" * 64,
            provenance={"methodology_version": "m1"}, actor_id=actor.id,
        )


def test_fhr3_r5_promotion_benchmark_requires_meaningful_metadata_and_provenance():
    from src.platform.ai.evaluation import validate_promotion_benchmark_manifest

    for field in (
        "dataset_key", "version", "capability_key", "schema_version",
        "source_provenance", "sensitivity_class", "owner",
    ):
        manifest = _benchmark_manifest()
        manifest[field] = "   "
        with pytest.raises(AIEvaluationError, match=f"promotion_benchmark_{field}_invalid"):
            validate_promotion_benchmark_manifest(manifest)

    for field in ("case_id", "language", "input_version", "sensitivity_class"):
        manifest = _benchmark_manifest()
        manifest["cases"][0][field] = "   "
        manifest["cases_sha256"] = cases_sha256(manifest["cases"])
        with pytest.raises(AIEvaluationError, match=f"promotion_benchmark_case_{field}_invalid"):
            validate_promotion_benchmark_manifest(manifest)

    manifest = _benchmark_manifest()
    manifest["cases"][0]["methodology_version"] = None
    manifest["cases_sha256"] = cases_sha256(manifest["cases"])
    validate_promotion_benchmark_manifest(manifest)

    manifest = _benchmark_manifest()
    manifest["cases"][0]["methodology_version"] = "   "
    manifest["cases_sha256"] = cases_sha256(manifest["cases"])
    with pytest.raises(AIEvaluationError, match="promotion_benchmark_case_methodology_version_invalid"):
        validate_promotion_benchmark_manifest(manifest)

    manifest = _benchmark_manifest()
    manifest["cases"][0]["source_refs"] = []
    manifest["cases_sha256"] = cases_sha256(manifest["cases"])
    with pytest.raises(AIEvaluationError, match="promotion_benchmark_source_references_invalid"):
        validate_promotion_benchmark_manifest(manifest)

    manifest = _benchmark_manifest()
    manifest["cases"][0]["human_gold_state"] = "draft"
    manifest["cases_sha256"] = cases_sha256(manifest["cases"])
    with pytest.raises(AIEvaluationError, match="promotion_benchmark_human_gold_state_invalid"):
        validate_promotion_benchmark_manifest(manifest)


def test_fhr3_r5_benchmark_execution_provenance_requires_real_source_references(benchmark_db):
    db, organization, workspace, actor, registration, dataset, benchmark = benchmark_db
    run = create_evaluation_run(
        db, organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
        dataset_id=dataset.id, benchmark_id=benchmark.id, model_registration_id=registration.id,
        baseline_registration_id=None, prompt_version_id=None, policy_profile_id=None,
        input_fingerprint=benchmark_input_fingerprint(benchmark), environment_fingerprint="e" * 64,
        provenance={"methodology_version": "m1"}, actor_id=actor.id,
    )
    row = benchmark_execution_provenance(
        db,
        run=run,
        cases=[
            {"case_id": "case-a", "source_refs": []},
            {"case_id": "case-b", "source_refs": []},
        ],
    )
    assert row["value"] is False
    assert row["evidence"]["source_refs"] == []
