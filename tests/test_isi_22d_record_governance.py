from __future__ import annotations

import base64
import hashlib
import inspect
import io
import json
import uuid
import zipfile
from decimal import localcontext
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from src.api import data_routes
from src.core.database import Base
from src.platform.access.models import Product
from src.platform.data.ingestion import IngestionError, StructuredRecord, extract_structured_records
from src.platform.data.ingestion_run_service import create_ingestion_run, retry_ingestion_run
from src.platform.data.models import (
    DataAuditEvent,
    DataConnectorContractVersion,
    DataIngestionRun,
    DataNormalizedRecord,
    DataQualityResult,
    DataRecordEntity,
    DataRecordGovernancePolicyVersion,
    DataRecordResolution,
    DataSource,
    DataSourceSchemaMappingVersion,
    DataSourceVersion,
    IngestionJob,
)
from src.platform.data.record_governance_service import (
    activate_record_governance_policy_version,
    create_record_governance_policy_version,
    get_record_quarantine_detail,
    list_record_governance_policy_versions,
    list_record_quarantine,
    materialize_ingestion_run_records,
    resolve_quarantined_record,
)
from src.platform.data.schemas import (
    IngestionRunCreate,
    RecordGovernancePolicyActivationRequest,
    RecordGovernancePolicyVersionCreate,
    RecordResolutionCreate,
)
from src.platform.data.service import DataPlatformError
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace
from src.workers import data_jobs


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _default_schema():
    return [
        {
            "ordinal": 1,
            "source_field": "external_id",
            "logical_type": "STRING",
            "required": True,
            "nullable": False,
            "missing_values": ["", "NA"],
        },
        {
            "ordinal": 2,
            "source_field": "name",
            "logical_type": "STRING",
            "required": False,
            "nullable": True,
            "missing_values": [""],
        },
    ]


def _mapping_for(schema):
    return [
        {
            "source_field": field["source_field"],
            "disposition": "MAP",
            "field_key": f"record.{field['source_field']}",
        }
        for field in schema
    ]


def _build_case(tmp_path, *, schema=None, field_mapping=None, schema_kind="TABULAR", unexpected="REJECT"):
    schema = schema or _default_schema()
    field_mapping = field_mapping or _mapping_for(schema)
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    db.add_all(
        [
            Product(code="SIMPA", name="SIMPA", is_active=True),
            Product(code="ORDO", name="ORDO", is_active=True),
        ]
    )
    marker = uuid.uuid4().hex
    organization = Organization(slug=f"rec-{marker}", name="Record governance")
    user = User(email=f"rec-{marker}@example.invalid", display_name="Record steward")
    db.add_all([organization, user])
    db.flush()
    membership = Membership(user_id=user.id, organization_id=organization.id, status="active")
    workspace = Workspace(
        organization_id=organization.id,
        product_code="SIMPA",
        slug=f"rec-{marker}",
        name="Record workspace",
        status="active",
    )
    db.add_all([membership, workspace])
    db.flush()
    source = DataSource(
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        name="Source-local records",
        source_kind="dataset",
        status="active",
        created_by_membership_id=membership.id,
    )
    other_source = DataSource(
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        name="Other records",
        source_kind="dataset",
        status="active",
    )
    db.add_all([source, other_source])
    db.flush()
    connector = DataConnectorContractVersion(
        source_id=source.id,
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        version_no=1,
        connector_kind="synthetic",
        transport="batch",
        fingerprint="a" * 64,
        lifecycle_state="ACTIVE",
    )
    db.add(connector)
    db.flush()
    mapping = DataSourceSchemaMappingVersion(
        source_id=source.id,
        connector_contract_version_id=connector.id,
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        version_no=1,
        contract_format_version=1,
        schema_kind=schema_kind,
        source_schema_json=_canonical(schema),
        field_mapping_json=_canonical(field_mapping),
        missing_value_policy="PRESERVE_MISSING",
        unexpected_field_policy=unexpected,
        fingerprint="b" * 64,
        lifecycle_state="ACTIVE",
    )
    db.add(mapping)
    db.commit()
    return {
        "db": db,
        "storage": LocalFilesystemStorage(tmp_path / "storage"),
        "organization": organization,
        "workspace": workspace,
        "membership": membership,
        "source": source,
        "other_source": other_source,
        "connector": connector,
        "mapping": mapping,
        "schema": schema,
    }


