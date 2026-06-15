"""Stretch: POST /api/proactive/poll/stream streams the live self-diagnosis then the
outcome -- reusing the same scripted-orchestrator path as the chat SSE test, zero tokens."""

from __future__ import annotations

import json


def _read_events(client, payload):
    events = []
    with client.stream("POST", "/api/proactive/poll/stream", json=payload) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:"):].strip()))
    return events


def test_poll_stream_emits_live_trace_then_outcome(client):
    events = _read_events(
        client, {"advance_to": "2026-06-02T12:00:00", "equipment_id": "HSM-F2-WRB"}
    )
    types = [e["type"] for e in events]

    # the autonomous run streams its tool calls live (same event shape as chat)
    assert "tool_start" in types
    assert any(e.get("tool") == "diagnostic" for e in events if e["type"] == "tool_start")

    # exactly one final, carrying the fired outcome + alert
    finals = [e for e in events if e["type"] == "final"]
    assert len(finals) == 1
    final = finals[0]
    assert final["outcomes"] and final["outcomes"][0]["equipment_id"] == "HSM-F2-WRB"
    assert final["outcomes"][0]["kind"] == "acute_alarm"
    assert final["alerts"]

    # every event is tagged with the stream's session id (isolation)
    assert all(e.get("session_id") == "proactive" for e in events)
