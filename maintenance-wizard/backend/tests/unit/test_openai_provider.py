"""The OpenAI-compatible provider is registered and carries base_url (capture path).

Construction only -- no network, no key use (the key is only touched inside chat()).
"""

from __future__ import annotations

from backend.app.llm.providers import build_client, get_provider_class


def test_openai_provider_registered():
    assert get_provider_class("openai").__name__ == "OpenAIClient"
    assert get_provider_class("OpenAI").__name__ == "OpenAIClient"  # case-insensitive


def test_openai_client_constructs_with_base_url():
    client = build_client(
        "openai", "gemini-2.0-flash", "test-key", tier="large",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    assert client.provider == "openai"
    assert client.model == "gemini-2.0-flash"
    assert client.options.get("base_url") == "https://generativelanguage.googleapis.com/v1beta/openai/"


def test_groq_still_default_and_ignores_base_url():
    client = build_client("groq", "llama-3.3-70b-versatile", "k", tier="large", base_url=None)
    assert client.provider == "groq"
