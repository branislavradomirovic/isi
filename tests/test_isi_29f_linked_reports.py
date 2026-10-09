from pathlib import Path
from uuid import uuid4
import pytest
from pydantic import ValidationError
from test_isi_29e_service import context as extraction_context, request, complete
from test_isi_29b_spatial_registry import args, create as geometry_create, validate
from src.platform.extraction import service as extraction
from src.platform.extraction.contracts import Review
from src.platform.reporting import linked_evidence as linked, service as reports
from src.platform.reporting.schemas import EvidenceLink
from src.platform.reporting.render import render_html, render_json

context = extraction_context


def accepted(c, product="SIMPA", territory=False):
    row, _body, version, profile = request(c, product)
    assert complete(c, row)
    result = extraction.detail(c["db"], **args(c, product), request_id=row.id, storage=c["storage"])
    territories = []
    geometry = None
    if territory:
        geometry = geometry_create(c, product)
        validate(c, geometry, product)
        territories = [{"claim_id": "c1", "geometry_id": geometry.id, "at_date": geometry.valid_from, "scope_note": "Synthetic declared source area"}]
    extraction.review_request(c["db"], **args(c, product), request_id=row.id, storage=c["storage"],
                              payload=Review(fingerprint=result["artifact_fingerprint"], decision="REVIEWED_ACCEPTED",
                                             attested=True, note="Synthetic review", territories=territories))
    c["db"].commit()
    return row, version, profile, geometry


def build(c, row, product="SIMPA", **changes):
    return linked.build(c["db"], **args(c, product), request_id=row.id,
                        link=EvidenceLink(claim_id="c1", attested=True, note="Synthetic contextual association", **changes), storage=c["storage"])


@pytest.mark.parametrize("product", ["SIMPA", "ORDO"])
@pytest.mark.parametrize("territory", [False, True])
def test_source_claim_map_review_report_export_e2e(context, product, territory):
    c = context
    row, version, profile, geo = accepted(c, product, territory)
    content, manifest = build(c, row, product)
    assert content["packet"]["truth_validation"] is False
    assert content["packet"]["extraction_quality"] == "UNCALIBRATED"
    assert content["packet"]["numerical_evidence"]["status"] == "UNAVAILABLE"
    assert bool(content["packet"]["geometry"]) == territory
    if territory:
        assert content["packet"]["geometry"]["metadata"]["id"] == str(geo.id)
    scope = args(c, product)
    scope.pop("user_id")
    report, report_version = reports.create_report(c["db"], **scope, report_type="linked_evidence", title="Synthetic linked report",
                                                  content=content, source_manifest=manifest, actor_id=c["member"].id)
    linked.validate_version(c["db"], user_id=c["user"].id, report=report, version=report_version, storage=c["storage"])
    reports.submit_version(c["db"], report_version)
    reports.review_version(c["db"], version=report_version, reviewer_id=c["member"].id, decision="approved", note="Synthetic report review")
    reports.publish_version(c["db"], version=report_version, report=report)
    for fmt in ["html", "markdown", "json"]:
        linked.validate_version(c["db"], user_id=c["user"].id, report=report, version=report_version, storage=c["storage"])
        export = reports.create_export(c["db"], report=report, version=report_version, export_format=fmt, actor_id=c["member"].id)
        assert export.content_text and len(export.sha256) == 64
    # The complete immutable version and prior saved exports cannot bypass source withdrawal.
    profile.governance_state = "DRAFT"
    c["db"].commit()
    with pytest.raises(reports.ReportingError, match="no_longer_available"):
        linked.validate_version(c["db"], user_id=c["user"].id, report=report, version=report_version, storage=c["storage"])


@pytest.mark.parametrize("product", ["SIMPA", "ORDO"])
def test_unreviewed_rejected_missing_and_cross_product_fail(context, product):
    c = context
    row, *_ = request(c, product)
    complete(c, row)
    with pytest.raises(reports.ReportingError, match="accepted_review"):
        build(c, row, product)
    result = extraction.detail(c["db"], **args(c, product), request_id=row.id, storage=c["storage"])
    extraction.review_request(c["db"], **args(c, product), request_id=row.id, storage=c["storage"],
                              payload=Review(fingerprint=result["artifact_fingerprint"], decision="REJECTED", attested=False, note="Synthetic rejection"))
    with pytest.raises(reports.ReportingError):
        build(c, row, product)
    other = "ORDO" if product == "SIMPA" else "SIMPA"
    with pytest.raises(reports.ReportingError):
        build(c, row, other)


@pytest.mark.parametrize("changes", [{"attested": False}, {"attested": 1}, {"note": "   "}, {"extra": "bad"}, {"claim_id": "wrong"}])
def test_explicit_bounded_link_contract(changes):
    fields = {"claim_id": "c1", "note": "Synthetic note", "attested": True, **changes}
    with pytest.raises(ValidationError):
        EvidenceLink(**fields)


def test_result_id_wrong_scope_and_unknown_claim(context):
    row, *_ = accepted(context)
    with pytest.raises(reports.ReportingError):
        build(context, row, result_id=uuid4())
    with pytest.raises(reports.ReportingError):
        linked.build(context["db"], **args(context), request_id=row.id,
                     link=EvidenceLink(claim_id="c2", attested=True, note="Missing claim"), storage=context["storage"])


def test_packet_tamper_and_revoked_user(context):
    c = context
    row, *_ = accepted(c)
    content, manifest = build(c, row)
    scope = args(c)
    scope.pop("user_id")
    report, version = reports.create_report(c["db"], **scope, report_type="linked_evidence", title="Synthetic packet",
                                            content=content, source_manifest=manifest, actor_id=c["member"].id)
    version.content_sha256 = "0" * 64
    with pytest.raises(reports.ReportingError):
        linked.validate_version(c["db"], user_id=c["user"].id, report=report, version=version, storage=c["storage"])
    with pytest.raises(reports.ReportingError):
        linked.build(c["db"], user_id=uuid4(), **scope, request_id=row.id,
                     link=EvidenceLink(claim_id="c1", attested=True, note="Synthetic association"), storage=c["storage"])


def test_renderer_escapes_claim_markup(context):
    c = context
    row, *_ = accepted(c)
    content, manifest = build(c, row)
    content["sections"][0]["text"] = '<script>alert("bad")</script>'
    metadata = {"title": "Synthetic", "product_code": "SIMPA", "report_type": "linked_evidence", "version_no": 1, "status": "approved", "content_sha256": "0" * 64}
    html = render_html(metadata=metadata, content=content, source_manifest=manifest)
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert '"packet"' in render_json(metadata=metadata, content=content, source_manifest=manifest)


def test_api_all_quote_delivery_paths_guarded_and_ui_no_cached_exports():
    text = Path("src/api/reporting_routes.py").read_text()
    assert text.count("linked_evidence.validate_version(") == 6
    assert '"/linked-preview"' in text and "evidence_link=payload.evidence_link" in text
    ui = Path("src/streamlit_app/reporting_workspace.py").read_text()
    assert "report_export_" not in ui
    from src.streamlit_app.linked_reporting_workspace import HELP
    assert len(HELP) == 10
