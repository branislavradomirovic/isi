from src.platform.ai.providers import CompletionRequest, DevelopmentStubProvider


def test_development_stub_is_deterministic_and_non_domain():
    provider = DevelopmentStubProvider()
    result = provider.complete(
        CompletionRequest(
            model_name="stub",
            system_prompt="system",
            user_prompt="user",
            structured=True,
        )
    )
    assert result.provider_name == "development-stub"
    assert '"status":"ok"' in result.text
    assert "domain" not in result.text.lower()


def test_development_stub_embedding_has_fixed_dimension():
    provider = DevelopmentStubProvider()
    first = provider.embed(model_name="stub-embed", text="same")
    second = provider.embed(model_name="stub-embed", text="same")
    assert first.vector == second.vector
    assert len(first.vector) == 16
