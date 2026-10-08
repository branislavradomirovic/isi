from uuid import uuid4
from datetime import date
import hashlib
import pytest
from sqlalchemy import select
from test_isi_29b_spatial_registry import context as spatial_fixture, args, create as geometry_create, validate
from test_isi_29e_contracts import example
from src.platform.extraction import service as s
from src.platform.extraction.contracts import Create, Review, ExtractionError
from src.platform.extraction.models import ExtractionArtifact
from src.platform.ai.service import bootstrap_ai_registry, execute_ai_job
from src.platform.ai.models import AIJob, AIJobAttempt, AIModel
from src.platform.ai.providers import CompletionResult
from src.platform.data.models import DataSource, DataSourceVersion, DataSourceGovernanceProfile, DataAuditEvent
from src.platform.data.storage import scoped_storage_key
from src.domains.simpa.models import SimpaLocalActor

context = spatial_fixture


def document(c, product="SIMPA", text="Synthetic has 12 services in 2025."):
    db = c["db"]
    params = args(c, product)
    params.pop("user_id")
    source = DataSource(**params, name="Synthetic source " + uuid4().hex, source_kind="document", status="active")
    db.add(source)
    db.flush()
    raw = text.encode()
    sha = hashlib.sha256(raw).hexdigest()
    key = scoped_storage_key(**{k: str(v) for k, v in params.items()}, sha256=sha, extension="txt")
    c["storage"].put_bytes(key, raw)
    version = DataSourceVersion(
        **params,
        source_id=source.id,
        version_no=1,
        original_filename="synthetic.txt",
        extension="txt",
        size_bytes=len(raw),
        sha256=sha,
        storage_key=key,
        ingest_status="succeeded",
        content_state="AVAILABLE",
    )
    profile = DataSourceGovernanceProfile(
        **params,
        source_id=source.id,
        classification="INTERNAL",
        privacy_category="AGGREGATE_NON_PERSONAL",
        ai_use_policy="LOCAL_ANALYSIS_ONLY",
        governance_state="GOVERNED",
        processing_purpose="Synthetic aggregate evidence",
        data_owner_ref="Synthetic owner",
        revision=1,
    )
    db.add_all([version, profile])
    bootstrap_ai_registry(db, include_dev_stub=True)
    db.commit()
    return version, profile


def request(c, product="SIMPA", text="Synthetic has 12 services in 2025."):
    v, p = document(c, product, text)
    body = Create(
        organization_id=c["org"].id,
        workspace_id=c[product.lower()].id,
        input_kind="document",
        input_id=v.id,
        language="en",
        model_key="isi-ollama-chat-default",
        request_key=uuid4(),
    )
    row, new = s.create_request(c["db"], user_id=c["user"].id, product_code=product, payload=body, storage=c["storage"])
    c["db"].commit()
    assert new
    return row, body, v, p


def complete(c, row, output=None):
    db = c["db"]
    s.verify_request(db, row, c["storage"])
    assert s.worker_guard(db, row.job_id, storage=c["storage"])
    job = db.get(AIJob, row.job_id)
    job.status = "succeeded"
    job.attempts = 1
    job.model_name = db.get(AIModel, job.model_id).model_name
    job.provider_name = "ollama"
    job.structured_output = output or example()
    attempt = AIJobAttempt(
        job_id=job.id, attempt_no=1, provider_name=job.provider_name, model_name=job.model_name, status="succeeded"
    )
    db.add(attempt)
    db.flush()
    result = s.worker_guard(db, row.job_id, after=True, storage=c["storage"])
    db.commit()
    return result


