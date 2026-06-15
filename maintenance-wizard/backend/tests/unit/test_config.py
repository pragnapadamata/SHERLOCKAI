"""Settings load from defaults and are overridable by environment variables."""

from __future__ import annotations

from backend.app.core.config import Settings


def test_defaults_are_groq_tiers():
    settings = Settings(_env_file=None)
    assert settings.app_env == "dev"
    assert settings.llm_small_provider == "groq"
    assert settings.llm_large_provider == "groq"
    assert settings.llm_small_model
    assert settings.llm_large_model
    # No key is baked in -- it must come from config.
    assert settings.llm_small_api_key is None
    assert settings.llm_large_api_key is None


def test_environment_overrides_large_tier(monkeypatch):
    monkeypatch.setenv("LLM_LARGE_PROVIDER", "openai")
    monkeypatch.setenv("LLM_LARGE_MODEL", "gpt-4o")
    monkeypatch.setenv("LLM_LARGE_API_KEY", "sk-test-123")

    settings = Settings(_env_file=None)

    assert settings.llm_large_provider == "openai"
    assert settings.llm_large_model == "gpt-4o"
    assert settings.llm_large_api_key == "sk-test-123"
    # The small tier is independent and keeps its default.
    assert settings.llm_small_provider == "groq"


def test_env_var_names_are_case_insensitive(monkeypatch):
    monkeypatch.setenv("log_level", "DEBUG")
    assert Settings(_env_file=None).log_level == "DEBUG"
