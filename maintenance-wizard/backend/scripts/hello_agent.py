"""End-to-end proof of the agentic spine against a real model.

Run with a Groq API key configured in .env:

    uv run python -m backend.scripts.hello_agent

It registers the echo tool, asks the large-tier model to use it, and prints the
final answer, the tool invocations, and the provenance trail. Success looks like
a coherent reply that mentions the echoed string, exactly one echo invocation,
and one provenance record per LLM call.
"""

from __future__ import annotations

from backend.app.agents.loop import ToolLoopOrchestrator
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.llm.messages import Message
from backend.app.llm.tiers import LLMRegistry
from backend.app.tools.base import ToolRegistry
from backend.app.tools.examples.echo import EchoTool

ECHO_STRING = "hello agentic spine"


def build_orchestrator() -> ToolLoopOrchestrator:
    settings = get_settings()
    configure_logging(settings.log_level, dev=settings.app_env != "prod")
    llm = LLMRegistry(settings).get("large")
    tools = ToolRegistry()
    tools.register(EchoTool())
    return ToolLoopOrchestrator(llm=llm, tools=tools, max_iters=5)


def main() -> None:
    orchestrator = build_orchestrator()
    messages = [
        Message(
            role="system",
            content=(
                "You are a tool-using assistant. When the user asks you to echo "
                "something, call the `echo` tool, then briefly confirm what you did."
            ),
        ),
        Message(
            role="user",
            content=(
                f"Use the echo tool to echo the string '{ECHO_STRING}', then "
                "briefly summarize what you did."
            ),
        ),
    ]

    result = orchestrator.run(messages)

    print("\n=== FINAL ANSWER ===")
    print(result.content)

    print("\n=== TOOL INVOCATIONS ===")
    for inv in result.tool_invocations:
        status = "ok" if inv.ok else f"ERROR: {inv.error}"
        print(f"  {inv.tool}({inv.arguments}) -> {inv.result!r}  [{status}]")

    print("\n=== PROVENANCE TRAIL ===")
    for prov in result.provenance:
        print(
            f"  {prov.tier}:{prov.provider}/{prov.model}  "
            f"{prov.latency_ms}ms  in={prov.tokens_in} out={prov.tokens_out}"
        )

    print(
        f"\niterations={result.iterations} stop_reason={result.stop_reason}"
    )


if __name__ == "__main__":
    main()
