from __future__ import annotations

import csv
import hashlib
import io
import json
import posixpath
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree


class IngestionError(ValueError):
    pass


@dataclass(frozen=True)
class QualityCheck:
    code: str
    status: str
    message: str
    metric_name: str = ""
    metric_value: str = ""


@dataclass(frozen=True)
class IngestionProfile:
    detected_format: str
    row_count: int | None
    column_count: int | None
    sheet_count: int | None
    schema_fingerprint: str
    quality: tuple[QualityCheck, ...]


@dataclass(frozen=True)
class StructuredRecord:
    ordinal: int
    locator: str
    values: dict[str, object]


def normalized_extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def _fingerprint(fields: list[str]) -> str:
    normalized = "\n".join(field.strip().casefold() for field in fields)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest() if normalized else ""


def _decode_text(payload: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1250", "latin-1"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise IngestionError("text_encoding_not_supported")


def _inspect_csv(payload: bytes) -> IngestionProfile:
    text = _decode_text(payload)
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(text), dialect)
    rows = list(reader)
    if not rows:
        return IngestionProfile(
            "csv", 0, 0, None, "",
            (
                QualityCheck("file.non_empty", "pass", "Upload contains bytes."),
                QualityCheck("table.rows", "warn", "CSV contains no rows.", "row_count", "0"),
            ),
        )
    header = [str(value).strip() for value in rows[0]]
    data_rows = max(len(rows) - 1, 0)
    width = max((len(row) for row in rows), default=len(header))
    quality = [
        QualityCheck("file.non_empty", "pass", "Upload contains bytes."),
        QualityCheck("format.parseable", "pass", "CSV parsed successfully."),
        QualityCheck("table.rows", "pass" if data_rows > 0 else "warn", f"CSV data rows: {data_rows}.", "row_count", str(data_rows)),
        QualityCheck("table.columns", "pass" if width > 0 else "warn", f"CSV columns: {width}.", "column_count", str(width)),
    ]
    if header and len(set(header)) != len(header):
        quality.append(QualityCheck("schema.unique_headers", "warn", "CSV header contains duplicate column names."))
    return IngestionProfile("csv", data_rows, width, None, _fingerprint(header), tuple(quality))


def _inspect_json(payload: bytes) -> IngestionProfile:
    text = _decode_text(payload)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise IngestionError("json_invalid") from exc
    fields: list[str] = []
    if isinstance(value, list):
        rows = len(value)
        for item in value[:100]:
            if isinstance(item, dict):
                fields.extend(str(key) for key in item.keys())
        fields = sorted(set(fields))
        columns = len(fields) if fields else None
    elif isinstance(value, dict):
        rows = 1
        fields = sorted(str(key) for key in value.keys())
        columns = len(fields)
    else:
        rows = 1
        columns = 1
    return IngestionProfile(
        "json",
        rows,
        columns,
        None,
        _fingerprint(fields),
        (
            QualityCheck("file.non_empty", "pass", "Upload contains bytes."),
            QualityCheck("format.parseable", "pass", "JSON parsed successfully."),
            QualityCheck("json.records", "pass", f"JSON records: {rows}.", "row_count", str(rows)),
        ),
    )


def _xlsx_guard(zf: zipfile.ZipFile, max_uncompressed_bytes: int) -> None:
    total = 0
    for info in zf.infolist():
        if info.file_size > max_uncompressed_bytes:
            raise IngestionError("xlsx_member_too_large")
        total += info.file_size
        if total > max_uncompressed_bytes:
            raise IngestionError("xlsx_uncompressed_limit_exceeded")


def _inspect_xlsx(payload: bytes, max_uncompressed_bytes: int) -> IngestionProfile:
    try:
        zf = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile as exc:
        raise IngestionError("xlsx_invalid_zip") from exc
    with zf:
        _xlsx_guard(zf, max_uncompressed_bytes)
        names = set(zf.namelist())
        if "xl/workbook.xml" not in names:
            raise IngestionError("xlsx_workbook_missing")
        workbook = ElementTree.fromstring(zf.read("xl/workbook.xml"))
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        sheets = workbook.findall(".//m:sheet", ns)
        sheet_count = len(sheets)
        row_count: int | None = None
        column_count: int | None = None
        if "xl/worksheets/sheet1.xml" in names:
            root = ElementTree.fromstring(zf.read("xl/worksheets/sheet1.xml"))
            rows = root.findall(".//m:row", ns)
            row_count = max(len(rows) - 1, 0) if rows else 0
            first = rows[0] if rows else None
            column_count = len(first.findall("m:c", ns)) if first is not None else 0
        sheet_names = [sheet.attrib.get("name", "") for sheet in sheets]
        return IngestionProfile(
            "xlsx",
            row_count,
            column_count,
            sheet_count,
            _fingerprint(sheet_names),
            (
                QualityCheck("file.non_empty", "pass", "Upload contains bytes."),
                QualityCheck("format.parseable", "pass", "XLSX package structure parsed successfully."),
                QualityCheck("xlsx.sheets", "pass" if sheet_count else "warn", f"Workbook sheets: {sheet_count}.", "sheet_count", str(sheet_count)),
            ),
        )


