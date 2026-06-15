"""Provider registry and the client factory.

Adding a new provider is a two-line change: implement ``LLMClient`` in a new module
here, then add it to ``PROVIDERS``.
"""

from __future__ import annotations

from backend.app.llm.base import LLMClient
from backend.app.llm.providers.groq import GroqClient
from backend.app.llm.providers.openai_compat import OpenAIClient

PROVIDERS: dict[str, type[LLMClient]] = {
    "groq": GroqClient,            # live default (free tier)
    "openai": OpenAIClient,        # any OpenAI-compatible base_url (e.g. Gemini, for capture)
    # "cerebras": CerebrasClient,
}


def get_provider_class(name: str) -> type[LLMClient]:
    """Look up a provider adapter class by name (case-insensitive)."""

    key = name.lower().strip()
    if key not in PROVIDERS:
        raise ValueError(
            f"Unknown LLM provider {name!r}. Registered providers: "
            f"{sorted(PROVIDERS)}."
        )
    return PROVIDERS[key]


def build_client(
    provider: str,
    model: str,
    api_key: str | None = None,
    *,
    tier: str = "unknown",
    **options: object,
) -> LLMClient:
    """Construct a client for the given provider/model. No network or key needed at
    construction time -- the key is only used when ``chat`` is called."""

    return get_provider_class(provider)(
        model=model, api_key=api_key, tier=tier, **options
    )
