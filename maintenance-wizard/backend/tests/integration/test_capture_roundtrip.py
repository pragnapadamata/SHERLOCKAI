"""Zero-token dry-run of the capture pipeline: drive the REAL capture functions with a stub
orchestrator, write JSON, load it back, and serve it -- proving capture-key == lookup-key
(the mismatch that would silently cause cache misses on camera) and that the trace replays.
"""

from __future__ import annotations

import json
from dataclasses import replace

from backend.app.agents.contracts import OrchestratorResult
from backend.app.agents.demo_cache import CachedOrchestrator, derive_key, load_demo_cache
from backend.app.agents.events import emit
from backend.app.proactive.engine import COMPREHENSIVE
from backend.scripts import capture_demo_cache as cap


class _StubOrch:
    """Stateless stand-in for the real orchestrator: emits a trace, returns a full result."""

    def run(self, query: str, session_id: str = "default") -> OrchestratorResult:
        for ev in (
            {"type": "status", "message": "Routing and planning"},
            {"type": "tool_start", "tool": "diagnostic"},
            {"type": "tool_end", "tool": "diagnostic", "ok": True, "summary": "stub"},
        ):
            emit(ev)
        return OrchestratorResult(
            answer=f"Stub analysis: {query[:50]}",
            provenance=[{"kind": "record", "table": "fault_catalog", "id": "F2-WRB-001"}],
            specialists_used=["diagnostic", "reporting"],
            findings=[{"role": "diagnostic", "summary": "stub", "key_facts": {}, "provenance": [],
                       "tools_used": ["get_fault_info"], "stop_reason": "completed",
                       "tokens_in": 1, "tokens_out": 1}],
            plan=[], session_id=session_id, iterations=2, stop_reason="completed",
            tokens_in=2, tokens_out=2,
        )


def _run_capture(base) -> None:
    """Replicates capture_demo_cache.main() exactly, but against the stub orchestrator."""

    orch = _StubOrch()
    for i, query in enumerate(cap.CHAT_QUERIES, start=1):
        cap._write(base / "chat" / f"{i}.json", cap._capture(orch, query, f"capture-chat-{i}"))
    for asset in cap.REPORT_ASSETS:
        cap._write(base / "reports" / f"{asset}.json",
                   cap._capture(orch, cap._REPORT_QUERY.format(equipment_id=asset), f"report-{asset}"))
    query = COMPREHENSIVE.format(
        kind=cap.PROACTIVE["kind"], name=cap.PROACTIVE["name"],
        equipment_id=cap.PROACTIVE["equipment_id"],
        timestamp="(captured for demo)", message="Acute anomaly captured for the demo cache.",
    )
    cap._write(base / "proactive" / f"{cap.PROACTIVE['equipment_id']}.json",
               cap._capture(orch, query, "capture-proactive"))


def test_capture_writes_valid_json_with_keys_and_trace(tmp_path):
    _run_capture(tmp_path)
    assert (tmp_path / "chat" / "1.json").is_file()
    assert (tmp_path / "chat" / "2.json").is_file()
    for asset in cap.REPORT_ASSETS:
        assert (tmp_path / "reports" / f"{asset}.json").is_file()
    assert (tmp_path / "proactive" / "HSM-F2-WRB.json").is_file()

    rep = json.loads((tmp_path / "reports" / "HSM-F3-GBX.json").read_text())
    assert rep["key"] == "report:HSM-F3-GBX"
    assert rep["final"]["findings"] and rep["final"]["provenance"]  # non-degraded -> no 503

    pro = json.loads((tmp_path / "proactive" / "HSM-F2-WRB.json").read_text())
    assert pro["key"] == "proactive:HSM-F2-WRB"
    assert any(e["type"] == "tool_start" for e in pro["events"])
    assert all(e["type"] != "final" for e in pro["events"])  # final is stored separately