def _inspect_txt(payload: bytes) -> IngestionProfile:
    text = _decode_text(payload)
    lines = text.splitlines()
    return IngestionProfile(
        "txt", len(lines), 1 if lines else 0, None, "",
        (
            QualityCheck("file.non_empty", "pass", "Upload contains bytes."),
            QualityCheck("format.parseable", "pass", "Text decoded successfully."),
            QualityCheck("text.lines", "pass" if lines else "warn", f"Text lines: {len(lines)}.", "line_count", str(len(lines))),
        ),
    )


def _validated_headers(values: list[object], *, format_name: str) -> list[str]:
    headers = ["" if value is None else str(value).strip() for value in values]
    if not headers or any(not header for header in headers):
        raise IngestionError(f"record_materialization_{format_name}_header_invalid")
    if len(set(headers)) != len(headers):
        raise IngestionError("record_materialization_duplicate_headers")
    return headers


def _extract_csv_records(payload: bytes) -> tuple[StructuredRecord, ...]:
    text = _decode_text(payload)
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    try:
        rows = list(csv.reader(io.StringIO(text), dialect))
    except csv.Error as exc:
        raise IngestionError("record_materialization_csv_invalid") from exc
    if not rows:
        raise IngestionError("record_materialization_csv_header_missing")
    headers = _validated_headers(list(rows[0]), format_name="csv")
    records: list[StructuredRecord] = []
    for ordinal, row in enumerate(rows[1:], start=1):
        if len(row) > len(headers) and any(value != "" for value in row[len(headers):]):
            raise IngestionError("record_materialization_csv_row_width_invalid")
        values = {
            header: row[index] if index < len(row) else None
            for index, header in enumerate(headers)
        }
        records.append(StructuredRecord(ordinal, f"csv:row:{ordinal}", values))
    return tuple(records)


def _reject_json_constant(_value: str) -> object:
    raise ValueError("non-finite JSON number")


def _json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _extract_json_records(payload: bytes, *, schema_kind: str) -> tuple[StructuredRecord, ...]:
    try:
        value = json.loads(
            _decode_text(payload),
            object_pairs_hook=_json_object,
            parse_constant=_reject_json_constant,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise IngestionError("record_materialization_json_invalid") from exc
    if schema_kind == "TABULAR":
        if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
            raise IngestionError("record_materialization_json_shape_invalid")
        return tuple(
            StructuredRecord(index + 1, f"json:index:{index}", dict(item))
            for index, item in enumerate(value)
        )
    if schema_kind == "RECORD":
        if not isinstance(value, dict):
            raise IngestionError("record_materialization_json_shape_invalid")
        return (StructuredRecord(1, "json:record:1", dict(value)),)
    raise IngestionError("record_materialization_schema_kind_invalid")


_CELL_REFERENCE = re.compile(r"^([A-Z]+)[0-9]+$")
_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def _xlsx_column_index(reference: str) -> int:
    match = _CELL_REFERENCE.fullmatch(reference.upper())
    if match is None:
        raise IngestionError("record_materialization_xlsx_cell_reference_invalid")
    result = 0
    for character in match.group(1):
        result = result * 26 + ord(character) - ord("A") + 1
    return result - 1


def _xlsx_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in set(zf.namelist()):
        return []
    try:
        root = ElementTree.fromstring(zf.read("xl/sharedStrings.xml"))
    except ElementTree.ParseError as exc:
        raise IngestionError("record_materialization_xlsx_invalid") from exc
    return [
        "".join(node.text or "" for node in item.findall(f".//{{{_MAIN_NS}}}t"))
        for item in root.findall(f"{{{_MAIN_NS}}}si")
    ]


def _xlsx_worksheet_path(zf: zipfile.ZipFile, workbook: ElementTree.Element) -> str:
    sheets = workbook.findall(f".//{{{_MAIN_NS}}}sheet")
    if len(sheets) != 1:
        raise IngestionError("record_materialization_xlsx_multiple_sheets_unsupported")
    relationship_id = sheets[0].attrib.get(f"{{{_OFFICE_REL_NS}}}id")
    if not relationship_id or "xl/_rels/workbook.xml.rels" not in set(zf.namelist()):
        raise IngestionError("record_materialization_xlsx_worksheet_missing")
    try:
        relationships = ElementTree.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    except ElementTree.ParseError as exc:
        raise IngestionError("record_materialization_xlsx_invalid") from exc
    target = None
    for relationship in relationships.findall(f"{{{_PACKAGE_REL_NS}}}Relationship"):
        if relationship.attrib.get("Id") == relationship_id:
            target = relationship.attrib.get("Target")
            break
    if not target:
        raise IngestionError("record_materialization_xlsx_worksheet_missing")
    path = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join("xl", target))
    if path not in set(zf.namelist()) or not path.startswith("xl/worksheets/"):
        raise IngestionError("record_materialization_xlsx_worksheet_missing")
    return path


