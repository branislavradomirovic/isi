"""Evidence-bound local extraction, worker guards and immutable human review."""

from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone, date
from uuid import UUID, uuid4
from sqlalchemy import select
from src.platform.extraction.contracts import ExtractionError, canonical, digest, validate_output
from src.platform.extraction.models import ExtractionRequest, ExtractionArtifact, ExtractionReview
from src.platform.spatial.service import authorize, get_geometry
from src.platform.ai.models import AIJob, AIJobAttempt, AIModel, AIPolicyProfile, AIPrompt, AIPromptVersion
from src.platform.ai.service import create_ai_job
from src.platform.data.models import (
    DataSource,
    DataSourceVersion,
    DataSourceGovernanceProfile,
    DataRetentionState,
    DataGovernanceInvalidation,
    DataAuditEvent,
)
from src.platform.data.storage import build_storage, scoped_storage_key
from src.platform.data.governance import ai_policy_capabilities, AnalyticalAIAction
from src.platform.data.analytical_service import load_governed_analytical_input, evaluate_analytical_ai_eligibility
from src.platform.ai.namespaces import private_namespace
from src.platform.identity.models import Membership


def adapter(product):
    if product == "SIMPA":
        from src.domains.simpa import extraction_adapter as module
    elif product == "ORDO":
        from src.domains.ordo import extraction_adapter as module
    else:
        raise ExtractionError("unsupported_product")
    return module


def scope(row):
    return {x: getattr(row, x) for x in ("organization_id", "workspace_id", "product_code")}


def scoped(db, model, key, params):
    if model is ExtractionRequest:
        result = db.scalar(select(model).where(model.id == key, *[getattr(model, k) == v for k, v in params.items()]))
    else:
        result = db.get(model, key)
    if result is None:
        raise ExtractionError("not_accessible")
    return result


def source_profile(db, version, params):
    if any(getattr(version, k) != v for k, v in params.items()):
        raise ExtractionError("source_not_accessible")
    source = db.get(DataSource, version.source_id)
    profile = db.scalar(
        select(DataSourceGovernanceProfile).where(DataSourceGovernanceProfile.source_id == version.source_id)
    )
    retention = db.scalar(select(DataRetentionState).where(DataRetentionState.version_id == version.id))
    invalid = db.scalar(
        select(DataGovernanceInvalidation.id).where(DataGovernanceInvalidation.upstream_version_id == version.id)
    )
    if (
        source is None
        or any(getattr(source, k) != v for k, v in params.items())
        or source.status != "active"
        or version.content_state != "AVAILABLE"
        or version.ingest_status != "succeeded"
        or invalid
        or (retention and retention.purge_status != "NONE")
        or profile is None
        or any(getattr(profile, k) != v for k, v in params.items())
        or profile.governance_state not in {"GOVERNED", "FROZEN"}
        or profile.privacy_category != "AGGREGATE_NON_PERSONAL"
        or profile.classification == "UNCLASSIFIED"
        or not profile.processing_purpose
        or not profile.data_owner_ref
        or AnalyticalAIAction.LOCAL_ANALYSIS not in ai_policy_capabilities(profile.ai_use_policy)
    ):
        raise ExtractionError("source_governance_ineligible")
    return {
        "source_id": str(source.id),
        "version_id": str(version.id),
        "version": version.version_no,
        "sha256": version.sha256,
        "governance_revision": profile.revision,
        "classification": profile.classification,
        "privacy": profile.privacy_category,
        "ai_policy": profile.ai_use_policy,
        "purpose": profile.processing_purpose,
    }


