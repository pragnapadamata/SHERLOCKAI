"""The bounded tool-calling loop -- the agentic spine.

The loop is intentionally small and dependable: call the model, run any tools it
requests, feed the results back, and stop either when the model returns a final
answer or when ``max_iters`` is hit (which raises, never loops unbounded). A
tool that raises is captured as a failed invocation and reported back to the
model rather than crashing the run.

``ToolLoopOrchestrator`` is the narrow public interface -- callers depend only on
``.run(messages, ...) -> AgentResult``. Swapping in a different orchestration
engine (e.g. a graph framework) later is a single-file replacement behind it.
"""

from __future__ import annotations

import json
from typing import Any

from backend.app.agents.events import emit
from backend.app.agents.schemas import AgentResult, ToolInvocation
from backend.app.core.logging import get_logger
from backend.app.llm.base import LLMClient
from backend.app.llm.messages import Message, ToolCall
from backend.app.tools.base import ToolRegistry

log = get_logger(__name__)

DEFAULT_MAX_ITERS = 5


class ToolLoopError(RuntimeError):
    """Raised when the loop exhausts ``max_iters`` without a final answer.

    The partial :class:`AgentResult` is attached as ``.result`` for debugging.
    """

    def __init__(self, message: str, result: AgentResult) -> None:
        super().__init__(message)
        self.result = result


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return str(value)


def _execute_tool(tools: ToolRegistry, call: ToolCall) -> ToolInvocation:
    try:
        tool = tools.get(call.name)
    except KeyError as exc:
        log.warning("tool_not_found", tool=call.name)
        return ToolInvocation(
            tool=call.name, arguments=call.arguments, ok=False, error=str(exc)
        )
    try:
        result = tool.run(**call.arguments)
        return ToolInvocation(
            tool=call.name, arguments=call.arguments, result=result, ok=True
        )
    except Exception as exc:  # noqa: BLE001 -- tool faults must not crash the loop
        log.warning("tool_failed", tool=call.name, error=str(exc))
        return ToolInvocation(
            tool=call.name,
            arguments=call.arguments,
            ok=False,
            error=f"{type(exc).__name__}: {exc}",
        )


def run_tool_loop(
    messages: list[Message],
    *,
    llm: LLMClient,
    tools: ToolRegistry,
    allow: list[str] | None = None,
    max_iters: int = DEFAULT_MAX_ITERS,
) -> AgentResult:
    """Drive the model/tool loop to a final answer or raise ``ToolLoopError``."""

    conversation = list(messages)
    result = AgentResult(content=None, messages=conversation)
    specs = tools.specs(allow=allow)

    for iteration in range(1, max_iters + 1):
        result.iterations = iteration
        try:
            chat = llm.chat(conversation, tools=specs or None)
        except Exception as exc:  # noqa: BLE001 -- provider/tool-call errors: retry once, then degrade
            log.warning("llm_call_failed_retrying", error=str(exc))
            try:
                chat = llm.chat(conversation, tools=specs or None)
            except Exception as exc2:  # noqa: BLE001 -- persistent failure: return partial, never crash
                log.warning("llm_call_failed", error=str(exc2))
                result.stop_reason = "llm_error"
                return result
        if chat.provenance is not None:
            result.provenance.append(chat.provenance)

        conversation.append(
            Message(
                role="assistant",
                content=chat.content,
                tool_calls=chat.tool_calls,
            )
        )

        if not chat.tool_calls:
            result.content = chat.content
            result.stop_reason = "completed"
            return result

        for call in chat.tool_calls:
            emit({"type": "tool_start", "tool": call.name})
            invocation = _execute_tool(tools, call)
            result.tool_invocations.append(invocation)
            summary = invocation.result.get("summary") if isinstance(invocation.result, dict) else None
            emit({"type": "tool_end", "tool": call.name, "ok": invocation.ok, "summary": summary})
            payload = invocation.result if invocation.ok else invocation.error
            conversation.append(
                Message(
                    role="tool",
                    name=call.name,
                    tool_call_id=call.id,
                    content=_stringify(payload),
                )
            )

    result.stop_reason = "max_iters"
    raise ToolLoopError(
        f"Tool loop exceeded max_iters={max_iters} without a final answer.",
        result,
    )


class ToolLoopOrchestrator:
    """Narrow orchestration interface over :func:`run_tool_loop`.

    Callers depend only on ``run(messages, ...) -> AgentResult`` so the engine
    underneath can be replaced without touching them.
    """

    def __init__(
        self,
        llm: LLMClient,
        tools: ToolRegistry,
        *,
        max_iters: int = DEFAULT_MAX_ITERS,
    ) -> None:
        self._llm = llm
        self._tools = tools
        self._max_iters = max_iters

    def run(
        self,
        messages: list[Message],
        *,
        allow: list[str] | None = None,
        max_iters: int | None = None,
    ) -> AgentResult:
        return run_tool_loop(
            messages,
            llm=self._llm,
            tools=self._tools,
            allow=allow,
            max_iters=max_iters or self._max_iters,
        )
