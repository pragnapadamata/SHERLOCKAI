"""Report endpoint: structured report assembled from the orchestrator findings."""

from __future__ import annotations


def test_generate_report(client):
    r = client.post("/api/reports", json={"equipment_id": "HSM-F2-WRB"})
    assert r.status_code == 200
    body = r.json()
    assert body["equipment_id"] == "HSM-F2-WRB"
    assert body["body"]  # the synthesized analysis
    assert body["sections"] and body["sections"][0]["role"]  # per-specialist sections
    assert body["provenance"]


def test_degraded_report_returns_503(api_system):
    from dataclasses import replace

    from fastapi.testclient import TestClient

    from backend.app.agents.contracts import OrchestratorResult
    from backend.app.api.app import create_app

    class _Empty:  # mimics the loop degrading on a quota 429: no findings, no provenance
        def run(self, query, session_id="default"):
            return OrchestratorResult(answer="")

    client = TestClient(create_app(system=replace(api_system, orchestrator=_Empty())))
    r = client.post("/api/reports", json={"equipment_id": "HSM-F2-WRB"})
    assert r.status_code == 503
    assert "could not be generated" in r.json()["detail"].lower()