def load_input(db, kind, key, params, storage=None):
    units, sources = {}, []
    if kind == "document":
        version = db.get(DataSourceVersion, key)
        if version is None:
            raise ExtractionError("source_not_accessible")
        identity = source_profile(db, version, params)
        if version.extension != "txt" or db.get(DataSource, version.source_id).source_kind != "document":
            raise ExtractionError("document_format_unsupported")
        if version.size_bytes > 200000:
            raise ExtractionError("input_limit")
        expected = scoped_storage_key(
            **{k: str(v) for k, v in params.items()}, sha256=version.sha256, extension=version.extension
        )
        if version.storage_key != expected:
            raise ExtractionError("source_storage_scope_mismatch")
        try:
            raw = (storage or build_storage()).get_bytes(expected)
        except (OSError, RuntimeError):
            raise ExtractionError("source_storage_unavailable") from None
        if len(raw) != version.size_bytes or hashlib.sha256(raw).hexdigest() != version.sha256:
            raise ExtractionError("source_hash_mismatch")
        try:
            text = raw.decode("utf-8")  # preserve BOM/Unicode offsets, no normalization
        except UnicodeDecodeError:
            raise ExtractionError("document_encoding_unsupported") from None
        units["document"] = {
            "text": text,
            "source": identity,
            "locator": "txt:unicode-span",
            "page": None,
            "bbox": None,
        }
        sources = [identity]
    elif kind == "snapshot":
        eligible = evaluate_analytical_ai_eligibility(
            db,
            artifact_type="snapshot",
            artifact_id=key,
            action="LOCAL_ANALYSIS",
            namespace=private_namespace(params["organization_id"], params["product_code"]),
            **params,
        )
        if not eligible.allowed or eligible.privacy_category != "AGGREGATE_NON_PERSONAL":
            raise ExtractionError("snapshot_ai_ineligible")
        data = load_governed_analytical_input(db, artifact_type="snapshot", artifact_id=key, **params)
        seen = {}
        for record in data.records:
            version = db.get(DataSourceVersion, record.source_version_id)
            if version is None:
                raise ExtractionError("source_not_accessible")
            identity = source_profile(db, version, params)
            seen[str(version.id)] = identity
            for column, value in sorted(record.payload.items()):
                if value is None:
                    continue  # explicit missing; never convert null to zero
                unit = f"record:{record.normalized_record_id}:{column}"
                if len(unit) > 180:
                    raise ExtractionError("cell_locator_limit")
                text = value if isinstance(value, str) else canonical(value)
                units[unit] = {
                    "text": text,
                    "source": identity,
                    "locator": record.source_locator,
                    "column": column,
                    "record_sha256": record.content_fingerprint,
                    "record_id": str(record.normalized_record_id),
                    "page": None,
                    "bbox": None,
                }
        sources = list(seen.values())
        sources.append({"snapshot_id": str(key), "fingerprint": data.artifact_fingerprint})
    else:
        raise ExtractionError("input_kind_invalid")
    if not units or len(units) > 200 or sum(len(x["text"]) for x in units.values()) > 12000:
        raise ExtractionError("input_limit")
    identity = {"kind": kind, "id": str(key), "sources": sources, "units_sha256": digest(units)}
    return units, identity


def prompt_version(db, product, actor, *, allow_create=True):
    module = adapter(product)
    system, user, schema = (
        module.prompt(),
        "UNTRUSTED_SOURCE_UNITS_JSON:\n{input}",
        {
            "type": "object",
            "required": ["mentions", "claims"],
            "properties": {"mentions": {"type": "array"}, "claims": {"type": "array"}},
        },
    )
    checksum = hashlib.sha256((system + "\n" + user + "\n" + json.dumps(schema, sort_keys=True)).encode()).hexdigest()
    prompt = db.scalar(select(AIPrompt).where(AIPrompt.prompt_key == module.PROMPT_KEY))
    if prompt is None:
        if not allow_create:
            raise ExtractionError("prompt_registry_drift")
        prompt = AIPrompt(
            prompt_key=module.PROMPT_KEY,
            product_scope=product,
            title=product + " evidence extraction",
            purpose="Quoted entity/claim extraction",
            is_active=True,
        )
        db.add(prompt)
        db.flush()
    if not prompt.is_active or prompt.product_scope != product:
        raise ExtractionError("prompt_registry_drift")
    version = db.scalar(
        select(AIPromptVersion).where(AIPromptVersion.prompt_id == prompt.id, AIPromptVersion.version_no == 1)
    )
    if version is None:
        if not allow_create:
            raise ExtractionError("prompt_registry_drift")
        version = AIPromptVersion(
            prompt_id=prompt.id,
            version_no=1,
            system_template=system,
            user_template=user,
            output_schema=schema,
            checksum=checksum,
            status="active",
            created_by_membership_id=actor,
        )
        db.add(version)
        db.flush()
    if (
        version.status != "active"
        or version.checksum != checksum
        or version.system_template != system
        or version.user_template != user
        or version.output_schema != schema
    ):
        raise ExtractionError("prompt_registry_drift")
    return version


