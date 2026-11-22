from __future__ import annotations

import pytest

from creator_app.config import Settings
from creator_app.credential_broker import CredentialBroker
from creator_app.free_providers import GeminiAdapter
from creator_app.providers import build_provider_router


def test_free_router_uses_only_verified_free_route_by_default(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-claude-key")
    monkeypatch.setenv("MISTRAL_API_KEY", "test-mistral-key")
    monkeypatch.delenv("CKNEXUS_PROVIDER_ALLOW_PAID", raising=False)
    settings = Settings(provider_local_first=False, provider_allow_cloud=False)
    router = build_provider_router(settings, CredentialBroker(environment={}))
    assert [provider.name for provider in router._providers] == ["gemini"]
    assert router.policy.allow_cloud is True
    assert all(
        provider.name not in {"groq", "openai", "claude", "mistral"}
        for provider in router._providers
    )
    assert [status.name for status in router.statuses() if status.available] == ["gemini"]


def test_free_router_fails_closed_without_free_keys(monkeypatch):
    for key in ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("CKNEXUS_PROVIDER_ALLOW_PAID", raising=False)
    router = build_provider_router(Settings(), CredentialBroker(environment={}))
    assert router._providers == ()
    assert router.policy.allow_cloud is False


@pytest.mark.asyncio
async def test_router_fails_over_from_gemini_to_groq_without_paid_provider(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("CKNEXUS_PROVIDER_ALLOW_PAID", "true")
    router = build_provider_router(
        Settings(provider_local_first=False, provider_allow_cloud=True),
        CredentialBroker(environment={}),
    )

    async def gemini_unavailable(_prompt: str) -> str:
        raise RuntimeError("simulated free-tier rate limit")

    async def groq_success(_prompt: str) -> str:
        return "fallback-ok"

    monkeypatch.setattr(router._providers[0], "invoke", gemini_unavailable)
    monkeypatch.setattr(router._providers[1], "invoke", groq_success)
    result = await router.route("safe synthetic test")
    assert result.provider == "groq"
    assert result.output == "fallback-ok"
    assert result.attempts == 2
    assert result.degraded is True


@pytest.mark.asyncio
async def test_gemini_api_key_is_sent_in_header_not_url(monkeypatch):
    import json

    secret = "test-gemini-secret"
    monkeypatch.setenv("GEMINI_API_KEY", secret)
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({
                "candidates": [{"content": {"parts": [{"text": "ok"}]}}],
                "usageMetadata": {"totalTokenCount": 2},
            }).encode()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["key_header"] = request.get_header("X-goog-api-key")
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("creator_app.free_providers.urlopen", fake_urlopen)
    result = await GeminiAdapter().invoke("safe test")

    assert result == "ok"
    assert secret not in captured["url"]
    assert captured["key_header"] == secret


def test_billable_providers_require_both_explicit_opt_ins(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.delenv("CKNEXUS_PROVIDER_ALLOW_PAID", raising=False)

    paid_disabled = build_provider_router(
        Settings(provider_allow_cloud=True), CredentialBroker(environment={})
    )
    assert paid_disabled._providers == ()
    assert paid_disabled.policy.allow_cloud is False

    monkeypatch.setenv("CKNEXUS_PROVIDER_ALLOW_PAID", "true")
    cloud_disabled = build_provider_router(
        Settings(provider_allow_cloud=False), CredentialBroker(environment={})
    )
    assert cloud_disabled._providers == ()

    cloud_enabled = build_provider_router(
        Settings(provider_allow_cloud=True), CredentialBroker(environment={})
    )
    assert [provider.name for provider in cloud_enabled._providers] == ["groq", "openai"]
