"""Proactive control endpoint: trigger fires F2 acute; debounced; alert visible."""

from __future__ import annotations


def test_state(client):
    state = client.get("/api/proactive/state").json()
    assert "cursor" in state and state["monitored_assets"]


def test_poll_fires_f2_acute_then_debounces(client):
    r = client.post("/api/proactive/poll",
                    json={"advance_to": "2026-06-02T12:00:00", "equipment_id": "HSM-F2-WRB"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["outcomes"]) == 1
    out = body["outcomes"][0]
    assert out["kind"] == "acute_alarm" and out["equipment_id"] == "HSM-F2-WRB"
    assert body["alerts"] and body["alerts"][0]["severity"] in ("high", "critical")

    # the alert is visible via the poll-based list endpoint
    alerts = client.get("/api/alerts").json()
    assert any(a["alert_id"] == out["alert_id"] for a in alerts)

    # the ticket carries the autonomous analysis
    ticket = client.get(f"/api/tickets/{out['ticket_id']}").json()
    assert ticket["answer"] and ticket["kind"] == "acute_alarm"

    # second poll: debounced, no new outcome
    again = client.post("/api/proactive/poll", json={"equipment_id": "HSM-F2-WRB"})
    assert again.json()["outcomes"] == []


def test_reset_rearms_the_f2_alarm(client):
    fired = client.post("/api/proactive/poll",
                        json={"advance_to": "2026-06-02T12:00:00", "equipment_id": "HSM-F2-WRB"})
    assert len(fired.json()["outcomes"]) == 1

    # debounced until reset
    assert client.post("/api/proactive/poll",
                       json={"equipment_id": "HSM-F2-WRB"}).json()["outcomes"] == []

    state = client.post("/api/proactive/reset").json()
    assert "cursor" in state and state["monitored_assets"]

    # the same planted scenario fires again after the reset (debounce + cursor cleared)
    rearmed = client.post("/api/proactive/poll",
                          json={"advance_to": "2026-06-02T12:00:00", "equipment_id": "HSM-F2-WRB"})
    outcomes = rearmed.json()["outcomes"]
    assert len(outcomes) == 1 and outcomes[0]["kind"] == "acute_alarm"
