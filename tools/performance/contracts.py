"""Immutable, closed evidence vocabulary for ISI-26 R1."""
from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Seconds = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Count = Annotated[int, Field(ge=0, strict=True)]
WorkloadID = Literal[
    "api.health.read.v1", "api.authenticated.context.v1", "api.authenticated.navigation.v1",
    "api.readiness.synthetic.v1", "data.ingestion.synthetic.v1", "simpa.analytics.synthetic.v1",
    "ordo.forecast.synthetic.v1", "report.render.synthetic.v1", "ai.stub.synthetic.v1", "ai.circuit.synthetic.v1",
]
Reason = Literal[
    "ok", "unexpected_exception", "correctness_mismatch", "timeout", "dependency_unavailable",
    "xlsx_member_too_large", "xlsx_uncompressed_limit_exceeded", "authorization_denied", "circuit_open",
]
Metric = Literal["correctness_failures", "p50_seconds", "p95_seconds", "p99_seconds",
                 "throughput", "resource", "resilience_failures"]


class BudgetClass(StrEnum):
    CORRECTNESS = "CORRECTNESS"
    LATENCY_THROUGHPUT = "LATENCY_THROUGHPUT"
    RESOURCE = "RESOURCE"
    RESILIENCE = "RESILIENCE"


class BudgetState(StrEnum):
    HARD_GATE = "HARD_GATE"
    CALIBRATED = "CALIBRATED"
    UNCALIBRATED = "UNCALIBRATED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNAVAILABLE = "UNAVAILABLE"


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)


class Calibration(Frozen):
    evidence_sha256: Digest
    accepted_contract_sha256: Digest
    repeated_runs: Annotated[int, Field(ge=3, strict=True)]
    observed_bound: Annotated[float, Field(gt=0, allow_inf_nan=False)]
    safety_margin: Annotated[float, Field(gt=1, allow_inf_nan=False)]
    scope: Literal["REPOSITORY_ACCEPTANCE_ONLY"] = "REPOSITORY_ACCEPTANCE_ONLY"


class Budget(Frozen):
    metric: Metric
    budget_class: BudgetClass
    state: BudgetState
    threshold: Seconds | None = None
    calibration: Calibration | None = None
    unavailable_reason: Literal["not_portable"] | None = None

    @model_validator(mode="after")
    def valid_budget(self) -> Budget:
        expected = (BudgetClass.CORRECTNESS if self.metric == "correctness_failures" else
                    BudgetClass.RESILIENCE if self.metric == "resilience_failures" else
                    BudgetClass.RESOURCE if self.metric == "resource" else BudgetClass.LATENCY_THROUGHPUT)
        if self.budget_class != expected:
            raise ValueError("metric_class_mismatch")
        if expected in {BudgetClass.CORRECTNESS, BudgetClass.RESILIENCE}:
            if self.state != BudgetState.HARD_GATE or self.threshold != 0:
                raise ValueError("non_compensable_gate_required")
        elif self.state == BudgetState.HARD_GATE:
            raise ValueError("timing_resource_not_hard_gate")
        if self.state == BudgetState.CALIBRATED:
            if self.calibration is None or self.threshold is None or self.metric == "resource":
                raise ValueError("calibration_evidence_required")
            c = self.calibration
            safe = c.observed_bound / c.safety_margin if self.metric == "throughput" else c.observed_bound * c.safety_margin
            if self.threshold != safe:
                raise ValueError("calibration_margin_mismatch")
        elif self.calibration is not None:
            raise ValueError("unexpected_calibration")
        if self.state not in {BudgetState.HARD_GATE, BudgetState.CALIBRATED} and self.threshold is not None:
            raise ValueError("unexpected_threshold")
        if (self.state == BudgetState.UNAVAILABLE) != (self.unavailable_reason is not None):
            raise ValueError("unavailable_reason_required")
        return self


class Workload(Frozen):
    workload_id: WorkloadID
    version: Literal[1] = 1
    title: Literal["Health", "Authenticated context", "Authenticated navigation", "Synthetic readiness",
                   "Synthetic ingestion", "SIMPA aggregate statistics", "ORDO explicit forecast",
                   "Persisted report rendering", "Development AI stub", "AI circuit and fallback"]
    category: Literal["api", "data", "simpa", "ordo", "report", "ai"]
    execution_mode: Literal["IN_PROCESS", "ISOLATED_SQLITE"]
    fixture: Literal["synthetic-v1"] = "synthetic-v1"
    fixture_sha256: Digest
    warmups: Annotated[int, Field(ge=0, le=100, strict=True)] = 1
    samples: Annotated[int, Field(ge=1, le=1024, strict=True)] = 8
    concurrency: Annotated[int, Field(ge=1, le=16, strict=True)] = 2
    correctness_gates: tuple[Literal["exact_result", "scope_isolation", "bounded_failure", "deterministic_result"], ...]
    budgets: tuple[Budget, ...]
    expected_failures: tuple[Reason, ...] = ()
    privacy: Literal["SYNTHETIC_NO_RAW_EVIDENCE"] = "SYNTHETIC_NO_RAW_EVIDENCE"
    environment: Literal["LOCAL_REPOSITORY", "LOCAL_DISPOSABLE_POSTGRES", "LOCAL_DISPOSABLE_SERVICES"] = "LOCAL_REPOSITORY"

    @model_validator(mode="after")
    def required_metrics(self) -> Workload:
        metrics = [b.metric for b in self.budgets]
        if len(metrics) != len(set(metrics)) or set(metrics) != {
            "correctness_failures", "resilience_failures", "p50_seconds", "p95_seconds", "p99_seconds", "throughput", "resource"
        }:
            raise ValueError("required_metrics_mismatch")
        if not self.correctness_gates or any(x in self.expected_failures for x in ("ok", "unexpected_exception", "correctness_mismatch")):
            raise ValueError("invalid_gates_or_failures")
        return self


class Operation(Frozen):
    success: Annotated[bool, Field(strict=True)] = True
    correct: Annotated[bool, Field(strict=True)] = True
    reason: Reason = "ok"
    result_sha256: Digest | None = None

    @model_validator(mode="after")
    def coherent(self) -> Operation:
        if self.success and (not self.correct or self.reason != "ok"):
            raise ValueError("incoherent_operation")
        if not self.success and self.reason == "ok":
            raise ValueError("failure_reason_required")
        return self


class Sample(Frozen):
    operation: Operation
    seconds: Seconds


class Result(Frozen):
    schema_version: Literal["ISI26-R1-v1"] = "ISI26-R1-v1"
    repository_sha: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    contract: Workload
    contract_sha256: Digest
    measured: tuple[Sample, ...]
    warmup_failures: Count
    wall_seconds: Annotated[float, Field(gt=0, allow_inf_nan=False)]
    effective_concurrency: Annotated[int, Field(ge=1, le=16, strict=True)]
    PRODUCTION_CAPACITY_VERIFIED: Literal[False] = False
    SERVER_VERIFIED: Literal[False] = False

    @model_validator(mode="after")
    def integrity(self) -> Result:
        if self.contract_sha256 != fingerprint(self.contract):
            raise ValueError("contract_fingerprint_mismatch")
        if len(self.measured) != self.contract.samples or self.warmup_failures > self.contract.warmups:
            raise ValueError("sample_count_mismatch")
        if self.effective_concurrency != min(self.contract.concurrency, self.contract.samples):
            raise ValueError("concurrency_mismatch")
        return self


def canonical_json(value: object) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def fingerprint(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()
