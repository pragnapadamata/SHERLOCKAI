"""Demo cache: key derivation, fast-replay, and serving cached chat/reports via the API.

Zero tokens: a hand-built cache wraps the scripted orchestrator; cache hits never touch
the inner orchestrator, and delay_ms=0 keeps replay instant.
"""

from __future__ import annotations

import json
from dataclasses import replace

from backend.app.agents.contracts import OrchestratorResult
from backend.app.agents.demo_cache import CachedOrchestrator, derive_key, normalize_key


def _entry(key: str, answer: str = "CACHED ANSWER") -> dict:
    return {
        "key": key,
        "query": "captured",
        "events": [
            {"type": "status", "message": "Routing and planning"},
            {"type": "tool_start", "tool": "diagnostic"},
            {"type": "tool_end", "tool": "diagnostic", "ok": True, "summary": "done"},
        ],
        "final": {
            "answer": answer,
            "provenance": [{"kind": "record", "table": "fault_catalog", "id": "F2-WRB-001"}],
            "specialists_used": ["diagnostic", "reporting"],
            "findings": [{"role": "diagnostic", "summary": "s", "key_facts": {}, "provenance": []}],
            "plan": [],
            "session_id": "capture",
            "iterations": 2,
            "stop_reason": "completed",
            "tokens_in": 5,
            "tokens_out": 5,
        },
    }


def test_key_derivation_and_normalization():
    # Punctuation (incl. the apostrophe) is removed so a lightly reworded question still hits.
    assert normalize_key("  What's   the STATUS?? ") == "whats the status"
    assert derive_key("What is wrong with the gearbox?").startswith("chat:")
    assert derive_key("Generate a structured maintenance report for HSM-F3-GBX: x") == "report:HSM-F3-GBX"
    assert derive_key("AUTONOMOUS ALERT -- acute_alarm on F2 (HSM-F2-WRB) at t. m") == "proactive:HSM-F2-WRB"


def test_run_streaming_fast_replays_trace_then_final():
    key = derive_key("hello there")

    class _Inner:  # must not be reached on a cache hit
        def run_streaming(self, *a):
            raise AssertionError("inner called on hit")

    co = CachedOrchestrator(_Inner(), {key: _entry(key)}, delay_ms=0)
    emitted: list[dict] = []
    result = co.run_streaming("Hello there!", "sess", emitted.append)

    assert [e["type"] for e in emitted] == ["status", "tool_start", "tool_end", "final"]
    assert all(e["session_id"] == "sess" for e in emitted)
    assert emitted[-1]["answer"] == "CACHED ANSWER"
    assert result.answer == "CACHED ANSWER"


def test_run_miss_delegates_to_inner():
    class _Live:
        def run(self, query, session_id="default"):
            return OrchestratorResult(answer="LIVE")

    co = CachedOrchestrator(_Live(), {}, delay_ms=0)
    assert co.run("an uncached question", "s").answer == "LIVE"


def test_api_serves_cached_chat_and_report(api_system):
    from fastapi.testclient import TestClient

    from backend.app.api.app import create_app

    chat_q = "What is going on with F3?"
    cache = {
        derive_key(chat_q): _entry(derive_key(chat_q)),
        "report:HSM-F2-WRB": _entry("report:HSM-F2-WRB"),
    }
    system = replace(
        api_system, orchestrator=CachedOrchestrator(api_system.orchestrator, cache, delay_ms=0)
    )
    client = TestClient(create_app(system=system))

    events: list[dict] = []
    with client.stream("POST", "/api/chat", json={"query": chat_q, "session_id": "s"}) as r:
        for line in r.iter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:"):].strip()))
    assert any(e["type"] == "tool_start" for e in events)
    finals = [e for e in events if e["type"] == "final"]
    assert finals and finals[0]["answer"] == "CACHED ANSWER"

    rep = client.post("/api/reports", json={"equipment_id": "HSM-F2-WRB"})
    assert rep.status_code == 200 and rep.json()["body"] == "CACHED ANSWER"
