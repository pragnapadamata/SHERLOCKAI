"""Concurrency: per-request SSE isolation + thread-safe DB under concurrent reads."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace

import httpx

from backend.app.api.app import create_app
from backend.app.conversation.memory import ConversationMemory
from backend.tests.fakes import build_constant_orchestrator


async def _collect(client, session_id):
    events = []
    async with client.stream("POST", "/api/chat",
                             json={"query": "hi", "session_id": session_id}) as response:
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:"):].strip()))
    return events


async def test_two_concurrent_chat_streams_do_not_cross_contaminate(api_system, ml_registry):
    # Constant orchestrator -> each run emits a couple of events, deterministically.
    system = replace(
        api_system,
        orchestrator=build_constant_orchestrator(ml_registry, ConversationMemory(clock=lambda: "t")),
    )
    transport = httpx.ASGITransport(app=create_app(system=system))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        a, b = await asyncio.gather(_collect(client, "AAA"), _collect(client, "BBB"))

    assert a and b
    assert all(e.get("session_id") == "AAA" for e in a), a   # no event from B leaked into A
    assert all(e.get("session_id") == "BBB" for e in b), b
    assert any(e["type"] == "final" for e in a)
    assert any(e["type"] == "final" for e in b)


async def test_concurrent_reads_are_thread_safe(api_system):
    transport = httpx.ASGITransport(app=create_app(system=api_system))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        results = await asyncio.gather(
            *[client.get("/api/dashboard/equipment") for _ in range(15)]
        )
    assert all(r.status_code == 200 for r in results)  # no "SQLite objects ... same thread" errors
