"""Provider-neutral message, tool, and result types.

These are the lingua franca of the LLM layer. Each provider adapter translates
between these types and its own wire format, so the agents and tools never see
provider-specific shapes. The ``to_openai`` helpers exist because every provider
we target (Groq today, others later) speaks the OpenAI-style chat/tool schema.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class ToolSpec:
    """A tool advertised to the model: name, description, JSON-Schema arguments."""

    name: str
    description: str
    parameters: dict[str, Any]

    def to_openai(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolCall:
    """A model's request to call a tool, with arguments already parsed to a dict."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Message:
    """A single conversation message in provider-neutral form."""

    role: Role
    content: str | None = None
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)

    def to_openai(self) -> dict[str, Any]:
        """Serialize to an OpenAI-style message dict."""

        msg: dict[str, Any] = {"role": self.role}
        if self.content is not None:
            msg["content"] = self.content
        if self.role == "tool":
            msg["tool_call_id"] = self.tool_call_id
            if self.name:
                msg["name"] = self.name
        if self.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                    },
                }
                for tc in self.tool_calls
            ]
        return msg


@dataclass
class Provenance:
    """Traceability record for one LLM call: which model produced an output."""

    provider: str
    model: str
    tier: str
    latency_ms: float
    tokens_in: int | None = None
    tokens_out: int | None = None


@dataclass
class ChatResult:
    """The normalized result of a single chat completion."""

    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    provenance: Provenance | None = None
    raw: Any = None