def _policy_payload(case, **changes):
    values = {
        "organization_id": case["organization"].id,
        "workspace_id": case["workspace"].id,
        "product_code": "SIMPA",
        "connector_contract_version_id": case["connector"].id,
        "schema_mapping_version_id": case["mapping"].id,
        "identity_field_keys": ["record.external_id"],
    }
    values.update(changes)
    return RecordGovernancePolicyVersionCreate(**values)


def _create_and_activate_policy(case, **changes):
    response = create_record_governance_policy_version(
        case["db"],
        source_id=case["source"].id,
        payload=_policy_payload(case, **changes),
        actor_id=case["membership"].id,
    )
    activate_record_governance_policy_version(
        case["db"],
        source_id=case["source"].id,
        policy_id=response.id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
        actor_id=case["membership"].id,
    )
    case["db"].flush()
    return case["db"].get(DataRecordGovernancePolicyVersion, response.id)


def _create_run(case, raw, *, filename="batch.csv", key=None, cursor=None):
    marker = key or uuid.uuid4().hex
    request = IngestionRunCreate(
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
        connector_contract_version_id=case["connector"].id,
        schema_mapping_version_id=case["mapping"].id,
        idempotency_key=f"record:{marker}",
        filename=filename,
        content_type="application/octet-stream",
        content_base64=base64.b64encode(raw).decode("ascii"),
        cursor_after=cursor or marker,
    )
    response = create_ingestion_run(
        case["db"],
        case["storage"],
        source_id=case["source"].id,
        request=request,
        payload_bytes=raw,
        actor_id=case["membership"].id,
        backend="inline",
    )
    return case["db"].get(DataIngestionRun, response.run.id)


def _finish_run(case, run):
    run.status = "SUCCEEDED"
    case["db"].get(IngestionJob, run.inspection_job_id).status = "succeeded"
    case["db"].get(DataSourceVersion, run.source_version_id).ingest_status = "succeeded"
    case["db"].flush()


def test_policy_create_normalizes_fingerprints_lists_and_rejects_semantic_noop(tmp_path):
    case = _build_case(tmp_path)
    response = create_record_governance_policy_version(
        case["db"],
        source_id=case["source"].id,
        payload=_policy_payload(
            case,
            identity_field_keys=[" RECORD.NAME ", "record.external_id", "record.name"],
        ),
        actor_id=case["membership"].id,
    )
    assert response.identity_field_keys == ["record.external_id", "record.name"]
    assert response.lifecycle_state == "DRAFT" and response.version_no == 1
    semantic = {
        "source_id": str(case["source"].id),
        "connector_contract_version_id": str(case["connector"].id),
        "schema_mapping_version_id": str(case["mapping"].id),
        "contract_format_version": 1,
        "identity_field_keys": ["record.external_id", "record.name"],
        "missing_identity_policy": "QUARANTINE",
        "exact_duplicate_policy": "LINK_EXISTING",
        "conflict_policy": "QUARANTINE",
    }
    assert response.fingerprint == hashlib.sha256(_canonical(semantic).encode()).hexdigest()
    assert [item.id for item in list_record_governance_policy_versions(
        case["db"], source_id=case["source"].id,
        organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code="SIMPA",
    )] == [response.id]
    with pytest.raises(DataPlatformError, match="record_policy_unchanged"):
        create_record_governance_policy_version(
            case["db"], source_id=case["source"].id,
            payload=_policy_payload(case, identity_field_keys=["record.name", "record.external_id"]),
            actor_id=case["membership"].id,
        )


def test_policy_validates_mapped_identity_exact_binding_scope_and_lifecycle(tmp_path):
    case = _build_case(tmp_path)
    with pytest.raises(DataPlatformError, match="record_policy_identity_field_not_mapped"):
        create_record_governance_policy_version(
            case["db"], source_id=case["source"].id,
            payload=_policy_payload(case, identity_field_keys=["record.unknown"]),
            actor_id=case["membership"].id,
        )
    with pytest.raises(DataPlatformError, match="connector_contract_version_not_accessible"):
        create_record_governance_policy_version(
            case["db"], source_id=case["other_source"].id,
            payload=_policy_payload(case), actor_id=case["membership"].id,
        )
    case["mapping"].lifecycle_state = "DRAFT"
    draft = create_record_governance_policy_version(
        case["db"], source_id=case["source"].id,
        payload=_policy_payload(case), actor_id=case["membership"].id,
    )
    with pytest.raises(DataPlatformError, match="record_policy_mapping_not_active"):
        activate_record_governance_policy_version(
            case["db"], source_id=case["source"].id, policy_id=draft.id,
            organization_id=case["organization"].id, workspace_id=case["workspace"].id,
            product_code="SIMPA", actor_id=case["membership"].id,
        )


