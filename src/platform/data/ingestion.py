from __future__ import annotations

import csv
import hashlib
import io
import json
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
