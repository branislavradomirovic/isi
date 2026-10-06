from __future__ import annotations

from dataclasses import dataclass

from src.core.config import get_settings
from src.platform.ai.models import AIModel
from src.platform.ai.providers import AIProvider, DevelopmentStubProvider, OllamaProvider, ProviderError


class GatewayError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProviderDescriptor:
    provider_name: str
    local_provider: bool
    development_only: bool


def provider_for_model(model: AIModel) -> AIProvider:
    settings = get_settings()
    provider_type = model.provider_type
    if provider_type == "ollama":
        return OllamaProvider(
            getattr(settings, "ai_ollama_base_url", "http://127.0.0.1:11434"),
            num_thread=getattr(settings, "ai_ollama_num_thread", None),
        )
    if provider_type == "stub":
        if str(getattr(settings, "isi_env", "development")).lower() == "production":
            raise GatewayError("development_stub_forbidden_in_production")
        if not bool(getattr(settings, "ai_allow_dev_stub", False)):
            raise GatewayError("development_stub_disabled")
        return DevelopmentStubProvider()
    if provider_type == "external":
        raise GatewayError("external_provider_not_configured")
    raise GatewayError(f"unsupported_provider_type:{provider_type}")


def descriptor_for_model(model: AIModel) -> ProviderDescriptor:
    return ProviderDescriptor(
        provider_name=model.provider_name,
        local_provider=bool(model.local_provider),
        development_only=model.provider_type == "stub",
    )


__all__ = [
    "GatewayError",
    "ProviderDescriptor",
    "ProviderError",
    "descriptor_for_model",
    "provider_for_model",
]