def _xlsx_cell_value(cell: ElementTree.Element, shared_strings: list[str]) -> object:
    if cell.find(f"{{{_MAIN_NS}}}f") is not None:
        raise IngestionError("record_materialization_xlsx_formula_unsupported")
    cell_type = cell.attrib.get("t", "n")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(f".//{{{_MAIN_NS}}}t"))
    value_node = cell.find(f"{{{_MAIN_NS}}}v")
    if value_node is None:
        return None
    value = value_node.text or ""
    if cell_type == "s":
        try:
            return shared_strings[int(value)]
        except (ValueError, IndexError) as exc:
            raise IngestionError("record_materialization_xlsx_shared_string_invalid") from exc
    if cell_type == "b":
        if value not in {"0", "1"}:
            raise IngestionError("record_materialization_xlsx_boolean_invalid")
        return value == "1"
    if cell_type in {"n", "str", "d"}:
        return value
    if cell_type == "e":
        raise IngestionError("record_materialization_xlsx_cell_error_unsupported")
    raise IngestionError("record_materialization_xlsx_cell_type_unsupported")


def _extract_xlsx_records(payload: bytes, *, max_uncompressed_bytes: int) -> tuple[StructuredRecord, ...]:
    try:
        zf = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile as exc:
        raise IngestionError("xlsx_invalid_zip") from exc
    with zf:
        _xlsx_guard(zf, max_uncompressed_bytes)
        if "xl/workbook.xml" not in set(zf.namelist()):
            raise IngestionError("xlsx_workbook_missing")
        try:
            workbook = ElementTree.fromstring(zf.read("xl/workbook.xml"))
            worksheet_path = _xlsx_worksheet_path(zf, workbook)
            worksheet = ElementTree.fromstring(zf.read(worksheet_path))
        except ElementTree.ParseError as exc:
            raise IngestionError("record_materialization_xlsx_invalid") from exc
        shared_strings = _xlsx_shared_strings(zf)
        rows = worksheet.findall(f".//{{{_MAIN_NS}}}row")
        if not rows:
            raise IngestionError("record_materialization_xlsx_header_missing")
        parsed_rows: list[dict[int, object]] = []
        for row in rows:
            parsed: dict[int, object] = {}
            next_index = 0
            for cell in row.findall(f"{{{_MAIN_NS}}}c"):
                reference = cell.attrib.get("r")
                index = _xlsx_column_index(reference) if reference else next_index
                parsed[index] = _xlsx_cell_value(cell, shared_strings)
                next_index = index + 1
            parsed_rows.append(parsed)
        header_row = parsed_rows[0]
        width = max(header_row, default=-1) + 1
        headers = _validated_headers(
            [header_row.get(index) for index in range(width)],
            format_name="xlsx",
        )
        records: list[StructuredRecord] = []
        for ordinal, row in enumerate(parsed_rows[1:], start=1):
            if any(index >= len(headers) and value is not None for index, value in row.items()):
                raise IngestionError("record_materialization_xlsx_row_width_invalid")
            values = {header: row.get(index) for index, header in enumerate(headers)}
            records.append(StructuredRecord(ordinal, f"xlsx:row:{ordinal}", values))
        return tuple(records)


def extract_structured_records(
    payload: bytes,
    *,
    filename: str,
    schema_kind: str,
    max_uncompressed_bytes: int,
) -> tuple[StructuredRecord, ...]:
    if not payload:
        raise IngestionError("empty_payload")
    extension = normalized_extension(filename)
    if extension == "csv":
        if schema_kind != "TABULAR":
            raise IngestionError("record_materialization_schema_kind_mismatch")
        return _extract_csv_records(payload)
    if extension == "json":
        return _extract_json_records(payload, schema_kind=schema_kind)
    if extension == "xlsx":
        if schema_kind != "TABULAR":
            raise IngestionError("record_materialization_schema_kind_mismatch")
        return _extract_xlsx_records(payload, max_uncompressed_bytes=max_uncompressed_bytes)
    raise IngestionError("record_materialization_format_unsupported")


def inspect_payload(payload: bytes, *, filename: str, max_uncompressed_bytes: int) -> IngestionProfile:
    if not payload:
        raise IngestionError("empty_payload")
    ext = normalized_extension(filename)
    if ext == "csv":
        return _inspect_csv(payload)
    if ext == "json":
        return _inspect_json(payload)
    if ext == "xlsx":
        return _inspect_xlsx(payload, max_uncompressed_bytes=max_uncompressed_bytes)
    if ext == "txt":
        return _inspect_txt(payload)
    if ext in {"pdf", "docx"}:
        return IngestionProfile(
            ext, None, None, None, "",
            (
                QualityCheck("file.non_empty", "pass", "Upload contains bytes."),
                QualityCheck("document.registered", "pass", f"{ext.upper()} registered for later semantic extraction."),
            ),
        )
    raise IngestionError("unsupported_format")
