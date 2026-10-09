"""Immutable report packets with live source authorization and invalidation guards."""
from datetime import date, datetime, timezone
import json
from uuid import UUID

from src.platform.extraction import service as extraction
from src.platform.extraction.contracts import ExtractionError
from src.platform.reporting.schemas import EvidenceLink
from src.platform.reporting.service import ReportingError, canonical_json, sha256_json
from src.platform.spatial.service import authorize, get_geometry, GeometryAccessError

SCHEMA = "ISI-LINKED-EVIDENCE-v1"
LIMIT = 2_000_000


def _rows(values):
    return [{"polje": k, "vrednost": v if isinstance(v, str) else canonical_json(v)} for k, v in values.items()]


def build(db, *, user_id, organization_id, workspace_id, product_code, request_id, link, storage=None):
    params = dict(organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    try:
        link = EvidenceLink.model_validate(link)
        value = extraction.detail(db, user_id=user_id, request_id=request_id, storage=storage, **params)
        if value["state"] != "REVIEWED_ACCEPTED" or not value["review"]["attested"]:
            raise ReportingError("linked_evidence_accepted_review_required")
        claims = [x for x in value["artifact"]["output"]["claims"] if x["id"] == link.claim_id]
        if len(claims) != 1:
            raise ReportingError("linked_evidence_claim_not_accessible")
        claim = claims[0]
        territory = next((x for x in value["review"]["territories"] if x["claim_id"] == link.claim_id), None)
        geometry = None
        if territory:
            geometry = get_geometry(db, user_id=user_id, geometry_id=UUID(territory["geometry_id"]),
                                    at_date=date.fromisoformat(territory["at_date"]), storage=storage, **params)
        result = {"status": "UNAVAILABLE", "reason": "NO_RESULT_SELECTED", "causal": False}
        if link.result_id:
            authorize(db, user_id=user_id, permission="analysis.read", **params)
            if product_code == "SIMPA":
                from src.domains.simpa.report_evidence import result_evidence
            elif product_code == "ORDO":
                from src.domains.ordo.report_evidence import result_evidence
            else:
                raise ReportingError("report_product_invalid")
            result = result_evidence(db, result_id=link.result_id, organization_id=organization_id, workspace_id=workspace_id)
    except ReportingError:
        raise
    except (ValueError, KeyError, TypeError) as exc:
        raise ReportingError("linked_evidence_no_longer_available") from exc
    packet = {
        "claim": claim, "source": value["artifact"]["source"],
        "anchor_units": value["artifact"]["anchor_units"],
        "extraction_provenance": {k: v for k, v in value["artifact"].items() if k not in {"output", "anchor_units", "source", "links"}},
        "extraction_fingerprint": value["artifact_fingerprint"],
        "review": value["review"], "territory": territory, "geometry": geometry,
        "numerical_evidence": result,
        "association": {"attested": link.attested, "note": link.note, "relation": "HUMAN_CONTEXT_ONLY"},
        "extraction_quality": "UNCALIBRATED", "truth_validation": False, "methodology_validation": False, "causal": False,
    }
    def serial(value):
        if isinstance(value, datetime):
            return value.replace(tzinfo=timezone.utc).isoformat() if value.tzinfo is None else value.astimezone(timezone.utc).isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return str(value)
    packet = json.loads(json.dumps(packet, default=serial, ensure_ascii=False, allow_nan=False))
    binding = {"request_id": str(request_id), "link": link.model_dump(mode="json")}
    content = {
        "schema": SCHEMA, "product_code": product_code, "report_type": "linked_evidence",
        "source_kind": "extraction_request", "source_id": str(request_id),
        "linked_evidence_binding": binding, "packet": packet,
        "sections": [
            {"key": "boundary", "title": "Obuhvat i odgovornost", "text": "Prihvaćena ekstrakcija nije potvrda istinitosti ili metodologije. Veza rezultata je ljudski izabran kontekst; sistem ne potvrđuje slaganje vrednosti, perioda ni teritorije. Kvalitet ekstrakcije nije kalibrisan."},
            {"key": "claim", "title": "Prihvaćeni nalaz", "text": claim["statement"]["quote"],
             "rows": _rows(packet["claim"])},
            {"key": "sources", "title": "Citati i poreklo", "rows": _rows(packet["source"])},
            {"key": "territory", "title": "Obuhvat nalaza", "rows": _rows(packet["territory"] or {"status": "UNRESOLVED"})},
            {"key": "result", "title": "Numerički rezultat i XAI", "rows": _rows(packet["numerical_evidence"])},
            {"key": "association", "title": "Ljudsko obrazloženje veze", "text": link.note},
            {"key": "review", "title": "Pregled izvora", "rows": _rows(packet["review"])},
        ],
        "human_accountability": "Institucionalna odluka ostaje ljudska; izveštaj ne daje automatsku preporuku.",
    }
    manifest = [{"kind": "linked_evidence_packet", "id": str(request_id), **{k: str(v) for k, v in params.items()},
                 "checksum": sha256_json(packet), "label": "Reviewed scoped claim/source/geometry/result packet"}]
    if len(canonical_json(content).encode()) > LIMIT:
        raise ReportingError("linked_evidence_size_limit")
    return content, manifest


def validate_version(db, *, user_id, report, version, storage=None):
    if version.content.get("schema") != SCHEMA and report.report_type != "linked_evidence":
        return  # historical report contract is compatibility, not newly guarded claim transport
    try:
        binding = version.content["linked_evidence_binding"]
        expected, manifest = build(db, user_id=user_id, organization_id=report.organization_id,
                                   workspace_id=report.workspace_id, product_code=report.product_code,
                                   request_id=UUID(binding["request_id"]), link=binding["link"], storage=storage)
        if (version.content != expected or version.source_manifest != manifest
                or version.content_sha256 != sha256_json(expected)
                or version.source_manifest_sha256 != sha256_json(manifest)):
            raise ReportingError("linked_evidence_version_changed")
    except (KeyError, TypeError, ValueError) as exc:
        raise ReportingError("linked_evidence_no_longer_available") from exc


def sources(db, *, user_id, **params):
    try:
        rows = extraction.listing(db, user_id=user_id, **params)
        return [{"kind": "extraction_request", "id": x["id"], "label": "Prihvaćena ekstrakcija " + x["id"][:8],
                 "status": x["state"]} for x in rows["items"] if x["state"] == "REVIEWED_ACCEPTED"]
    except (ExtractionError, GeometryAccessError):
        return []  # no extra data.read permission: existing numerical report discovery remains usable