def policy(db, product):
    key = "simpa-sensitive-local" if product == "SIMPA" else "shared-local-only"
    row = db.scalar(select(AIPolicyProfile).where(AIPolicyProfile.policy_key == key))
    if row is None or not row.enabled or row.provider_policy != "local_only" or row.allow_external:
        raise ExtractionError("local_policy_unavailable")
    return row


def create_request(db, *, user_id, product_code, payload, storage=None):
    params = {
        "organization_id": payload.organization_id,
        "workspace_id": payload.workspace_id,
        "product_code": product_code,
    }
    actor = authorize(db, user_id=user_id, permission="ai.run", **params)
    authorize(db, user_id=user_id, permission="data.read", **params)
    old = db.scalar(
        select(ExtractionRequest).where(
            *[getattr(ExtractionRequest, k) == v for k, v in params.items()],
            ExtractionRequest.request_key == payload.request_key,
        )
    )
    if old:
        if old.binding["request"] != payload.model_dump(mode="json"):
            raise ExtractionError("idempotency_conflict")
        return old, False
    units, identity = load_input(db, payload.input_kind, payload.input_id, params, storage)
    version = prompt_version(db, product_code, actor)
    local_policy = policy(db, product_code)
    model = db.scalar(select(AIModel).where(AIModel.model_key == payload.model_key))
    if (
        model is None
        or not model.enabled
        or not model.local_provider
        or model.purpose != "chat"
        or model.product_scope not in {product_code, "SHARED"}
    ):
        raise ExtractionError("local_model_unavailable")
    request_text = canonical({"language": payload.language, "units": units})
    if len(request_text) > 20000:
        raise ExtractionError("input_limit")
    job = create_ai_job(
        db,
        **params,
        input_text=request_text,
        prompt_key=adapter(product_code).PROMPT_KEY,
        model_key=payload.model_key,
        policy_key=local_policy.policy_key,
        sensitivity="sensitive",
        actor_id=actor,
    )
    # Explicit documentary review independent of legacy policy review default.
    job.human_review_status = "pending"
    row = ExtractionRequest(
        **params, request_key=payload.request_key, job_id=job.id, created_by_membership_id=actor, state="PENDING"
    )
    row.binding = {
        "job_id": str(job.id),
        "actor_id": str(actor),
        "product_code": product_code,
        "request": payload.model_dump(mode="json"),
        "input": identity,
        "request_sha256": job.request_sha256,
        "prompt_id": str(version.id),
        "prompt_sha256": version.checksum,
        "model": {
            k: getattr(model, k)
            for k in [
                "model_key",
                "model_name",
                "provider_name",
                "provider_type",
                "product_scope",
                "local_provider",
                "purpose",
                "context_window",
                "max_output_tokens",
                "timeout_seconds",
            ]
        },
        "policy": {
            k: getattr(local_policy, k)
            for k in [
                "policy_key",
                "product_scope",
                "sensitivity",
                "provider_policy",
                "allow_external",
                "enabled",
                "require_human_review",
                "max_attempts",
            ]
        },
        "code_sha256": hashlib.sha256(__file_bytes(product_code)).hexdigest(),
        "schema": "ISI-EXTRACTION-v1",
    }
    row.fingerprint = digest(row.binding)
    db.add(row)
    db.flush()
    audit(db, row, actor, "extraction.created", row.fingerprint)
    return row, True


