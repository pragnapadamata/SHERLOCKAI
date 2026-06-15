"""The provider factory and tiered registry resolve configuration correctly."""

from __future__ import annotations

import pytest

from backend.app.core.config import Settings
from backend.app.llm.providers import build_client, get_provider_class
from backend.app.llm.providers.groq import GroqClient
from backend.app.llm.tiers import LLMRegistry


def test_build_groq_client_without_key():
    # Construction needs no key -- the key is only used when chat() is called.
    client = build_client("groq", "some-model", api_key=None, tier="large")
    assert isinstance(client, GroqClient)
    assert client.provider == "groq"
    assert client.model == "some-model"
    assert client.tier == "large"


def test_provider_lookup_is_case_insensitive():
    assert get_provider_class("GROQ") is GroqClient


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        get_provider_class("does-not-exist")


def test_registry_selects_and_caches_per_tier():
    settings = Settings(
        _env_file=None,
        llm_small_provider="groq",
        llm_small_model="small-model",
        llm_large_provider="groq",
        llm_large_model="large-model",
    )
    registry = LLMRegistry(settings)

    small = registry.get("small")
    large = registry.get("large")

    assert small.model == "small-model" and small.tier == "small"
    assert large.model == "large-model" and large.tier == "large"
    # Same tier returns the cached instance.
    assert registry.get("small") is small


def test_registry_rejects_unknown_tier():
    registry = LLMRegistry(Settings(_env_file=None))
    with pytest.raises(ValueError):
        registry.get("medium")  # type: ignore[arg-type]
