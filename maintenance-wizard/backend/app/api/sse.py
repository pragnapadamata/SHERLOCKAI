"""Server-Sent Events helpers: run blocking agent work in a worker thread and stream
its live events to the client.

Each call creates its own queue + emit closure and runs the work via asyncio.to_thread
(which copies the context), so the ContextVar event sink is isolated per request --
concurrent streams never mix.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from typing import Any

from backend.app.agents.events import event_sink


def sse_format(event: dict) -> str:
    return f"event: {event.get('type', 'message')}\ndata: {json.dumps(event, default=str)}\n\n"


async def stream_orchestrator(orchestrator: Any, query: str, session_id: str) -> AsyncIterator[str]:
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def emit(event: dict) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, event)

    def worker() -> None:
        try:
            orchestrator.run_streaming(query, session_id, emit)
        except Exception as exc:  # noqa: BLE001 -- surface failures as a stream event
            emit({"type": "error", "message": str(exc), "session_id": session_id})
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

    task = asyncio.create_task(asyncio.to_thread(worker))
    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            yield sse_format(event)
    finally:
        await task


async def stream_events(body: Callable[[], dict], session_id: str) -> AsyncIterator[str]:
    """Run a blocking ``body`` in a worker thread with the per-request event sink set,
    streaming any events it emits (e.g. an orchestrator's status/tool events) followed by
    a final event carrying ``body``'s return value.

    Reuses the same ContextVar sink + queue + to_thread bridge as ``stream_orchestrator``
    so concurrent streams stay isolated; ``body`` need only call the existing engine /
    orchestrator code, which emits through the module-level event sink.
    """

    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def emit(event: dict) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, event)

    def worker() -> None:
        def tagged(event: dict) -> None:
            event.setdefault("session_id", session_id)
            emit(event)

        token = event_sink.set(tagged)
        try:
            final = body()
            tagged({"type": "final", **final})
        except Exception as exc:  # noqa: BLE001 -- surface failures as a stream event
            tagged({"type": "error", "message": str(exc)})
        finally:
            event_sink.reset(token)
            loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

    task = asyncio.create_task(asyncio.to_thread(worker))
    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            yield sse_format(event)
    finally:
        await task