def __file_bytes(product):
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    paths = [
        Path(__file__),
        Path(__file__).with_name("contracts.py"),
        Path(__file__).with_name("models.py"),
        root / "domains" / product.lower() / "extraction_adapter.py",
        root / "domains" / product.lower() / "spatial_adapter.py",
    ]
    return canonical(
        {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    ).encode()


def audit(db, row, actor, event, fp):
    db.add(
        DataAuditEvent(
            **scope(row),
            actor_membership_id=actor,
            event_type=event,
            entity_type="extraction_request",
            entity_id=row.id,
            detail=canonical({"fingerprint": fp}),
        )
    )


def verify_request(db, row, storage=None, *, executing=False):
    if row.fingerprint != digest(row.binding) or row.state != "PENDING":
        raise ExtractionError("request_invalid_or_cancelled")
    if (
        row.binding["job_id"] != str(row.job_id)
        or row.binding["actor_id"] != str(row.created_by_membership_id)
        or row.binding["product_code"] != row.product_code
        or row.binding["request"]["organization_id"] != str(row.organization_id)
        or row.binding["request"]["workspace_id"] != str(row.workspace_id)
        or row.binding["request"]["request_key"] != str(row.request_key)
    ):
        raise ExtractionError("request_scope_changed")
    actor = db.get(Membership, row.created_by_membership_id)
    if actor is None or actor.status != "active" or actor.organization_id != row.organization_id:
        raise ExtractionError("actor_ineligible")
    authorize(db, user_id=actor.user_id, permission="ai.run", **scope(row))
    authorize(db, user_id=actor.user_id, permission="data.read", **scope(row))
    units, identity = load_input(
        db, row.binding["input"]["kind"], UUID(row.binding["input"]["id"]), scope(row), storage
    )
    if identity != row.binding["input"]:
        raise ExtractionError("source_changed")
    job = db.get(AIJob, row.job_id)
    if (
        job is None
        or any(getattr(job, k) != v for k, v in scope(row).items())
        or job.request_sha256 != row.binding["request_sha256"]
        or job.sensitivity != "sensitive"
        or job.model_registration_id is not None
    ):
        raise ExtractionError("job_binding_changed")
    version = prompt_version(db, row.product_code, row.created_by_membership_id, allow_create=False)
    if str(job.prompt_version_id) != row.binding["prompt_id"] or version.checksum != row.binding["prompt_sha256"]:
        raise ExtractionError("prompt_changed")
    model = db.get(AIModel, job.model_id)
    prof = db.get(AIPolicyProfile, job.policy_profile_id)
    if (
        model is None
        or not model.enabled
        or prof is None
        or job.effective_provider_policy != "local_only"
        or {k: getattr(model, k) for k in row.binding["model"]} != row.binding["model"]
        or {k: getattr(prof, k) for k in row.binding["policy"]} != row.binding["policy"]
        or (executing and row.binding["code_sha256"] != hashlib.sha256(__file_bytes(row.product_code)).hexdigest())
    ):
        raise ExtractionError("runtime_binding_changed")
    if job.request_text and hashlib.sha256(job.request_text.encode()).hexdigest() != job.request_sha256:
        raise ExtractionError("request_text_changed")
    return units, job


def suggestions(db, row, output):
    items = adapter(row.product_code).gazetteer(db, organization_id=row.organization_id, workspace_id=row.workspace_id)
    if len(items) > 200:
        raise ExtractionError("gazetteer_limit")
    result = {}
    for mention in output["mentions"]:
        matches = [x for x in items if x["name"].casefold() == mention["anchor"]["quote"].casefold()]
        result[mention["id"]] = {
            "state": "AMBIGUOUS" if len(matches) > 1 else "CANDIDATE" if matches else "UNRESOLVED",
            "alternatives": matches,
            "matching": "EXACT_NAME_ONLY",
            "resolved_identity": None,
        }
    return result


def worker_guard(db, job_id, *, after=False, storage=None):
    row = db.scalar(select(ExtractionRequest).where(ExtractionRequest.job_id == job_id).with_for_update())
    if row is None:
        return True  # legacy jobs unchanged
    job = db.get(AIJob, job_id)
    if not after and job.status not in {"queued"}:
        return False  # duplicate queue execution cannot refit/rewrite
    try:
        if not after and not job.request_text:
            raise ExtractionError("pending_request_text_missing")
        units, job = verify_request(db, row, storage, executing=True)
        if not after:
            return True
        if job.status not in {"succeeded", "review_required"}:
            return False
        output = validate_output(job.structured_output, units, adapter(row.product_code).KINDS)
        attempt = db.scalar(
            select(AIJobAttempt).where(
                AIJobAttempt.job_id == job.id,
                AIJobAttempt.attempt_no == job.attempts,
                AIJobAttempt.status == "succeeded",
            )
        )
        if (
            attempt is None
            or attempt.is_fallback
            or attempt.model_name != row.binding["model"]["model_name"]
            or attempt.provider_name != row.binding["model"]["provider_name"]
            or attempt.model_name != job.model_name
            or attempt.provider_name != job.provider_name
        ):
            raise ExtractionError("attempt_binding_invalid")
        payload = {
            "schema": "ISI-EXTRACTION-v1",
            "output": output,
            "source": row.binding["input"],
            "anchor_units": {
                k: {field: value for field, value in unit.items() if field != "text"} for k, unit in units.items()
            },
            "language": row.binding["request"]["language"],
            "job_id": str(job.id),
            "attempt_id": str(attempt.id),
            "attempt": attempt.attempt_no,
            "request_fingerprint": row.fingerprint,
            "model": row.binding["model"],
            "prompt_sha256": row.binding["prompt_sha256"],
            "policy": row.binding["policy"],
            "code_sha256": row.binding["code_sha256"],
            "links": suggestions(db, row, output),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": str(row.created_by_membership_id),
            "methodology_validated": False,
            "institutional_truth_validated": False,
        }
        artifact = ExtractionArtifact(id=uuid4(), request_id=row.id, payload=payload, fingerprint=digest(payload))
        db.add(artifact)
        # General AI job reads have no source-governance guard. Keep quotations only
        # in the extraction artifact, whose reads revalidate source and access.
        job.output_text = ""
        job.structured_output = None
        job.request_text = ""
        job.status = "review_required"
        job.human_review_status = "pending"
        db.flush()
        audit(db, row, row.created_by_membership_id, "extraction.extracted", artifact.fingerprint)
        return True
    except (ValueError, KeyError, TypeError, RuntimeError):
        # Never propagate provider/source payloads or nested validator errors.
        job.status = "failed"
        job.error_code = "extraction_validation_failed"
        job.error_message = "Evidence binding or extraction validation failed."
        job.output_text = ""
        job.structured_output = None
        job.request_text = ""
        job.finished_at = datetime.now(timezone.utc)
        audit(db, row, row.created_by_membership_id, "extraction.failed", row.fingerprint)
        db.flush()
        return False


def metadata(db, row):
    job = db.get(AIJob, row.job_id)
    artifact = db.scalar(select(ExtractionArtifact).where(ExtractionArtifact.request_id == row.id))
    review = (
        db.scalar(select(ExtractionReview).where(ExtractionReview.artifact_id == artifact.id)) if artifact else None
    )
    return {
        "id": str(row.id),
        "job_id": str(row.job_id),
        "state": row.state
        if row.state == "CANCELLED"
        else review.decision
        if review
        else "EXTRACTED_UNVERIFIED"
        if artifact
        else job.status,
        "artifact_fingerprint": artifact.fingerprint if artifact else None,
        "input_kind": row.binding["input"]["kind"],
        "input_id": row.binding["input"]["id"],
        "language": row.binding["request"]["language"],
    }


def listing(db, *, user_id, **params):
    authorize(db, user_id=user_id, permission="data.read", **params)
    rows = db.scalars(
        select(ExtractionRequest)
        .where(*[getattr(ExtractionRequest, k) == v for k, v in params.items()])
        .order_by(ExtractionRequest.created_at.desc(), ExtractionRequest.id)
        .limit(101)
    ).all()
    return {"items": [metadata(db, row) for row in rows[:100]], "truncated": len(rows) > 100}


def detail(db, *, user_id, request_id, storage=None, **params):
    authorize(db, user_id=user_id, permission="data.read", **params)
    row = scoped(db, ExtractionRequest, request_id, params)
    units, _ = verify_request(db, row, storage)
    result = metadata(db, row)
    artifact = db.scalar(select(ExtractionArtifact).where(ExtractionArtifact.request_id == row.id))
    if artifact:
        if (
            artifact.fingerprint != digest(artifact.payload)
            or artifact.payload["request_fingerprint"] != row.fingerprint
        ):
            raise ExtractionError("artifact_integrity_failed")
        if artifact.payload["anchor_units"] != {
            k: {field: value for field, value in unit.items() if field != "text"} for k, unit in units.items()
        }:
            raise ExtractionError("anchor_provenance_changed")
        validate_output(artifact.payload["output"], units, adapter(row.product_code).KINDS)
        result["artifact"] = artifact.payload
        review = db.scalar(select(ExtractionReview).where(ExtractionReview.artifact_id == artifact.id))
        if review:
            if (
                review.fingerprint != digest(review.payload)
                or review.payload["artifact_fingerprint"] != artifact.fingerprint
                or review.payload["decision"] != review.decision
                or review.payload["reviewer"] != str(review.reviewer_membership_id)
            ):
                raise ExtractionError("review_integrity_failed")
            current = adapter(row.product_code).gazetteer(
                db, organization_id=row.organization_id, workspace_id=row.workspace_id
            )
            for link in review.payload["entity_links"]:
                if link["identity"] not in current:
                    raise ExtractionError("entity_identity_changed")
            for territory in review.payload["territories"]:
                geometry = get_geometry(
                    db,
                    user_id=user_id,
                    geometry_id=UUID(territory["geometry_id"]),
                    at_date=date.fromisoformat(territory["at_date"]),
                    storage=storage,
                    **params,
                )
                if geometry["metadata"]["fingerprint"] != territory["geometry_fingerprint"]:
                    raise ExtractionError("territory_changed")
            result["review"] = review.payload
    return result


def review_request(db, *, user_id, request_id, payload, storage=None, **params):
    actor = authorize(db, user_id=user_id, permission="data.validate", **params)
    row = scoped(db, ExtractionRequest, request_id, params)
    result = detail(db, user_id=user_id, request_id=request_id, storage=storage, **params)
    artifact = db.scalar(select(ExtractionArtifact).where(ExtractionArtifact.request_id == row.id))
    if artifact is None or result.get("review") or payload.fingerprint != artifact.fingerprint:
        raise ExtractionError("review_conflict")
    if payload.decision == "REVIEWED_ACCEPTED" and not payload.attested:
        raise ExtractionError("review_attestation_required")
    claims = {x["id"]: x for x in artifact.payload["output"]["claims"]}
    mentions = {x["id"] for x in artifact.payload["output"]["mentions"]}
    current = adapter(row.product_code).gazetteer(
        db, organization_id=row.organization_id, workspace_id=row.workspace_id
    )
    if len(current) > 200:
        raise ExtractionError("gazetteer_limit")
    entity_links = []
    for link in payload.entity_links:
        matches = [x for x in current if x["id"] == str(link.domain_id) and x["kind"] == link.domain_kind]
        if link.mention_id not in mentions or len(matches) != 1:
            raise ExtractionError("entity_identity_not_accessible")
        entity_links.append({**link.model_dump(mode="json"), "identity": matches[0]})
    territories = []
    for territory in payload.territories:
        if territory.claim_id not in claims:
            raise ExtractionError("unknown_claim")
        geo = get_geometry(
            db, user_id=user_id, geometry_id=territory.geometry_id, at_date=territory.at_date, storage=storage, **params
        )
        if geo["metadata"]["geometry_type"] == "Point":
            raise ExtractionError("claim_scope_requires_area")
        territories.append(
            {
                **territory.model_dump(mode="json"),
                "geometry_fingerprint": geo["metadata"]["fingerprint"],
                "domain_binding": geo["metadata"]["domain_binding"],
            }
        )
    value = {
        "artifact_fingerprint": artifact.fingerprint,
        "decision": payload.decision,
        "attested": payload.attested,
        "note": payload.note,
        "territories": territories,
        "entity_links": entity_links,
        "reviewer": str(actor),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "truth_validation": False,
        "methodology_validation": False,
    }
    review = ExtractionReview(
        artifact_id=artifact.id,
        decision=payload.decision,
        payload=value,
        fingerprint=digest(value),
        reviewer_membership_id=actor,
    )
    db.add(review)
    job = db.get(AIJob, row.job_id)
    job.human_review_status = "accepted" if payload.decision == "REVIEWED_ACCEPTED" else "rejected"
    db.flush()
    audit(db, row, actor, "extraction.reviewed", review.fingerprint)
    return detail(db, user_id=user_id, request_id=request_id, storage=storage, **params)


def cancel(db, *, user_id, request_id, **params):
    actor = authorize(db, user_id=user_id, permission="ai.run", **params)
    row = scoped(db, ExtractionRequest, request_id, params)
    row = db.scalar(select(ExtractionRequest).where(ExtractionRequest.id == row.id).with_for_update())
    job = db.get(AIJob, row.job_id)
    if job.status != "queued" or row.state != "PENDING":
        raise ExtractionError("cancel_not_pending")
    row.state = "CANCELLED"
    job.request_text = ""
    job.status = "failed"
    job.error_code = "extraction_cancelled"
    job.error_message = "Cancelled before execution."
    audit(db, row, actor, "extraction.cancelled", row.fingerprint)
    return metadata(db, row)


def retrieve(db, *, user_id, geometry_id=None, period=None, storage=None, **params):
    items = listing(db, user_id=user_id, **params)
    if items["truncated"]:
        raise ExtractionError("retrieval_limit_refine_scope")
    result = []
    for item in items["items"]:
        if item["state"] != "REVIEWED_ACCEPTED":
            continue
        # Revalidation failure blocks the collection; never silently reuse stale quotes.
        value = detail(db, user_id=user_id, request_id=UUID(item["id"]), storage=storage, **params)
        territories = {x["claim_id"]: x for x in value["review"]["territories"]}
        for claim in value["artifact"]["output"]["claims"]:
            territory = territories.get(claim["id"])
            if geometry_id and (territory is None or territory["geometry_id"] != str(geometry_id)):
                continue
            if period is not None and (claim["period"] is None or claim["period"]["quote"] != period):
                continue
            result.append(
                {
                    "request_id": item["id"],
                    "fingerprint": value["artifact_fingerprint"],
                    "claim": claim,
                    "territory": territory,
                    "source": value["artifact"]["source"],
                    "reviewer": value["review"]["reviewer"],
                }
            )
            if len(result) > 100 or len(canonical(result).encode()) > 2000000:
                raise ExtractionError("retrieval_limit_refine_scope")
    return result
