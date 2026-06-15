"""Chat SSE: the agentic process streams live, then the final cited answer."""

from __future__ import annotations

import json


def _read_events(client, payload):
    events = []
    with client.stream("POST", "/api/chat", json=payload) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:"):].strip()))
    return events


def test_chat_streams_progress_then_final(client):
    events = _read_events(client, {"query": "What's wrong with the F2 bearing?", "session_id": "s1"})
    types = [e["type"] for e in events]

    assert "status" in types
    assert "tool_start" in types
    assert any(e.get("tool") == "diagnostic" for e in events if e["type"] == "tool_start")
    assert any(e.get("tool") == "get_fault_info" for e in events if e["type"] == "tool_start")

    finals = [e for e in events if e["type"] == "final"]
    assert len(finals) == 1
    final = finals[0]
    assert final["session_id"] == "s1"
    assert "F2-WRB-001" in final["answer"]
    assert final["provenance"]
    assert "diagnostic" in final["specialists_used"]


def test_every_event_is_tagged_with_session(client):
    events = _read_events(client, {"query": "status?", "session_id": "tagme"})
    assert events and all(e.get("session_id") == "tagme" for e in events)
