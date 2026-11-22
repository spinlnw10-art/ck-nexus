from __future__ import annotations

import pytest

from creator_app.config import Settings
from creator_app.credential_broker import CredentialBroker
from creator_app.providers import build_provider_router


def test_free_router_prefers_gemini_then_groq_and_excludes_paid(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-claude-key")
    monkeypatch.setenv("MISTRAL_API_KEY", "test-mistral-key")
    monkeypatch.delenv("CKNEXUS_PROVIDER_ALLOW_PAID", raising=False)
    settings = Settings(provider_local_first=False, provider_allow_cloud=False)
    router = build_provider_router(settings, CredentialBroker(environment={}))
    assert [provider.name for provider in router._providers] == ["gemini", "groq"]
    assert router.policy.allow_cloud is True
    assert all(provider.name not in {"openai", "claude", "mistral"} for provider in router._providers)
    assert [status.name for status in router.statuses() if status.available] == ["gemini", "groq"]


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
    monkeypatch.delenv("CKNEXUS_PROVIDER_ALLOW_PAID", raising=False)
    router = build_provider_router(
        Settings(provider_local_first=False, provider_allow_cloud=False),
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