@pytest.mark.parametrize("product", ["SIMPA", "ORDO"])
def test_immutable_lifecycle_review_and_retrieval(context, product):
    c = context
    row, body, v, p = request(c, product)
    same, new = s.create_request(
        c["db"], user_id=c["user"].id, product_code=product, payload=body, storage=c["storage"]
    )
    assert same.id == row.id and not new
    assert complete(c, row)
    value = s.detail(c["db"], **args(c, product), request_id=row.id, storage=c["storage"])
    assert value["state"] == "EXTRACTED_UNVERIFIED" and value["artifact"]["links"]["m1"]["resolved_identity"] is None
    assert s.retrieve(c["db"], **args(c, product), storage=c["storage"]) == []
    review = Review(
        fingerprint=value["artifact_fingerprint"],
        decision="REVIEWED_ACCEPTED",
        attested=True,
        note="Synthetic human review",
    )
    reviewed = s.review_request(c["db"], **args(c, product), request_id=row.id, payload=review, storage=c["storage"])
    c["db"].commit()
    assert reviewed["state"] == "REVIEWED_ACCEPTED" and not reviewed["review"]["truth_validation"]
    assert len(s.retrieve(c["db"], **args(c, product), period="2025", storage=c["storage"])) == 1
    assert s.retrieve(c["db"], **args(c, product), period="2026", storage=c["storage"]) == []
    with pytest.raises(ExtractionError):
        s.review_request(c["db"], **args(c, product), request_id=row.id, payload=review, storage=c["storage"])
    artifact = c["db"].scalar(select(ExtractionArtifact).where(ExtractionArtifact.request_id == row.id))
    artifact.payload = {}
    with pytest.raises(ValueError, match="immutable"):
        c["db"].flush()
    c["db"].rollback()
    events = c["db"].scalars(select(DataAuditEvent).where(DataAuditEvent.event_type.like("extraction.%"))).all()
    assert all(
        "Synthetic has" not in e.detail
        and "12" not in e.detail.replace(e.detail.split('"fingerprint":"')[1].split('"')[0], "")
        for e in events
    )


@pytest.mark.parametrize(
    "mutation", ["purge", "retire", "sensitive", "policy", "revision", "archived", "hash", "actor", "model"]
)
def test_revalidate_source_before_provider_and_read(context, mutation):
    c = context
    row, _, v, p = request(c)
    assert complete(c, row)
    if mutation == "purge":
        v.content_state = "PURGED"
    elif mutation == "retire":
        p.governance_state = "RETIRED"
    elif mutation == "sensitive":
        p.privacy_category = "SENSITIVE_PERSONAL_DATA"
    elif mutation == "policy":
        p.ai_use_policy = "PROHIBITED"
    elif mutation == "revision":
        p.revision += 1
    elif mutation == "archived":
        c["db"].get(DataSource, v.source_id).status = "archived"
    elif mutation == "hash":
        v.sha256 = "0" * 64
    elif mutation == "actor":
        c["member"].status = "suspended"
    elif mutation == "model":
        c["db"].get(AIModel, c["db"].get(AIJob, row.job_id).model_id).enabled = False
    c["db"].commit()
    with pytest.raises(ValueError):
        s.detail(c["db"], **args(c), request_id=row.id, storage=c["storage"])


def test_cancellation_duplicate_execution_and_hallucination(context):
    c = context
    row, _, _, _ = request(c)
    s.cancel(c["db"], **args(c), request_id=row.id)
    c["db"].commit()
    assert not s.worker_guard(c["db"], row.job_id, storage=c["storage"])
    row, _, _, _ = request(c)
    bad = example()
    bad["claims"][0]["value"]["quote"] = "99"
    assert not complete(c, row, bad)
    job = c["db"].get(AIJob, row.job_id)
    assert job.status == "failed" and job.structured_output is None and not job.output_text
    assert not s.worker_guard(c["db"], row.job_id, storage=c["storage"])


def test_ambiguity_and_claim_territory_review_revalidation(context):
    c = context
    row, _, _, _ = request(c)
    c["db"].add(
        SimpaLocalActor(
            organization_id=c["org"].id,
            workspace_id=c["simpa"].id,
            name="Synthetic",
            external_code="OTHER",
            actor_type="other",
        )
    )
    c["db"].commit()
    assert complete(c, row)
    result = s.detail(c["db"], **args(c), request_id=row.id, storage=c["storage"])
    assert result["artifact"]["links"]["m1"]["state"] == "AMBIGUOUS"
    g = geometry_create(c)
    validate(c, g)
    body = Review(
        fingerprint=result["artifact_fingerprint"],
        decision="REVIEWED_ACCEPTED",
        attested=True,
        note="Synthetic review",
        territories=[
            dict(claim_id="c1", geometry_id=g.id, at_date=date(2026, 1, 1), scope_note="Synthetic scope evidence")
        ],
    )
    s.review_request(c["db"], **args(c), request_id=row.id, payload=body, storage=c["storage"])
    c["db"].commit()
    assert len(s.retrieve(c["db"], **args(c), geometry_id=g.id, storage=c["storage"])) == 1
    assert s.retrieve(c["db"], **args(c), geometry_id=uuid4(), storage=c["storage"]) == []
    g.state = "RETIRED"
    c["db"].commit()
    with pytest.raises(ValueError):
        s.retrieve(c["db"], **args(c), storage=c["storage"])