def test_policy_activation_rollover_retirement_and_idempotence(tmp_path):
    case = _build_case(tmp_path)
    first = _create_and_activate_policy(case)
    same = activate_record_governance_policy_version(
        case["db"], source_id=case["source"].id, policy_id=first.id,
        organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code="SIMPA", actor_id=case["membership"].id,
    )
    assert same.lifecycle_state == "ACTIVE"
    second_created = create_record_governance_policy_version(
        case["db"], source_id=case["source"].id,
        payload=_policy_payload(case, identity_field_keys=["record.name"]),
        actor_id=case["membership"].id,
    )
    second = activate_record_governance_policy_version(
        case["db"], source_id=case["source"].id, policy_id=second_created.id,
        organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code="SIMPA", actor_id=case["membership"].id,
    )
    assert second.lifecycle_state == "ACTIVE"
    assert case["db"].get(DataRecordGovernancePolicyVersion, first.id).lifecycle_state == "RETIRED"
    with pytest.raises(DataPlatformError, match="record_policy_state_conflict"):
        activate_record_governance_policy_version(
            case["db"], source_id=case["source"].id, policy_id=first.id,
            organization_id=case["organization"].id, workspace_id=case["workspace"].id,
            product_code="SIMPA", actor_id=case["membership"].id,
        )


def test_new_run_policy_pin_backward_compatibility_rollover_mismatch_and_retired_retry(tmp_path):
    no_policy = _build_case(tmp_path / "none")
    legacy = _create_run(no_policy, b"external_id,name\n1,Alice\n", key="legacy")
    assert legacy.record_governance_policy_version_id is None

    case = _build_case(tmp_path / "pinned")
    policy = _create_and_activate_policy(case)
    run = _create_run(case, b"external_id,name\n1,Alice\n", key="pinned")
    assert run.record_governance_policy_version_id == policy.id
    run.status = "FAILED"
    case["db"].get(IngestionJob, run.inspection_job_id).status = "failed"
    case["db"].get(DataSourceVersion, run.source_version_id).ingest_status = "failed"
    policy.lifecycle_state = "RETIRED"
    response = retry_ingestion_run(
        case["db"], source_id=case["source"].id, run_id=run.id,
        organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code="SIMPA", actor_id=case["membership"].id,
    )
    assert response.record_governance_policy_version_id == policy.id

    mismatch = _build_case(tmp_path / "mismatch")
    _create_and_activate_policy(mismatch)
    mismatch["connector"].lifecycle_state = "RETIRED"
    mismatch["mapping"].lifecycle_state = "RETIRED"
    replacement_connector = DataConnectorContractVersion(
        source_id=mismatch["source"].id, organization_id=mismatch["organization"].id,
        workspace_id=mismatch["workspace"].id, product_code="SIMPA", version_no=2,
        connector_kind="replacement", transport="batch", fingerprint="c" * 64,
        lifecycle_state="ACTIVE",
    )
    mismatch["db"].add(replacement_connector); mismatch["db"].flush()
    replacement_mapping = DataSourceSchemaMappingVersion(
        source_id=mismatch["source"].id, connector_contract_version_id=replacement_connector.id,
        organization_id=mismatch["organization"].id, workspace_id=mismatch["workspace"].id,
        product_code="SIMPA", version_no=2, contract_format_version=1, schema_kind="TABULAR",
        source_schema_json=mismatch["mapping"].source_schema_json,
        field_mapping_json=mismatch["mapping"].field_mapping_json,
        missing_value_policy="PRESERVE_MISSING", unexpected_field_policy="REJECT",
        fingerprint="d" * 64, lifecycle_state="ACTIVE",
    )
    mismatch["db"].add(replacement_mapping); mismatch["db"].flush()
    mismatch["connector"] = replacement_connector
    mismatch["mapping"] = replacement_mapping
    before = mismatch["db"].scalar(select(func.count()).select_from(DataSourceVersion))
    with pytest.raises(DataPlatformError, match="record_policy_binding_mismatch"):
        _create_run(mismatch, b"external_id,name\n2,Bob\n", key="mismatch")
    assert mismatch["db"].scalar(select(func.count()).select_from(DataSourceVersion)) == before


