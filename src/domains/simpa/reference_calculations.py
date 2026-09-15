from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any


REFERENCE_SUITE_SCHEMA_VERSION = "SIMPA-REFERENCE-SUITE-v1"


class ReferenceCalculationError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalize_direct_observation(
    value_numeric: object = None,
    value_text: object = None,
) -> dict[str, float | str | None]:
    has_numeric = value_numeric is not None
    if isinstance(value_numeric, bool):
        raise ReferenceCalculationError("direct_observation_numeric_invalid")
    numeric: float | None = None
    if has_numeric:
        try:
            numeric = float(value_numeric)
        except (TypeError, ValueError):
            raise ReferenceCalculationError("direct_observation_numeric_invalid") from None
        if not math.isfinite(numeric):
            raise ReferenceCalculationError("direct_observation_numeric_invalid")

    if value_text is not None and not isinstance(value_text, str):
        raise ReferenceCalculationError("direct_observation_text_invalid")
    text = value_text.strip() if isinstance(value_text, str) else ""
    has_text = bool(text)
    if not has_numeric and not has_text:
        raise ReferenceCalculationError("direct_observation_value_channel_invalid")
    return {"value_numeric": numeric, "value_text": text}


def normalize_direct_observation_expected(
    value_numeric: object = None,
    value_text: object = None,
) -> dict[str, float | str | None]:
    normalized = normalize_direct_observation(value_numeric, value_text)
    if normalized["value_numeric"] is not None and normalized["value_text"]:
        raise ReferenceCalculationError("direct_observation_expected_value_channel_invalid")
    return normalized


def calculate_direct_observation(
    reference_record: Mapping[str, Any],
    *,
    indicator_code: str,
) -> dict[str, float | str | None]:
    expected_indicator = indicator_code.strip()
    if not expected_indicator or reference_record.get("indicator_code") != expected_indicator:
        raise ReferenceCalculationError("reference_indicator_mismatch")
    if reference_record.get("quality_status") != "validated":
        raise ReferenceCalculationError("reference_quality_not_validated")
    return normalize_direct_observation(
        reference_record.get("value_numeric"),
        reference_record.get("value_text"),
    )


def compare_direct_observation(
    actual: Mapping[str, Any],
    expected: Mapping[str, Any],
    *,
    accepted_tolerance: float,
) -> dict[str, Any]:
    if isinstance(accepted_tolerance, bool):
        raise ReferenceCalculationError("accepted_tolerance_invalid")
    try:
        tolerance = float(accepted_tolerance)
    except (TypeError, ValueError):
        raise ReferenceCalculationError("accepted_tolerance_invalid") from None
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ReferenceCalculationError("accepted_tolerance_invalid")
    normalized_actual = normalize_direct_observation(actual.get("value_numeric"), actual.get("value_text"))
    normalized_expected = normalize_direct_observation_expected(
        expected.get("value_numeric"), expected.get("value_text")
    )
    if normalized_expected["value_numeric"] is not None:
        passed = (
            normalized_actual["value_numeric"] is not None
            and abs(float(normalized_actual["value_numeric"]) - float(normalized_expected["value_numeric"]))
            <= tolerance
        )
        comparison = "numeric_tolerance"
    else:
        passed = normalized_actual["value_text"] == normalized_expected["value_text"]
        comparison = "normalized_text_exact"
    return {
        "actual": normalized_actual,
        "expected": normalized_expected,
        "accepted_tolerance": tolerance,
        "comparison": comparison,
        "passed": passed,
    }


def reference_case_fingerprint(
    *,
    case_key: str,
    indicator_code: str,
    reference_record: Mapping[str, Any],
    expected_result: Mapping[str, Any],
) -> str:
    key = case_key.strip()
    if not key:
        raise ReferenceCalculationError("reference_case_key_required")
    record = dict(reference_record)
    actual = calculate_direct_observation(record, indicator_code=indicator_code)
    expected = normalize_direct_observation_expected(
        expected_result.get("value_numeric"), expected_result.get("value_text")
    )
    semantic = {
        "case_key": key,
        "indicator_code": indicator_code.strip(),
        "reference_record": {
            "indicator_code": indicator_code.strip(),
            "quality_status": "validated",
            **actual,
        },
        "expected_result": expected,
    }
    return canonical_fingerprint(semantic)


def reference_suite_fingerprint(
    *,
    methodology_contract_fingerprint: str,
    reference_dataset: str,
    reference_dataset_version: str,
    cases: Sequence[Mapping[str, Any]],
) -> str:
    contract_fingerprint = methodology_contract_fingerprint.strip()
    dataset = reference_dataset.strip()
    dataset_version = reference_dataset_version.strip()
    if len(contract_fingerprint) != 64:
        raise ReferenceCalculationError("methodology_contract_fingerprint_invalid")
    if not dataset or not dataset_version:
        raise ReferenceCalculationError("reference_dataset_identity_required")
    normalized_cases = [
        {
            "case_key": str(item.get("case_key", "")).strip(),
            "case_fingerprint": str(item.get("case_fingerprint", "")),
        }
        for item in cases
    ]
    case_keys = [item["case_key"] for item in normalized_cases]
    if not case_keys or any(not key for key in case_keys) or len(case_keys) != len(set(case_keys)):
        raise ReferenceCalculationError("reference_case_keys_invalid")
    ordered = sorted(normalized_cases, key=lambda item: item["case_key"])
    fingerprints = [item["case_fingerprint"] for item in ordered]
    if any(len(value) != 64 for value in fingerprints):
        raise ReferenceCalculationError("reference_case_fingerprint_invalid")
    return canonical_fingerprint(
        {
            "schema_version": REFERENCE_SUITE_SCHEMA_VERSION,
            "methodology_contract_fingerprint": contract_fingerprint,
            "reference_dataset": dataset,
            "reference_dataset_version": dataset_version,
            "cases": [{"case_key": item["case_key"], "case_fingerprint": item["case_fingerprint"]} for item in ordered],
        }
    )


def reference_case_result_fingerprint(detail: Mapping[str, Any]) -> str:
    return canonical_fingerprint(dict(detail))


def reference_suite_result_fingerprint(detail: Mapping[str, Any]) -> str:
    return canonical_fingerprint(dict(detail))


__all__ = [
    "REFERENCE_SUITE_SCHEMA_VERSION",
    "ReferenceCalculationError",
    "calculate_direct_observation",
    "canonical_fingerprint",
    "canonical_json",
    "compare_direct_observation",
    "normalize_direct_observation",
    "normalize_direct_observation_expected",
    "reference_case_fingerprint",
    "reference_case_result_fingerprint",
    "reference_suite_fingerprint",
    "reference_suite_result_fingerprint",
]
