"""Ticket/alert models, service lifecycle, and tools."""

from __future__ import annotations

import pytest

from backend.app.tickets.models import Severity, TicketKind, TicketStatus, audience_for
from backend.app.tickets.service import AlertService, TicketService
from backend.app.tickets.store import AlertStore, TicketStore
from backend.app.tickets.tools import build_ticket_tools


def _service() -> TicketService:
    return TicketService(TicketStore(), clock=lambda: "2026-06-02T12:00:00", prefix="MW")


def test_create_assigns_sequential_id_and_opens():
    svc = _service()
    t1 = svc.create(equipment_id="HSM-F2-WRB", severity=Severity.CRITICAL,
                    kind=TicketKind.ACUTE_ALARM, title="spike")
    t2 = svc.create(equipment_id="HSM-F3-GBX", severity=Severity.MEDIUM,
                    kind=TicketKind.PREDICTIVE_ADVISORY, title="advisory")
    assert t1.ticket_id == "MW-2026-0001" and t2.ticket_id == "MW-2026-0002"
    assert t1.status == TicketStatus.OPEN
    assert t1.timeline and t1.timeline[0].status == TicketStatus.OPEN


def test_status_transitions_validate():
    svc = _service()
    t = svc.create(equipment_id="HSM-F2-WRB", severity=Severity.HIGH,
                   kind=TicketKind.ACUTE_ALARM, title="x")
    svc.update_status(t.ticket_id, TicketStatus.ACKNOWLEDGED)
    svc.update_status(t.ticket_id, TicketStatus.IN_PROGRESS)
    assert svc.get(t.ticket_id).status == TicketStatus.IN_PROGRESS
    with pytest.raises(ValueError):
        svc.update_status(t.ticket_id, TicketStatus.OPEN)  # illegal backward transition


def test_attach_analysis_and_feedback():
    svc = _service()
    t = svc.create(equipment_id="HSM-F2-WRB", severity=Severity.HIGH,
                   kind=TicketKind.ACUTE_ALARM, title="x")
    svc.attach_analysis(t.ticket_id, answer="A", findings=[{"role": "diagnostic"}],
                        provenance=[{"kind": "record"}], recommended_actions="do X")
    svc.attach_feedback(t.ticket_id, {"feedback_id": "FB-0001", "feedback_type": "confirmation"})
    t = svc.get(t.ticket_id)
    assert t.answer == "A" and t.recommended_actions == "do X"
    assert t.feedback[0]["feedback_id"] == "FB-0001"


def test_alert_audience_from_severity():
    assert "plant_manager" in audience_for(Severity.CRITICAL)
    assert audience_for(Severity.MEDIUM) == ["engineer"]
    svc = AlertService(AlertStore(), clock=lambda: "2026-06-02T12:00:00")
    a = svc.create(equipment_id="HSM-F2-WRB", severity=Severity.CRITICAL,
                   kind=TicketKind.ACUTE_ALARM, message="m")
    assert a.alert_id == "ALERT-0001" and "supervisor" in a.audience_roles


def test_ticket_tools_read_and_guarded_write():
    svc = _service()
    tools = build_ticket_tools(svc)
    created = tools["create_ticket"].run(equipment_id="HSM-F2-WRB", severity="high", title="x")
    tid = created["data"]["ticket_id"]
    got = tools["get_ticket"].run(ticket_id=tid)
    assert got["ok"] and got["data"]["ticket_id"] == tid
    listed = tools["list_tickets"].run(status="open")
    assert any(t["ticket_id"] == tid for t in listed["data"])
    bad = tools["update_ticket"].run(ticket_id=tid, status="closed")
    assert bad["ok"]  # open -> closed is legal
    illegal = tools["update_ticket"].run(ticket_id=tid, status="in_progress")
    assert illegal["ok"] is False  # closed is terminal
