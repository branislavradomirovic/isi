from unittest.mock import patch

import httpx
import pytest

from tools.performance.evidence import summarize
from tools.performance.harness import run
from tools.performance.scenarios import circuit_operation, prepared
from tools.performance.workloads import catalogue


@pytest.mark.parametrize("workload", [w for w in catalogue() if w.category == "ai"])
def test_concurrent_synthetic_jobs_and_registered_fallback(workload):
    with prepared(workload) as operation:
        result = run(workload, operation, repository_sha="a" * 40)
    assert summarize(result)["accepted"]
    assert len({s.operation.result_sha256 for s in result.measured}) == 1
    assert circuit_operation() == ("closed", "open", "half_open", "closed")


def test_timeout_translation_uses_transport_double_only():
    from src.platform.ai.providers import OllamaProvider, CompletionRequest, ProviderError
    with patch("src.platform.ai.providers.httpx.post", side_effect=httpx.ReadTimeout("synthetic")) as post:
        with pytest.raises(ProviderError) as error:
            OllamaProvider(base_url="http://synthetic.invalid").complete(CompletionRequest(
                model_name="synthetic", system_prompt="synthetic", user_prompt="synthetic", timeout_seconds=5))
        assert error.value.code == "timeout"
        assert post.call_args.kwargs["timeout"] == 5


@pytest.mark.parametrize("kind", ["ai", "data"])
def test_rq_dispatch_contract_and_bounded_failure_without_redis(kind):
    from tools.performance.scenarios import queue_contract
    assert queue_contract(kind) == {"accepted_dispatch": 1, "bounded_failure": 1, "job_timeout": 900}
