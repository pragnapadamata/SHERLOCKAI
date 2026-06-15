"""Shared input/output contracts for agent runs.

``AgentResult`` carries the two things the explainability requirement needs: a
provenance trail (which model produced each step) and a tool-invocation trail
(which tool was called with what arguments and what it returned).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.llm.messages import Message, Provenance


@dataclass
class ToolInvocation:
    """One tool call executed during a run, with its outcome."""

    tool: str
    arguments: dict[str, Any]
    result: Any = None
    ok: bool = True
    error: str | None = None


@dataclass
class AgentResult:
    """The outcome of a bounded agent run."""

    content: str | None
    messages: list[Message] = field(default_factory=list)
    tool_invocations: list[ToolInvocation] = field(default_factory=list)
    provenance: list[Provenance] = field(default_factory=list)
    iterations: int = 0
    stop_reason: str = "completed"  # "completed" | "max_iters"