def _xlsx_payload(*, sheet_count=1, formula=False):
    workbook_sheets = "".join(
        f'<sheet name="Sheet{i}" sheetId="{i}" r:id="rId{i}"/>'
        for i in range(1, sheet_count + 1)
    )
    relationships = "".join(
        f'<Relationship Id="rId{i}" '
        f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{i}.xml"/>'
        for i in range(1, sheet_count + 1)
    )
    formula_xml = "<f>1+1</f>" if formula else ""
    sheet = (
        '<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
        f'<row r="2"><c r="A2" t="s">{formula_xml}<v>2</v></c><c r="B2"><v>42</v></c></row>'
        '</sheetData></worksheet>'
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
            f"{workbook_sheets}</sheets></workbook>",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{relationships}</Relationships>",
        )
        archive.writestr(
            "xl/sharedStrings.xml",
            '<?xml version="1.0"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<si><t>external_id</t></si><si><t>amount</t></si><si><t>shared-value</t></si></sst>',
        )
        for index in range(1, sheet_count + 1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", sheet)
    return buffer.getvalue()


def test_structured_csv_json_and_xlsx_extraction_is_deterministic():
    csv_records = extract_structured_records(
        b"external_id,name\n1,Alice\n2,Bob\n", filename="batch.csv",
        schema_kind="TABULAR", max_uncompressed_bytes=1024 * 1024,
    )
    assert [(item.ordinal, item.locator, item.values) for item in csv_records] == [
        (1, "csv:row:1", {"external_id": "1", "name": "Alice"}),
        (2, "csv:row:2", {"external_id": "2", "name": "Bob"}),
    ]
    with pytest.raises(IngestionError, match="record_materialization_duplicate_headers"):
        extract_structured_records(
            b"id,id\n1,2\n", filename="duplicate.csv", schema_kind="TABULAR",
            max_uncompressed_bytes=1024,
        )
    tabular = extract_structured_records(
        b'[{"external_id":"1"},{"external_id":"2"}]', filename="batch.json",
        schema_kind="TABULAR", max_uncompressed_bytes=1024,
    )
    assert [item.locator for item in tabular] == ["json:index:0", "json:index:1"]
    record = extract_structured_records(
        b'{"external_id":"1"}', filename="record.json", schema_kind="RECORD",
        max_uncompressed_bytes=1024,
    )
    assert record[0].locator == "json:record:1"
    for raw, kind in ((b'{"id":1}', "TABULAR"), (b'[1]', "TABULAR"), (b'[{}]', "RECORD")):
        with pytest.raises(IngestionError, match="record_materialization_json_shape_invalid"):
            extract_structured_records(raw, filename="bad.json", schema_kind=kind, max_uncompressed_bytes=1024)
    xlsx = extract_structured_records(
        _xlsx_payload(), filename="batch.xlsx", schema_kind="TABULAR",
        max_uncompressed_bytes=1024 * 1024,
    )
    assert xlsx == (
        StructuredRecord(1, "xlsx:row:1", {"external_id": "shared-value", "amount": "42"}),
    )
    with pytest.raises(IngestionError, match="record_materialization_xlsx_multiple_sheets_unsupported"):
        extract_structured_records(
            _xlsx_payload(sheet_count=2), filename="multi.xlsx", schema_kind="TABULAR",
            max_uncompressed_bytes=1024 * 1024,
        )
    with pytest.raises(IngestionError, match="record_materialization_xlsx_formula_unsupported"):
        extract_structured_records(
            _xlsx_payload(formula=True), filename="formula.xlsx", schema_kind="TABULAR",
            max_uncompressed_bytes=1024 * 1024,
        )


def test_type_normalization_exact_deduplication_and_identity_conflict(tmp_path):
    schema = [
        {"ordinal": 1, "source_field": "id", "logical_type": "STRING", "required": True, "nullable": False, "missing_values": []},
        {"ordinal": 2, "source_field": "integer", "logical_type": "INTEGER", "required": True, "nullable": False, "missing_values": []},
        {"ordinal": 3, "source_field": "number", "logical_type": "NUMBER", "required": True, "nullable": False, "missing_values": []},
        {"ordinal": 4, "source_field": "boolean", "logical_type": "BOOLEAN", "required": True, "nullable": False, "missing_values": []},
        {"ordinal": 5, "source_field": "date", "logical_type": "DATE", "required": True, "nullable": False, "missing_values": []},
        {"ordinal": 6, "source_field": "datetime", "logical_type": "DATETIME", "required": True, "nullable": False, "missing_values": []},
        {"ordinal": 7, "source_field": "json", "logical_type": "JSON", "required": True, "nullable": False, "missing_values": []},
    ]
    case = _build_case(tmp_path, schema=schema)
    _create_and_activate_policy(case, identity_field_keys=["record.id"])
    run = _create_run(case, b"synthetic", filename="batch.csv", key="types")
    values = {
        "id": "A",
        "integer": "+0012",
        "number": "001.2300",
        "boolean": "TrUe",
        "date": "2026-09-13",
        "datetime": "2026-09-13T10:11:12+02:00",
        "json": {"z": [1, True], "a": {"b": None}},
    }
    records = (
        StructuredRecord(1, "synthetic:1", values),
        StructuredRecord(2, "synthetic:2", dict(values)),
        StructuredRecord(3, "synthetic:3", values | {"number": "2.5"}),
    )
    result = materialize_ingestion_run_records(case["db"], run=run, records=records)
    assert result == (type(result))(3, 1, 1, 1)
    rows = case["db"].scalars(
        select(DataNormalizedRecord).where(DataNormalizedRecord.ingestion_run_id == run.id)
        .order_by(DataNormalizedRecord.source_record_ordinal)
    ).all()
    normalized = json.loads(rows[0].normalized_record_json)
    assert normalized == {
        "record.id": "A", "record.integer": 12, "record.number": "1.23",
        "record.boolean": True, "record.date": "2026-09-13",
        "record.datetime": "2026-09-13T10:11:12+02:00",
        "record.json": {"a": {"b": None}, "z": [1, True]},
    }
    assert rows[1].duplicate_of_record_id == rows[0].id
    assert rows[2].quarantine_reason == "IDENTITY_CONTENT_CONFLICT"
    assert rows[2].conflict_with_record_id == rows[0].id
    assert case["db"].get(DataRecordEntity, rows[0].entity_id).state == "QUARANTINED"


def test_number_normalization_is_exact_context_independent_and_bounded(tmp_path):
    schema = [
        {"ordinal": 1, "source_field": "id", "logical_type": "STRING", "required": True, "nullable": False, "missing_values": []},
        {"ordinal": 2, "source_field": "number", "logical_type": "NUMBER", "required": True, "nullable": False, "missing_values": []},
    ]
    case = _build_case(tmp_path, schema=schema)
    _create_and_activate_policy(case, identity_field_keys=["record.id"])
    run = _create_run(case, b"synthetic", key="exact-number")
    first_large = "123456789012345678901234567890"
    second_large = "123456789012345678901234567891"
    records = (
        StructuredRecord(1, "number:ordinary", {"id": "ordinary", "number": "001.2300"}),
        StructuredRecord(2, "number:large:1", {"id": "large", "number": first_large}),
        StructuredRecord(3, "number:large:2", {"id": "large", "number": second_large}),
        StructuredRecord(4, "number:positive-extreme", {"id": "positive", "number": "1e1000000"}),
        StructuredRecord(5, "number:negative-extreme", {"id": "negative", "number": "1e-10000000"}),
        StructuredRecord(6, "number:at-bound", {"id": "at-bound", "number": "1e4095"}),
        StructuredRecord(7, "number:over-bound", {"id": "over-bound", "number": "1e4096"}),
    )

    with localcontext() as context:
        context.prec = 3
        context.Emin = -9
        context.Emax = 9
        result = materialize_ingestion_run_records(case["db"], run=run, records=records)

    assert result == (type(result))(7, 3, 0, 4)
    rows = case["db"].scalars(
        select(DataNormalizedRecord).where(DataNormalizedRecord.ingestion_run_id == run.id)
        .order_by(DataNormalizedRecord.source_record_ordinal)
    ).all()
    normalized = [json.loads(row.normalized_record_json) for row in rows]
    assert normalized[0]["record.number"] == "1.23"
    assert normalized[1]["record.number"] == first_large
    assert normalized[2]["record.number"] == second_large
    assert normalized[1]["record.number"] != normalized[2]["record.number"]
    assert rows[1].content_fingerprint != rows[2].content_fingerprint
    assert rows[2].quarantine_reason == "IDENTITY_CONTENT_CONFLICT"
    for row in (rows[3], rows[4], rows[6]):
        assert row.disposition == "QUARANTINED"
        assert row.quarantine_reason == "TYPE_NORMALIZATION_FAILED"
    assert normalized[3]["record.number"] is None
    assert normalized[4]["record.number"] is None
    assert len(normalized[5]["record.number"]) == 4096
    assert normalized[5]["record.number"] == "1" + "0" * 4095
    assert normalized[6]["record.number"] is None


def test_missing_required_identity_type_unexpected_and_unresolved_quarantine(tmp_path):
    schema = [
        {"ordinal": 1, "source_field": "id", "logical_type": "STRING", "required": True, "nullable": False, "missing_values": ["NA"]},
        {"ordinal": 2, "source_field": "required", "logical_type": "STRING", "required": True, "nullable": False, "missing_values": [""]},
        {"ordinal": 3, "source_field": "amount", "logical_type": "NUMBER", "required": False, "nullable": True, "missing_values": []},
    ]
    case = _build_case(tmp_path, schema=schema)
    _create_and_activate_policy(case, identity_field_keys=["record.id"])
    run = _create_run(case, b"synthetic", key="quarantine")
    records = (
        StructuredRecord(1, "q:1", {"id": "NA", "required": "yes", "amount": "1"}),
        StructuredRecord(2, "q:2", {"id": "B", "required": "", "amount": "1"}),
        StructuredRecord(3, "q:3", {"id": "C", "required": "yes", "amount": "bad"}),
        StructuredRecord(4, "q:4", {"id": "D", "required": "yes", "amount": "1", "extra": "hidden"}),
        StructuredRecord(5, "q:5", {"id": "C", "required": "yes", "amount": "2"}),
    )
    result = materialize_ingestion_run_records(case["db"], run=run, records=records)
    assert result.quarantined == 5
    reasons = [
        row.quarantine_reason
        for row in case["db"].scalars(
            select(DataNormalizedRecord).where(DataNormalizedRecord.ingestion_run_id == run.id)
            .order_by(DataNormalizedRecord.source_record_ordinal)
        )
    ]
    assert reasons == [
        "MISSING_IDENTITY", "REQUIRED_FIELD_MISSING", "TYPE_NORMALIZATION_FAILED",
        "UNEXPECTED_FIELD", "ENTITY_UNRESOLVED",
    ]


def test_accept_incoming_keeps_entity_quarantined_until_sibling_is_resolved(tmp_path):
    schema = [
        {"ordinal": 1, "source_field": "id", "logical_type": "STRING", "required": True, "nullable": False, "missing_values": []},
        {"ordinal": 2, "source_field": "amount", "logical_type": "NUMBER", "required": True, "nullable": False, "missing_values": []},
    ]
    case = _build_case(tmp_path, schema=schema)
    _create_and_activate_policy(case, identity_field_keys=["record.id"])
    run = _create_run(case, b"synthetic", key="sibling-resolution")
    materialize_ingestion_run_records(
        case["db"],
        run=run,
        records=(
            StructuredRecord(1, "sibling:invalid", {"id": "C", "amount": "invalid"}),
            StructuredRecord(2, "sibling:acceptable", {"id": "C", "amount": "2"}),
        ),
    )
    rows = case["db"].scalars(
        select(DataNormalizedRecord).where(DataNormalizedRecord.ingestion_run_id == run.id)
        .order_by(DataNormalizedRecord.source_record_ordinal)
    ).all()
    invalid, acceptable = rows
    assert invalid.quarantine_reason == "TYPE_NORMALIZATION_FAILED"
    assert acceptable.quarantine_reason == "ENTITY_UNRESOLVED"

    accepted = resolve_quarantined_record(
        case["db"], source_id=case["source"].id, record_id=acceptable.id,
        payload=RecordResolutionCreate(
            organization_id=case["organization"].id, workspace_id=case["workspace"].id,
            product_code="SIMPA", decision="ACCEPT_INCOMING",
            resolution_reference="case:accept-sibling",
        ), actor_id=case["membership"].id,
    )

    assert accepted.decision == "ACCEPT_INCOMING"
    assert acceptable.disposition == "ACCEPTED"
    assert invalid.disposition == "QUARANTINED"
    entity = case["db"].get(DataRecordEntity, acceptable.entity_id)
    assert entity.state == "QUARANTINED"

    rejected = resolve_quarantined_record(
        case["db"], source_id=case["source"].id, record_id=invalid.id,
        payload=RecordResolutionCreate(
            organization_id=case["organization"].id, workspace_id=case["workspace"].id,
            product_code="SIMPA", decision="REJECT_INCOMING",
            resolution_reference="case:reject-sibling",
        ), actor_id=case["membership"].id,
    )

    assert rejected.decision == "REJECT_INCOMING"
    assert invalid.disposition == "REJECTED"
    assert acceptable.disposition == "ACCEPTED"
    assert entity.state == "ACTIVE"


def test_complete_rematerialization_is_idempotent_and_partial_state_fails(tmp_path):
    case = _build_case(tmp_path / "complete")
    _create_and_activate_policy(case)
    run = _create_run(case, b"synthetic", key="complete")
    records = (
        StructuredRecord(1, "r:1", {"external_id": "1", "name": "Alice"}),
        StructuredRecord(2, "r:2", {"external_id": "2", "name": "Bob"}),
    )
    first = materialize_ingestion_run_records(case["db"], run=run, records=records)
    second = materialize_ingestion_run_records(case["db"], run=run, records=records)
    assert first == second
    assert case["db"].scalar(select(func.count()).select_from(DataNormalizedRecord)) == 2

    partial = _build_case(tmp_path / "partial")
    _create_and_activate_policy(partial)
    partial_run = _create_run(partial, b"synthetic", key="partial")
    materialize_ingestion_run_records(partial["db"], run=partial_run, records=records[:1])
    with pytest.raises(DataPlatformError, match="record_materialization_partial_integrity_failed"):
        materialize_ingestion_run_records(partial["db"], run=partial_run, records=records)


def test_quarantine_metadata_detail_resolution_and_audit_privacy(tmp_path):
    case = _build_case(tmp_path)
    _create_and_activate_policy(case)
    run = _create_run(case, b"synthetic", key="resolution")
    records = (
        StructuredRecord(1, "r:1", {"external_id": "1", "name": "private-Alice"}),
        StructuredRecord(2, "r:2", {"external_id": "1", "name": "private-Bob"}),
        StructuredRecord(3, "r:3", {"external_id": "NA", "name": "private-missing"}),
    )
    materialize_ingestion_run_records(case["db"], run=run, records=records)
    quarantined = list_record_quarantine(
        case["db"], source_id=case["source"].id,
        organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code="SIMPA",
    )
    assert len(quarantined) == 2
    assert "normalized_record" not in quarantined[0].model_dump()
    conflict = next(item for item in quarantined if item.quarantine_reason == "IDENTITY_CONTENT_CONFLICT")
    missing = next(item for item in quarantined if item.quarantine_reason == "MISSING_IDENTITY")
    detail = get_record_quarantine_detail(
        case["db"], source_id=case["source"].id, record_id=conflict.id,
        organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code="SIMPA",
    )
    assert detail.normalized_record["record.name"] == "private-Bob"
    assert detail.current_accepted_record["record.name"] == "private-Alice"
    accepted = resolve_quarantined_record(
        case["db"], source_id=case["source"].id, record_id=conflict.id,
        payload=RecordResolutionCreate(
            organization_id=case["organization"].id, workspace_id=case["workspace"].id,
            product_code="SIMPA", decision="ACCEPT_INCOMING",
            resolution_reference="case:accept", reason="reviewed",
        ), actor_id=case["membership"].id,
    )
    assert accepted.decision == "ACCEPT_INCOMING"
    prior = case["db"].get(DataNormalizedRecord, detail.current_accepted_record_id)
    incoming = case["db"].get(DataNormalizedRecord, conflict.id)
    assert (prior.disposition, incoming.disposition) == ("SUPERSEDED", "ACCEPTED")
    with pytest.raises(DataPlatformError, match="record_resolution_accept_forbidden"):
        resolve_quarantined_record(
            case["db"], source_id=case["source"].id, record_id=missing.id,
            payload=RecordResolutionCreate(
                organization_id=case["organization"].id, workspace_id=case["workspace"].id,
                product_code="SIMPA", decision="ACCEPT_INCOMING",
                resolution_reference="case:invalid",
            ), actor_id=case["membership"].id,
        )
    rejected = resolve_quarantined_record(
        case["db"], source_id=case["source"].id, record_id=missing.id,
        payload=RecordResolutionCreate(
            organization_id=case["organization"].id, workspace_id=case["workspace"].id,
            product_code="SIMPA", decision="REJECT_INCOMING",
            resolution_reference="case:reject",
        ), actor_id=case["membership"].id,
    )
    assert rejected.decision == "REJECT_INCOMING"
    assert case["db"].get(DataNormalizedRecord, missing.id).disposition == "REJECTED"
    assert case["db"].scalar(select(func.count()).select_from(DataRecordResolution)) == 2
    audits = "\n".join(case["db"].scalars(select(DataAuditEvent.detail)).all())
    for raw_value in ("private-Alice", "private-Bob", "private-missing"):
        assert raw_value not in audits


def test_worker_materializes_quality_warns_without_failing_and_structural_failure_rolls_back(tmp_path, monkeypatch):
    case = _build_case(tmp_path / "quality")
    _create_and_activate_policy(case)
    raw = b"external_id,name\n1,Alice\n1,Alice\n1,Bob\n"
    run = _create_run(case, raw, key="quality")
    monkeypatch.setattr(data_jobs, "build_storage", lambda: case["storage"])
    monkeypatch.setattr(
        data_jobs, "get_settings",
        lambda: SimpleNamespace(data_max_xlsx_uncompressed_bytes=1024 * 1024),
    )
    data_jobs.process_ingestion_job(case["db"], job_id=run.inspection_job_id)
    assert run.status == "SUCCEEDED"
    quality = {
        item.check_code: (item.status, item.metric_value)
        for item in case["db"].scalars(
            select(DataQualityResult).where(DataQualityResult.version_id == run.source_version_id)
        )
    }
    assert quality["records.materialized"] == ("pass", "3")
    assert quality["records.accepted"] == ("pass", "1")
    assert quality["records.duplicates"] == ("pass", "1")
    assert quality["records.quarantined"] == ("warn", "1")

    structural = _build_case(tmp_path / "structural")
    _create_and_activate_policy(structural)
    bad_run = _create_run(structural, b'{"external_id":"1"}', filename="bad.json", key="bad")
    monkeypatch.setattr(data_jobs, "build_storage", lambda: structural["storage"])
    data_jobs.process_ingestion_job(structural["db"], job_id=bad_run.inspection_job_id)
    assert bad_run.status == "FAILED"
    assert bad_run.error_code == "record_materialization_json_shape_invalid"
    assert structural["db"].scalar(select(func.count()).select_from(DataNormalizedRecord)) == 0


def test_schemas_routes_permissions_and_controlled_error_mappings():
    scope = {
        "organization_id": uuid.uuid4(),
        "workspace_id": uuid.uuid4(),
        "product_code": "SIMPA",
    }
    with pytest.raises(ValidationError):
        RecordResolutionCreate(
            **scope, decision="ACCEPT_INCOMING", resolution_reference="   "
        )
    with pytest.raises(ValidationError):
        RecordGovernancePolicyActivationRequest(**scope, unexpected=True)
    route_methods = {
        (route.path, method)
        for route in data_routes.router.routes
        for method in getattr(route, "methods", set())
    }
    expected = {
        ("/api/v1/data/sources/{source_id}/record-policies/versions", "POST"),
        ("/api/v1/data/sources/{source_id}/record-policies", "GET"),
        ("/api/v1/data/sources/{source_id}/record-policies/{policy_id}/activate", "POST"),
        ("/api/v1/data/sources/{source_id}/record-quarantine", "GET"),
        ("/api/v1/data/sources/{source_id}/record-quarantine/{record_id}", "GET"),
        ("/api/v1/data/sources/{source_id}/record-quarantine/{record_id}/resolve", "POST"),
    }
    assert expected <= route_methods
    expectations = (
        (data_routes.post_record_governance_policy_version, "data.governance.manage"),
        (data_routes.get_record_governance_policy_versions, "data.read"),
        (data_routes.post_record_governance_policy_activation, "data.governance.manage"),
        (data_routes.get_record_quarantine, "data.governance.manage"),
        (data_routes.get_record_quarantine_detail, "data.governance.manage"),
        (data_routes.post_record_quarantine_resolution, "data.governance.manage"),
    )
    for function, permission in expectations:
        source = inspect.getsource(function)
        assert f'permission_code="{permission}"' in source
    for code in ("record_policy_version_not_accessible", "record_quarantine_not_accessible"):
        assert data_routes._platform_error(DataPlatformError(code)).status_code == 404
    for code in (
        "record_policy_state_conflict", "record_policy_unchanged",
        "record_policy_binding_mismatch", "record_resolution_state_conflict",
        "record_resolution_accept_forbidden",
    ):
        assert data_routes._platform_error(DataPlatformError(code)).status_code == 409
    service_source = inspect.getsource(
        __import__("src.platform.data.record_governance_service", fromlist=["*"])
    )
    parser_source = inspect.getsource(
        __import__("src.platform.data.ingestion", fromlist=["extract_structured_records"])
    )
    for forbidden in (
        "requests", "httpx", "boto3", "socket", "subprocess", "eval(", "exec(",
        "openai", "pickle", "jinja",
    ):
        assert forbidden not in service_source.casefold()
        assert forbidden not in parser_source.casefold()
