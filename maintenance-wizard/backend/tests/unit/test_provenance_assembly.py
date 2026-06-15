"""Provenance harvest + dedup from mixed specialist and data-tool results."""

from __future__ import annotations

from backend.app.agents.provenance import dedup, harvest, sources_from_result
from backend.app.agents.schemas import ToolInvocation


def test_sources_from_specialist_and_data_results():
    specialist = {"provenance": [{"kind": "document", "doc_id": "M", "section": "S"}]}
    data = {"sources": [{"kind": "record", "table": "t", "id": "1"}]}
    assert sources_from_result(specialist)[0]["doc_id"] == "M"
    assert sources_from_result(data)[0]["table"] == "t"
    assert sources_from_result("not a dict") == []


def test_harvest_and_dedup_collapses_duplicates():
    invocations = [
        ToolInvocation(tool="diagnostic", arguments={}, ok=True, result={"provenance": [
            {"kind": "document", "doc_id": "M", "section": "S"},
            {"kind": "record", "table": "t", "id": "1"},
        ]}),
        ToolInvocation(tool="get_spare_parts", arguments={}, ok=True, result={"sources": [
            {"kind": "record", "table": "t", "id": "1"},  # duplicate of above
            {"kind": "computation", "method": "m", "model": "HGB"},
        ]}),
    ]
    refs = dedup(harvest(invocations))
    keys = {(r["kind"], r.get("doc_id"), r.get("table"), r.get("model")) for r in refs}
    assert len(refs) == 3  # the duplicate record collapsed
    assert ("computation", None, None, "HGB") in keys


def test_failed_invocations_are_ignored():
    invocations = [ToolInvocation(tool="x", arguments={}, ok=False, error="boom")]
    assert harvest(invocations) == []
