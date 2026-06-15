"""Tickets: queue, detail, status transitions, timeline notes (all deterministic)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_current_user, get_system
from backend.app.api.schemas import TicketStatusUpdate, TimelineNote
from backend.app.tickets.models import TicketStatus

router = APIRouter(prefix="/api/tickets")


@router.get("")
def list_tickets(status: str | None = None, equipment_id: str | None = None,
                 system: Any = Depends(get_system)) -> list[dict]:
    return [t.model_dump(mode="json")
            for t in system.ticket_service.list(status=status, equipment_id=equipment_id)]


@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, system: Any = Depends(get_system)) -> dict:
    ticket = system.ticket_service.get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="unknown ticket")
    return ticket.model_dump(mode="json")


@router.post("/{ticket_id}/status")
def update_status(ticket_id: str, body: TicketStatusUpdate, system: Any = Depends(get_system),
                  user: Any = Depends(get_current_user)) -> dict:
    try:
        ticket = system.ticket_service.update_status(
            ticket_id, TicketStatus(body.status), note=body.note, author=user.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ticket.model_dump(mode="json")


@router.post("/{ticket_id}/timeline")
def add_timeline(ticket_id: str, body: TimelineNote, system: Any = Depends(get_system),
                 user: Any = Depends(get_current_user)) -> dict:
    try:
        ticket = system.ticket_service.add_timeline(ticket_id, body.note, author=user.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ticket.model_dump(mode="json")
