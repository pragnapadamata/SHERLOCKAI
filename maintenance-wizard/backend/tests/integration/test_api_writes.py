"""Write endpoints: feedback, ticket status transitions, alert ack."""

from __future__ import annotations

from backend.app.tickets.models import Severity, TicketKind


def test_post_feedback(client):
    r = client.post("/api/feedback", json={
        "target_type": "fault", "target_id": "F3-GBX-002", "feedback_type": "correction",
        "correction": "Verify the oil sample before ordering.",
    })
    assert r.status_code == 200 and r.json()["feedback_id"].startswith("FB-")


def test_ticket_list_get_and_status_transitions(client, api_system):
    ticket = api_system.ticket_service.create(
        equipment_id="HSM-F2-WRB", severity=Severity.HIGH, kind=TicketKind.ACUTE_ALARM, title="x")
    tid = ticket.ticket_id

    assert any(t["ticket_id"] == tid for t in client.get("/api/tickets").json())
    assert client.get(f"/api/tickets/{tid}").json()["ticket_id"] == tid
    assert client.get("/api/tickets/NOPE").status_code == 404

    ok = client.post(f"/api/tickets/{tid}/status", json={"status": "acknowledged", "note": "seen"})
    assert ok.status_code == 200 and ok.json()["status"] == "acknowledged"

    illegal = client.post(f"/api/tickets/{tid}/status", json={"status": "open"})
    assert illegal.status_code == 409  # acknowledged -> open is not allowed


def test_alert_acknowledge(client, api_system):
    alert = api_system.alert_service.create(
        equipment_id="HSM-F2-WRB", severity=Severity.HIGH, kind=TicketKind.ACUTE_ALARM, message="m")
    assert client.post(f"/api/alerts/{alert.alert_id}/ack").json()["acknowledged"] is True
    assert client.post("/api/alerts/NOPE/ack").status_code == 404
