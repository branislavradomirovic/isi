from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass
from typing import Any, Protocol

import httpx


class ProviderError(RuntimeError):
    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message or code


@dataclass(frozen=True)
class CompletionRequest:
    model_name: str
    system_prompt: str
    user_prompt: str
    timeout_seconds: int = 120
    structured: bool = False


@dataclass(frozen=True)
class CompletionResult:
    text: str
    provider_name: str
    model_name: str
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class EmbeddingResult:
    vector: list[float]
    provider_name: str
    model_name: str
    latency_ms: int


class AIProvider(Protocol):
    provider_name: str
    local_provider: bool

    def complete(self, request: CompletionRequest) -> CompletionResult: ...
    def embed(self, *, model_name: str, text: str, timeout_seconds: int = 120) -> EmbeddingResult: ...


class OllamaProvider:
    provider_name = "ollama"
    local_provider = True

    def __init__(self, base_url: str = "http://127.0.0.1:11434") -> None:
        self.base_url = base_url.rstrip("/")

    def complete(self, request: CompletionRequest) -> CompletionResult:
        started = time.monotonic()
        payload: dict[str, Any] = {
            "model": request.model_name,
            "stream": False,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
        }
        if request.structured:
            payload["format"] = "json"
        try:
            response = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=request.timeout_seconds)
        except httpx.TimeoutException as exc:
            raise ProviderError("timeout", "Ollama request timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderError("provider_unavailable", "Ollama is unavailable") from exc
        if response.status_code >= 400:
            raise ProviderError("provider_http_error", f"Ollama HTTP {response.status_code}")
        try:
            body = response.json()
            text = str(body["message"]["content"])
        except (ValueError, KeyError, TypeError) as exc:
            raise ProviderError("invalid_provider_response", "Ollama returned an invalid response") from exc
        return CompletionResult(
            text=text,
            provider_name=self.provider_name,
            model_name=request.model_name,
            latency_ms=int((time.monotonic() - started) * 1000),
            input_tokens=_int_or_none(body.get("prompt_eval_count")),
            output_tokens=_int_or_none(body.get("eval_count")),
        )

    def embed(self, *, model_name: str, text: str, timeout_seconds: int = 120) -> EmbeddingResult:
        started = time.monotonic()
        endpoints = (
            ("/api/embed", {"model": model_name, "input": text}),
            ("/api/embeddings", {"model": model_name, "prompt": text}),
        )
        last_status = None
        for path, payload in endpoints:
            try:
                response = httpx.post(f"{self.base_url}{path}", json=payload, timeout=timeout_seconds)
            except httpx.TimeoutException as exc:
                raise ProviderError("timeout", "Ollama embedding request timed out") from exc
            except httpx.HTTPError as exc:
                raise ProviderError("provider_unavailable", "Ollama is unavailable") from exc
            last_status = response.status_code
            if response.status_code == 404:
                continue
            if response.status_code >= 400:
                raise ProviderError("provider_http_error", f"Ollama HTTP {response.status_code}")
            try:
                body = response.json()
                if "embeddings" in body:
                    vector = body["embeddings"][0]
                else:
                    vector = body["embedding"]
                values = [float(item) for item in vector]
            except (ValueError, KeyError, TypeError, IndexError) as exc:
                raise ProviderError("invalid_provider_response", "Ollama returned an invalid embedding") from exc
            return EmbeddingResult(
                vector=values,
                provider_name=self.provider_name,
                model_name=model_name,
                latency_ms=int((time.monotonic() - started) * 1000),
            )
        raise ProviderError("provider_http_error", f"Ollama embedding endpoint unavailable ({last_status})")


class DevelopmentStubProvider:
    provider_name = "development-stub"
    local_provider = True

    def complete(self, request: CompletionRequest) -> CompletionResult:
        started = time.monotonic()
        if request.structured:
            text = '{"status":"ok","message":"ISI-07 development diagnostic"}'
        else:
            text = "ISI-07 development diagnostic PASS. This is not a domain AI answer."
        return CompletionResult(
            text=text,
            provider_name=self.provider_name,
            model_name=request.model_name,
            latency_ms=max(1, int((time.monotonic() - started) * 1000)),
            input_tokens=None,
            output_tokens=None,
        )

    def embed(self, *, model_name: str, text: str, timeout_seconds: int = 120) -> EmbeddingResult:
        started = time.monotonic()
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        raw = [((byte / 255.0) * 2.0) - 1.0 for byte in digest[:16]]
        norm = math.sqrt(sum(value * value for value in raw)) or 1.0
        vector = [round(value / norm, 8) for value in raw]
        return EmbeddingResult(
            vector=vector,
            provider_name=self.provider_name,
            model_name=model_name,
            latency_ms=max(1, int((time.monotonic() - started) * 1000)),
        )


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
