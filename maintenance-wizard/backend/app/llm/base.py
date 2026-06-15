"""The abstract LLM client every provider adapter implements.

Keeping this interface small is deliberate: a new provider only has to translate
messages and tools to its wire format and translate the response back into a
``ChatResult``. Streaming is intentionally deferred to the API phase.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from backend.app.llm.messages import ChatResult, Message, ToolSpec


class LLMClient(ABC):
    """Provider-agnostic chat client for one model at one tier."""

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        *,
        tier: str = "unknown",
        **options: object,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.tier = tier
        self.options = options

    @property
    @abstractmethod
    def provider(self) -> str:
        """The provider name, e.g. ``"groq"``."""

    @abstractmethod
    def chat(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec] | None = None,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatResult:
        """Run one chat completion and return a normalized result."""
