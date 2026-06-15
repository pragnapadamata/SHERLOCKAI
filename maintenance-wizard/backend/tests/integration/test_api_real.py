"""Real-LLM chat SSE end-to-end through the API (slow; deselected; quota-aware)."""

from __future__ import annotations

import json

import pytest


@pytest.mark.slow
def test_real_chat_sse_streams_grounded_answer():
    from fastapi.testclient import TestClient

    from backend.app.api.app import create_app

    client = TestClient(create_app())  # real system, built lazily on first request
    with client.stream("POST", "/api/chat", json={
        "query": "What's the status of the F3 main drive gearbox?", "session_id": "real",
    }) as response:
        events = [json.loads(line[len("data:"):].strip())
                  for line in response.iter_lines() if line.startswith("data:")]

    finals = [e for e in events if e["type"] == "final"]
    assert finals and finals[0]["answer"]
    assert any(e["type"] == "tool_start" for e in events)  # live agent trace streamed
