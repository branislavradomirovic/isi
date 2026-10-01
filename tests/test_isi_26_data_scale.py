import pytest

from tools.performance.evidence import summarize
from tools.performance.harness import run
from tools.performance.scenarios import ingestion_operation, payloads, prepared
from tools.performance.workloads import catalogue


def test_small_larger_inspection_materialization_and_zip_guards():
    result = ingestion_operation()
    assert len(result) == 8
    assert result[-2:] == ["xlsx_member_too_large", "xlsx_uncompressed_limit_exceeded"]
    assert payloads(512) == payloads(512)
    with pytest.raises(ValueError):
        payloads(1000000)


def test_concurrent_worker_inspection_preserves_terminal_accounting():
    workload = next(w for w in catalogue() if w.category == "data")
    with prepared(workload) as operation:
        result = run(workload, operation, repository_sha="a" * 40)
    assert summarize(result)["accepted"]
    assert len({s.operation.result_sha256 for s in result.measured}) == 1
