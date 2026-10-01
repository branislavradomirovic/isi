from unittest.mock import patch

from tools.performance.evidence import summarize
from tools.performance.harness import run
from tools.performance.scenarios import prepared
from tools.performance.workloads import catalogue


def test_persisted_small_larger_reports_render_stably_without_ai():
    workload = next(w for w in catalogue() if w.category == "report")
    with patch("src.platform.ai.service.execute_ai_job", side_effect=AssertionError("report_inference_forbidden")):
        with prepared(workload) as operation:
            result = run(workload, operation, repository_sha="a" * 40)
    assert summarize(result)["accepted"]
    assert len({s.operation.result_sha256 for s in result.measured}) == 1
