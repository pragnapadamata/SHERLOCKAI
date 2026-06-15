"""The tiered LLM registry.

Two tiers, configured independently from settings:

- ``small`` -- a fast, cheap model for routing and simple sub-tasks
- ``large`` -- a stronger model for heavy reasoning

Either tier can point at any registered provider, so the small tier could be one
vendor and the large another. Clients are cached per tier. When rate-limit handling
is configured (capture against a free-tier RPM cap), each client is wrapped so all
tiers share one pacing budget and survive 429s patiently.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from backend.app.core.config import Settings, get_settings
from backend.app.llm.base import LLMClient
from backend.app.llm.providers import build_client
from backend.app.llm.rate_limit import Pacer, RateLimitedClient

Tier = Literal["small", "large"]


class LLMRegistry:
    """Resolves a tier name to a configured, cached LLM client."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._cache: dict[str, LLMClient] = {}
        # One shared pacer so every tier respects a single provider RPM budget.
        self._pacer = Pacer(self._settings.llm_min_call_interval_s)

    def _resolve_key(self, tier: Tier) -> str | None:
        """A tier's key, falling back to the other tier's key when the provider
        matches -- so a single Groq key in .env drives both tiers. This is key
        sharing within one provider, not model-tier failover (deferred to Phase 8)."""

        s = self._settings
        if tier == "small":
            if s.llm_small_api_key:
                return s.llm_small_api_key
            if s.llm_large_provider == s.llm_small_provider:
                return s.llm_large_api_key
            return None
        if s.llm_large_api_key:
            return s.llm_large_api_key
        if s.llm_small_provider == s.llm_large_provider:
            return s.llm_small_api_key
        return None

    def _build(self, tier: Tier) -> LLMClient:
        s = self._settings
        if tier == "small":
            client = build_client(s.llm_small_provider, s.llm_small_model, self._resolve_key("small"),
                                  tier="small", base_url=s.llm_small_base_url,
                                  request_timeout=s.llm_request_timeout)
        else:
            client = build_client(s.llm_large_provider, s.llm_large_model, self._resolve_key("large"),
                                  tier="large", base_url=s.llm_large_base_url,
                                  request_timeout=s.llm_request_timeout)
        if s.llm_min_call_interval_s > 0 or s.llm_rate_limit_max_retries > 1:
            return RateLimitedClient(client, pacer=self._pacer,
                                     max_retries=s.llm_rate_limit_max_retries,
                                     max_wait=s.llm_rate_limit_max_wait_s)
        return client

    def get(self, tier: Tier) -> LLMClient:
        if tier not in ("small", "large"):
            raise ValueError(f"Unknown tier {tier!r}. Expected 'small' or 'large'.")
        if tier not in self._cache:
            self._cache[tier] = self._build(tier)
        return self._cache[tier]


@lru_cache
def get_llm_registry() -> LLMRegistry:
    """Return a process-wide cached registry built from default settings."""

    return LLMRegistry()