def test_capture_key_equals_serve_lookup_key(tmp_path):
    _run_capture(tmp_path)
    cache = load_demo_cache(tmp_path)

    # chat: the assistant sends the same string -> same key
    for query in cap.CHAT_QUERIES:
        assert derive_key(query) in cache

    # report: the /api/reports endpoint sends _REPORT_QUERY.format(asset)
    for asset in cap.REPORT_ASSETS:
        assert derive_key(cap._REPORT_QUERY.format(equipment_id=asset)) in cache

    # proactive: the ENGINE builds COMPREHENSIVE with a DIFFERENT timestamp + message at serve
    # time; the key must still match the captured one (keyed by asset, not the varying parts).
    serve_query = COMPREHENSIVE.format(
        kind="acute_alarm", name="F2 finishing stand work-roll bearing",
        equipment_id="HSM-F2-WRB", timestamp="2026-06-02T12:00:00",
        message="Acute anomaly on F2: score 0.97, channels ['vibration_rms'].",
    )
    assert derive_key(serve_query) == "proactive:HSM-F2-WRB"
    assert derive_key(serve_query) in cache


def test_roundtrip_serves_cached_chat_report_and_proactive(tmp_path, api_system):
    from fastapi.testclient import TestClient

    from backend.app.api.app import create_app

    _run_capture(tmp_path)
    cache = load_demo_cache(tmp_path)
    cached = CachedOrchestrator(api_system.orchestrator, cache, delay_ms=0)
    api_system.engine.orchestrator = cached  # mirror container wiring (engine uses the wrapper)
    client = TestClient(create_app(system=replace(api_system, orchestrator=cached)))

    # chat fast-replay
    chat_events: list[dict] = []
    with client.stream("POST", "/api/chat", json={"query": cap.CHAT_QUERIES[0], "session_id": "s"}) as r:
        for line in r.iter_lines():
            if line.startswith("data:"):
                chat_events.append(json.loads(line[len("data:"):].strip()))
    assert any(e["type"] == "tool_start" for e in chat_events)
    finals = [e for e in chat_events if e["type"] == "final"]
    assert finals and finals[0]["answer"].startswith("Stub analysis")

    # report served from cache (200, not the degraded 503)
    rep = client.post("/api/reports", json={"equipment_id": "HSM-F3-GBX"})
    assert rep.status_code == 200 and rep.json()["body"].startswith("Stub analysis")

    # proactive poll/stream: engine fires F2, orchestrator.run hits the cache, trace replays
    pstream: list[dict] = []
    with client.stream("POST", "/api/proactive/poll/stream",
                       json={"advance_to": "2026-06-02T12:00:00", "equipment_id": "HSM-F2-WRB"}) as r:
        for line in r.iter_lines():
            if line.startswith("data:"):
                pstream.append(json.loads(line[len("data:"):].strip()))
    assert any(e["type"] == "tool_start" for e in pstream)
    pfinals = [e for e in pstream if e["type"] == "final"]
    assert pfinals and pfinals[0]["outcomes"]
    assert pfinals[0]["outcomes"][0]["equipment_id"] == "HSM-F2-WRB"


def test_capture_detects_degraded_and_resumes(tmp_path):
    # Degraded forms the capture must refuse to write.
    assert cap._is_degraded({"stop_reason": "llm_error", "findings": [{"a": 1}],
                             "provenance": [{"b": 1}]})
    assert cap._is_degraded({"answer": "x", "findings": [], "provenance": []})
    assert cap._is_degraded({"answer": "I could not complete the request within the step budget.",
                             "findings": [{"a": 1}], "provenance": [{"b": 1}]})
    # A real, grounded result is fine.
    assert not cap._is_degraded({"answer": "ok", "findings": [{"a": 1}], "provenance": [{"b": 1}]})

    # Resumable: a good entry is skipped; a degraded/missing one is not.
    good = tmp_path / "good.json"
    good.write_text('{"final": {"answer": "ok", "findings": [{"r": 1}], "provenance": [{"k": 1}]}}')
    assert cap._already_good(good) is True
    bad = tmp_path / "bad.json"
    bad.write_text('{"final": {"answer": "x", "findings": [], "provenance": []}}')
    assert cap._already_good(bad) is False
    assert cap._already_good(tmp_path / "missing.json") is False
