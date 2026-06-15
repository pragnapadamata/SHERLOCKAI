"""A per-context event sink so the agentic process can be streamed live.

``run_streaming`` sets the sink for the duration of one orchestrator run; the
loop and specialists call ``emit`` as they work. The sink is a ContextVar, so
concurrent requests (each running in its own copied context via asyncio.to_thread)
are isolated -- one stream never receives another's events. When no sink is set
(the normal, non-streaming path), ``emit`` is a no-op.
"""

from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar

event_sink: ContextVar[Callable[[dict], None] | None] = ContextVar(
    "agent_event_sink", default=None
)


def emit(event: dict) -> None:
    sink = event_sink.get()
    if sink is None:
        return
    try:
        sink(event)
    except Exception:  # noqa: BLE001 -- event emission must never break the agent
        pass