def test_cross_product_and_scope_denied(context):
    c = context
    row, body, v, p = request(c)
    with pytest.raises(ValueError):
        s.detail(c["db"], **args(c, "ORDO"), request_id=row.id, storage=c["storage"])
    body.input_id = v.id
    body.workspace_id = c["ordo"].id
    body.request_key = uuid4()
    with pytest.raises(ValueError):
        s.create_request(c["db"], user_id=c["user"].id, product_code="ORDO", payload=body, storage=c["storage"])


def test_real_gateway_exact_schema_then_worker_finalization(context, monkeypatch):
    c = context
    row, _, _, _ = request(c)

    class Synthetic:
        def complete(self, req):
            assert "UNTRUSTED" in req.user_prompt and "SIMPA" in req.system_prompt
            from src.platform.extraction.contracts import canonical

            return CompletionResult(
                text=canonical(example()),
                provider_name="ollama",
                model_name=c["db"].get(AIModel, c["db"].get(AIJob, row.job_id).model_id).model_name,
                latency_ms=1,
                input_tokens=None,
                output_tokens=None,
            )

    monkeypatch.setattr("src.platform.ai.service.provider_for_model", lambda _: Synthetic())
    assert s.worker_guard(c["db"], row.job_id, storage=c["storage"])
    execute_ai_job(c["db"], job_id=row.job_id)
    assert s.worker_guard(c["db"], row.job_id, after=True, storage=c["storage"])
    c["db"].commit()
    assert s.detail(c["db"], **args(c), request_id=row.id, storage=c["storage"])["state"] == "EXTRACTED_UNVERIFIED"


def test_tamper_artifact_review_detected(context):
    c = context
    row, _, _, _ = request(c)
    complete(c, row)
    a = c["db"].scalar(select(ExtractionArtifact).where(ExtractionArtifact.request_id == row.id))
    # In-memory JSON tamper (not persisted ORM update) must fail read fingerprint.
    a.payload["output"]["claims"][0]["value"]["quote"] = "99"
    with pytest.raises(ExtractionError):
        s.detail(c["db"], **args(c), request_id=row.id, storage=c["storage"])


def test_human_identity_resolution_and_changed_registry_block(context):
    c = context
    row, _, _, _ = request(c)
    assert complete(c, row)
    value = s.detail(c["db"], **args(c), request_id=row.id, storage=c["storage"])
    review = Review(
        fingerprint=value["artifact_fingerprint"],
        decision="REVIEWED_ACCEPTED",
        attested=True,
        note="Synthetic source inspected",
        entity_links=[
            dict(
                mention_id="m1",
                domain_kind="local_system",
                domain_id=c["local"].id,
                evidence_note="Synthetic exact registry evidence",
            )
        ],
    )
    s.review_request(c["db"], **args(c), request_id=row.id, payload=review, storage=c["storage"])
    c["db"].commit()
    assert len(s.retrieve(c["db"], **args(c), storage=c["storage"])) == 1
    c["local"].jurisdiction_code = "CHANGED"
    c["db"].commit()
    with pytest.raises(ExtractionError, match="entity_identity_changed"):
        s.retrieve(c["db"], **args(c), storage=c["storage"])


def test_governed_snapshot_cells_and_invalidation(tmp_path):
    from test_isi_22g_domain_consumption import _domain_case

    db, org, ws, _, _, _, snapshot, record = _domain_case(tmp_path)
    params = dict(organization_id=org.id, workspace_id=ws.id, product_code="SIMPA")
    version = db.get(DataSourceVersion, record.source_version_id)
    version.ingest_status = "succeeded"
    db.flush()
    units, identity = s.load_input(db, "snapshot", snapshot.id, params)
    assert any(x["text"] == "12.5" and x["record_id"] == str(record.id) for x in units.values())
    assert not any(x["column"] == "value_text" for x in units.values())
    assert identity["sources"][-1]["fingerprint"] == snapshot.fingerprint
    record.normalized_record_json = record.normalized_record_json.replace("12.5", "99.0")
    db.flush()
    with pytest.raises(ValueError):
        s.load_input(db, "snapshot", snapshot.id, params)
    db.close()


