from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.core.config import Settings
from src.platform.ai.providers import CompletionRequest, OllamaProvider


@pytest.mark.parametrize('value', [0, -1, 65])
def test_settings_reject_invalid_limits(value):
    with pytest.raises(ValidationError):
        Settings(ai_ollama_num_thread=value)


@pytest.mark.parametrize('value', [0, -1, 65, True, '2'])
def test_provider_rejects_invalid_limits(value):
    with pytest.raises(ValueError):
        OllamaProvider(num_thread=value)


@pytest.mark.parametrize('limit', [None, 2, 64])
def test_completion_preserves_default_and_bounds_isi_request(monkeypatch, limit):
    payloads = []
    def post(url, *, json, timeout):
        payloads.append(json)
        return SimpleNamespace(status_code=200, json=lambda: {'message': {'content': 'synthetic'}})
    monkeypatch.setattr('src.platform.ai.providers.httpx.post', post)
    result = OllamaProvider(num_thread=limit).complete(CompletionRequest('reference', 'system', 'synthetic', structured=True))
    assert result.text == 'synthetic' and payloads[0]['format'] == 'json'
    if limit is None:
        assert 'options' not in payloads[0]
    else:
        assert payloads[0]['options'] == {'num_thread': limit}


@pytest.mark.parametrize('limit', [None, 2])
def test_both_embedding_endpoints_keep_same_thread_bound(monkeypatch, limit):
    calls = []
    def post(url, *, json, timeout):
        calls.append((url, json))
        if url.endswith('/api/embed'):
            return SimpleNamespace(status_code=404)
        return SimpleNamespace(status_code=200, json=lambda: {'embedding': [1., 2.]})
    monkeypatch.setattr('src.platform.ai.providers.httpx.post', post)
    result = OllamaProvider(num_thread=limit).embed(model_name='reference', text='synthetic')
    assert result.vector == [1., 2.] and len(calls) == 2
    for _, payload in calls:
        if limit is None:
            assert 'options' not in payload
        else:
            assert payload['options'] == {'num_thread': limit}


def test_gateway_propagates_optional_isi_limit(monkeypatch):
    from src.platform.ai import gateway
    monkeypatch.setattr(gateway, 'get_settings', lambda: SimpleNamespace(
        ai_ollama_base_url='http://synthetic.invalid', ai_ollama_num_thread=2))
    provider = gateway.provider_for_model(SimpleNamespace(provider_type='ollama'))
    assert provider.num_thread == 2 and provider.local_provider is True
