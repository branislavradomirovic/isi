import io
import json
import zipfile

import pytest

from src.platform.data.ingestion import IngestionError, inspect_payload


def _xlsx_bytes() -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="Podaci" sheetId="1" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/></sheets></workbook>',
        )
        zf.writestr(
            "xl/worksheets/sheet1.xml",
            '<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1"/><c r="B1"/></row><row r="2"><c r="A2"/><c r="B2"/></row></sheetData></worksheet>',
        )
    return out.getvalue()


def test_csv_profile_is_structured():
    profile = inspect_payload(b"opstina,vrednost\nNovi Sad,10\nNis,12\n", filename="data.csv", max_uncompressed_bytes=1024 * 1024)
    assert profile.detected_format == "csv"
    assert profile.row_count == 2
    assert profile.column_count == 2
    assert len(profile.schema_fingerprint) == 64


def test_json_profile_is_structured():
    payload = json.dumps([{"opstina": "A", "vrednost": 1}, {"opstina": "B", "vrednost": 2}]).encode()
    profile = inspect_payload(payload, filename="data.json", max_uncompressed_bytes=1024 * 1024)
    assert profile.detected_format == "json"
    assert profile.row_count == 2
    assert profile.column_count == 2


def test_xlsx_profile_uses_zip_xml_without_extra_dependency():
    profile = inspect_payload(_xlsx_bytes(), filename="data.xlsx", max_uncompressed_bytes=1024 * 1024)
    assert profile.detected_format == "xlsx"
    assert profile.sheet_count == 1
    assert profile.row_count == 1
    assert profile.column_count == 2


def test_document_registration_does_not_claim_semantic_extraction():
    profile = inspect_payload(b"%PDF-1.4 fake but non-empty", filename="report.pdf", max_uncompressed_bytes=1024 * 1024)
    assert profile.detected_format == "pdf"
    assert profile.row_count is None
    assert any(item.code == "document.registered" for item in profile.quality)


def test_unsupported_format_rejected():
    with pytest.raises(IngestionError, match="unsupported_format"):
        inspect_payload(b"abc", filename="legacy.xls", max_uncompressed_bytes=1024 * 1024)