def test_source_revoked_before_provider_never_executes(context, monkeypatch):
    c = context
    row, _, _, profile = request(c)
    profile.governance_state = "RETIRED"
    c["db"].commit()
    calls = []
    monkeypatch.setattr("src.platform.ai.service.provider_for_model", lambda *_: calls.append(1))
    assert not s.worker_guard(c["db"], row.job_id, storage=c["storage"])
    assert not calls and c["db"].get(AIJob, row.job_id).error_code == "extraction_validation_failed"


def test_existing_worker_blocks_invalid_source_and_keeps_legacy_lane(context, monkeypatch):
    from src.workers.ai_jobs import run_ai_job

    c = context
    row, _, _, profile = request(c)
    profile.governance_state = "RETIRED"
    c["db"].commit()
    calls = []
    monkeypatch.setattr("src.workers.ai_jobs.build_session_factory", lambda: lambda: c["db"])
    monkeypatch.setattr("src.workers.ai_jobs.execute_ai_job", lambda *a, **kw: calls.append(kw))
    monkeypatch.setattr("src.platform.extraction.service.build_storage", lambda: c["storage"])
    run_ai_job(str(row.job_id))
    assert not calls and c["db"].get(AIJob, row.job_id).status == "failed"
    assert s.worker_guard(c["db"], uuid4())  # non-extraction jobs retain existing worker behavior


def test_request_binding_immutable_and_document_size_limit(context):
    c = context
    row, _, _, _ = request(c)
    row.job_id = uuid4()
    with pytest.raises(ValueError, match="immutable"):
        c["db"].flush()
    c["db"].rollback()
    v, _ = document(c, text="x" * 12001)
    with pytest.raises(ExtractionError, match="input_limit"):
        s.load_input(c["db"], "document", v.id, {k: v for k, v in args(c).items() if k != "user_id"}, c["storage"])


@pytest.mark.parametrize("mutation", ["policy_attempts", "model_timeout", "request_erased"])
def test_full_runtime_policy_and_model_parameters_pinned(context, mutation):
    c = context
    row, _, _, _ = request(c)
    job = c["db"].get(AIJob, row.job_id)
    if mutation == "policy_attempts":
        from src.platform.ai.models import AIPolicyProfile

        c["db"].get(AIPolicyProfile, job.policy_profile_id).max_attempts += 1
    elif mutation == "model_timeout":
        c["db"].get(AIModel, job.model_id).timeout_seconds += 1
    else:
        job.request_text = ""
    c["db"].commit()
    assert not s.worker_guard(c["db"], job.id, storage=c["storage"])
    assert job.status == "failed" and job.structured_output is None


def test_storage_io_failure_sanitized_before_provider(context):
    c = context
    row, _, _, _ = request(c)

    class Unavailable:
        def get_bytes(self, key):
            raise PermissionError("PRIVATE_STORAGE_DETAIL")

    assert not s.worker_guard(c["db"], row.job_id, storage=Unavailable())
    job = c["db"].get(AIJob, row.job_id)
    assert job.status == "failed" and not job.request_text and "PRIVATE" not in job.error_message


def test_generic_ai_job_cannot_bypass_extraction_source_governance(context):
    from src.platform.ai.service import job_response

    c = context
    row, _, version, _ = request(c)
    assert complete(c, row)
    job = c["db"].get(AIJob, row.job_id)
    response = job_response(c["db"], job)
    assert response.output_text == "" and response.structured_output is None and job.request_text == ""
    assert s.detail(c["db"], **args(c), request_id=row.id, storage=c["storage"])["artifact"]["output"]["claims"]
    version.content_state = "PURGED"
    c["db"].commit()
    with pytest.raises(ValueError):
        s.detail(c["db"], **args(c), request_id=row.id, storage=c["storage"])
    assert job_response(c["db"], job).output_text == "" and job_response(c["db"], job).structured_output is None


def test_pending_component_code_change_blocks_execution(context, monkeypatch):
    c = context
    row, _, _, _ = request(c)
    monkeypatch.setattr(s, "__file_bytes", lambda product: b"changed-component")
    assert not s.worker_guard(c["db"], row.job_id, storage=c["storage"])
    assert c["db"].get(AIJob, row.job_id).status == "failed"
