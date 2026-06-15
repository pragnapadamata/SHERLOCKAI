"""OpenAI-compatible provider adapter (configurable base_url).

Works with any OpenAI-compatible chat/tool endpoint. Its purpose here is to capture the
demo cache against Google Gemini's free OpenAI-compatible API
(base_url https://generativelanguage.googleapis.com/v1beta/openai/, model gemini-2.0-flash,
key GEMINI_API_KEY) -- the daily budget dwarfs Groq's. Live mode stays on Groq; this is a
capture-only override driven by the tier's ``llm_*_base_url`` setting. The ``openai`` SDK is
imported lazily inside ``_client`` so importing this module needs neither the package nor a key.
"""

from __future__ import annotations

import json
import time
from collections.abc import Sequence

from backend.app.llm.base import LLMClient
from backend.app.llm.messages import ChatResult, Message, Provenance, ToolCall, ToolSpec


class OpenAIClient(LLMClient):
    """Chat client for any OpenAI-compatible API; base_url comes from options."""

    @property
    def provider(self) -> str:
        return "openai"

    def _client(self):
        from openai import OpenAI

        if not self.api_key:
            raise RuntimeError(
                "OpenAI-compatible API key is not configured. Set the tier's API key "
                "(e.g. GEMINI_API_KEY for the Gemini capture endpoint)."
            )
        # Per-call request timeout for the live client (LLM_REQUEST_TIMEOUT, default 180s),
        # so long large-context completions are not cut off by a lower client default.
        kwargs: dict[str, object] = {"api_key": self.api_key}
        base_url = self.options.get("base_url")
        if base_url:
            kwargs["base_url"] = str(base_url)
        timeout = self.options.get("request_timeout")
        if timeout is not None:
            kwargs["timeout"] = float(timeout)
        return OpenAI(**kwargs)

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
            tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=arguments))

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
