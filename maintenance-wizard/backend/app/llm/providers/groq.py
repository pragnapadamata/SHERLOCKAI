"""Groq provider adapter -- the development default (free tier).

Groq exposes an OpenAI-compatible chat/tool interface, so this adapter is a thin
translation between our neutral types and the Groq SDK. The SDK and the API key
are touched lazily inside :meth:`_client`, so importing this module never
requires the ``groq`` package to be importable or a key to be present -- the
offline test suite relies on that.
"""

from __future__ import annotations

import json
import time
from collections.abc import Sequence

from backend.app.llm.base import LLMClient
from backend.app.llm.messages import (
    ChatResult,
    Message,
    Provenance,
    ToolCall,
    ToolSpec,
)


class GroqClient(LLMClient):
    """Chat client backed by Groq's OpenAI-compatible API."""

    @property
    def provider(self) -> str:
        return "groq"

    def _client(self):
        from groq import Groq

        if not self.api_key:
            raise RuntimeError(
                "Groq API key is not configured. Set LLM_SMALL_API_KEY / "
                "LLM_LARGE_API_KEY in your environment or .env."
            )
        # Per-call request timeout for the live client. The SDK default is 60s, which cut
        # off long large-context completions; LLM_REQUEST_TIMEOUT (default 180s) raises it.
        kwargs: dict[str, object] = {"api_key": self.api_key}
        timeout = self.options.get("request_timeout")
        if timeout is not None:
            kwargs["timeout"] = float(timeout)
        return Groq(**kwargs)

    def chat(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec] | None = None,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatResult:
        client = self._client()

        kwargs: dict[str, object] = {
            "model": self.model,
            "messages": [m.to_openai() for m in messages],
        }
        if tools:
            kwargs["tools"] = [t.to_openai() for t in tools]
            kwargs["tool_choice"] = "auto"
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        start = time.perf_counter()
        resp = client.chat.completions.create(**kwargs)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        message = resp.choices[0].message
        tool_calls: list[ToolCall] = []
        for tc in message.tool_calls or []:
            try:
                arguments = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {"_raw": tc.function.arguments}
            tool_calls.append(
                ToolCall(id=tc.id, name=tc.function.name, arguments=arguments)
            )

        usage = getattr(resp, "usage", None)
        provenance = Provenance(
            provider=self.provider,
            model=self.model,
            tier=self.tier,
            latency_ms=latency_ms,
            tokens_in=getattr(usage, "prompt_tokens", None),
            tokens_out=getattr(usage, "completion_tokens", None),
        )
        return ChatResult(
            content=message.content,
            tool_calls=tool_calls,
            provenance=provenance,
            raw=resp,
        )
