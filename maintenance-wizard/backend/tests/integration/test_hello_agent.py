"""End-to-end loop behavior, driven by a scripted fake LLM (no network)."""

from __future__ import annotations

import pytest

from backend.app.agents.loop import (
    ToolLoopError,
    ToolLoopOrchestrator,
    run_tool_loop,
)
from backend.app.llm.messages import Message
from backend.app.tools.base import ToolRegistry
from backend.app.tools.examples.echo import EchoTool
from backend.tests.fakes import FakeLLMClient, text_result, tool_call_result


def _registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(EchoTool())
    return registry


def test_loop_invokes_tool_then_completes():
    llm = FakeLLMClient(
        [
            tool_call_result("call_1", "echo", {"message": "hello agentic spine"}),
            text_result("Done. I echoed 'hello agentic spine'."),
        ]
    )

    result = run_tool_loop(
        [Message(role="user", content="echo it")],
        llm=llm,
        tools=_registry(),
        max_iters=5,
    )

    assert result.stop_reason == "completed"
    assert result.content == "Done. I echoed 'hello agentic spine'."

    # The tool was actually invoked with the right argument and result.
    assert len(result.tool_invocations) == 1
    invocation = result.tool_invocations[0]
    assert invocation.tool == "echo"
    assert invocation.arguments == {"message": "hello agentic spine"}
    assert invocation.result == "hello agentic spine"
    assert invocation.ok is True

    # Provenance recorded for both LLM calls.
    assert len(result.provenance) == 2
    assert all(p.provider == "fake" for p in result.provenance)

    # The tool result is in the transcript, linked to the call id.
    assert any(
        m.role == "tool" and m.tool_call_id == "call_1" for m in result.messages
    )


def test_orchestrator_wraps_loop_and_returns_immediately_on_text():
    llm = FakeLLMClient([text_result("no tools needed")])
    orchestrator = ToolLoopOrchestrator(llm=llm, tools=_registry(), max_iters=3)

    result = orchestrator.run([Message(role="user", content="hi")])

    assert result.content == "no tools needed"
    assert result.iterations == 1
    assert result.tool_invocations == []


def test_unknown_tool_is_captured_not_crashing():
    llm = FakeLLMClient(
        [
            tool_call_result("c1", "missing_tool", {}),
            text_result("recovered after a bad tool call"),
        ]
    )

    result = run_tool_loop(
        [Message(role="user", content="x")],
        llm=llm,
        tools=_registry(),
        max_iters=5,
    )

    assert result.content == "recovered after a bad tool call"
    assert result.tool_invocations[0].ok is False
    assert "missing_tool" in (result.tool_invocations[0].error or "")


def test_max_iters_raises_with_partial_result_attached():
    # The model never stops calling tools, so the loop must hit the bound.
    llm = FakeLLMClient(
        [tool_call_result(f"c{i}", "echo", {"message": "x"}) for i in range(10)]
    )

    with pytest.raises(ToolLoopError) as exc_info:
        run_tool_loop(
            [Message(role="user", content="x")],
            llm=llm,
            tools=_registry(),
            max_iters=3,
        )

    assert exc_info.value.result.stop_reason == "max_iters"
    assert exc_info.value.result.iterations == 3
