"""Bounded thread execution; correctness is independent of timing."""
from __future__ import annotations

import math
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor

from tools.performance.contracts import Operation, Result, Sample, Workload, fingerprint


def nearest_rank(samples: Sequence[float], q: float) -> float | None:
    if not math.isfinite(q) or not 0 < q <= 1:
        raise ValueError("invalid_quantile")
    if any(not math.isfinite(x) or x < 0 for x in samples):
        raise ValueError("invalid_latency")
    return sorted(samples)[math.ceil(q * len(samples)) - 1] if samples else None


def run(workload: Workload, operation: Callable[[], Operation], *, repository_sha: str,
        clock: Callable[[], float] = time.perf_counter) -> Result:
    def invoke() -> Operation:
        try:
            result = operation()
            if not isinstance(result, Operation):
                raise TypeError("operation_contract_required")
            if not result.success and (result.reason not in workload.expected_failures or not result.correct):
                return Operation(success=False, correct=False, reason=result.reason)
            return result
        except Exception:
            return Operation(success=False, correct=False, reason="unexpected_exception")

    warmup_failures = sum(not invoke().correct for _ in range(workload.warmups))

    def measure(_: int) -> Sample:
        start = clock()
        result = invoke()
        return Sample(operation=result, seconds=clock() - start)

    effective = min(workload.concurrency, workload.samples)
    with ThreadPoolExecutor(max_workers=effective) as pool:
        start = clock()
        samples = tuple(pool.map(measure, range(workload.samples)))
        elapsed = clock() - start
    return Result(repository_sha=repository_sha, contract=workload, contract_sha256=fingerprint(workload),
                  measured=samples, warmup_failures=warmup_failures, wall_seconds=elapsed,
                  effective_concurrency=effective)
