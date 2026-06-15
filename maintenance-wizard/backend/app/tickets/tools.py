"""Ticket tools. Read tools (get/list) may be exposed to the orchestrator; the
create/update tools exist for completeness/tests but ticket writes in the running
system are always deterministic (engine + orchestrator service calls), never
LLM-driven (Q4)."""

from __future__ import annotations

from typing import Any, ClassVar

from backend.app.tickets.models import Severity, TicketKind, TicketStatus
from backend.app.tickets.service import TicketService
from backend.app.tools.results import DataTool, ExpectedToolError, SourceRef, ToolResult


def _ref(ticket_id: str, equipment_id: str | None = None) -> SourceRef:
    return SourceRef.record(table="tickets", id=ticket_id, equipment_id=equipment_id)


class GetTicketTool(DataTool):
    name: ClassVar[str] = "get_ticket"
    description: ClassVar[str] = "Fetch one maintenance ticket by its id (e.g. MW-2026-0001)."
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {"ticket_id": {"type": "string", "description": "Ticket id."}},
        "required": ["ticket_id"],
        "additionalProperties": False,
    }

    def __init__(self, service: TicketService) -> None:
        self._svc = service

    def execute(self, ticket_id: str) -> ToolResult:
        ticket = self._svc.get(ticket_id)
        if ticket is None:
            raise ExpectedToolError(f"Unknown ticket {ticket_id!r}.")
        return ToolResult(tool=self.name, data=ticket.model_dump(mode="json"),
                          sources=[_ref(ticket.ticket_id, ticket.equipment_id)],
                          summary=f"{ticket.ticket_id}: {ticket.status} ({ticket.severity})")


class ListTicketsTool(DataTool):
    name: ClassVar[str] = "list_tickets"
    description: ClassVar[str] = "List maintenance tickets, optionally by status or equipment."
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Filter by status (open, acknowledged, ...)."},
            "equipment_id": {"type": "string", "description": "Filter by asset."},
        },
        "additionalProperties": False,
    }

    def __init__(self, service: TicketService) -> None:
        self._svc = service

    def execute(self, status: str | None = None, equipment_id: str | None = None) -> ToolResult:
        tickets = self._svc.list(status=status, equipment_id=equipment_id)
        data = [t.model_dump(mode="json") for t in tickets]
        return ToolResult(tool=self.name, data=data,
                          sources=[_ref(t.ticket_id, t.equipment_id) for t in tickets],
                          summary=f"{len(tickets)} ticket(s)")


class CreateTicketTool(DataTool):
    name: ClassVar[str] = "create_ticket"
    description: ClassVar[str] = "Open a maintenance ticket for an asset (deterministic helper)."
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string"},
            "severity": {"type": "string", "enum": [s.value for s in Severity]},
            "title": {"type": "string"},
        },
        "required": ["equipment_id", "severity", "title"],
        "additionalProperties": False,
    }

    def __init__(self, service: TicketService) -> None:
        self._svc = service

    def execute(self, equipment_id: str, severity: str, title: str) -> ToolResult:
        try:
            ticket = self._svc.create(equipment_id=equipment_id, severity=Severity(severity),
                                      kind=TicketKind.USER_REQUEST, title=title)
        except ValueError as exc:
            raise ExpectedToolError(str(exc)) from exc
        return ToolResult(tool=self.name, data=ticket.model_dump(mode="json"),
                          sources=[_ref(ticket.ticket_id, equipment_id)],
                          summary=f"Opened {ticket.ticket_id}")


class UpdateTicketTool(DataTool):
    name: ClassVar[str] = "update_ticket"
    description: ClassVar[str] = "Update a ticket's status (open -> acknowledged -> ... -> closed)."
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "ticket_id": {"type": "string"},
            "status": {"type": "string", "enum": [s.value for s in TicketStatus]},
            "note": {"type": "string"},
        },
        "required": ["ticket_id", "status"],
        "additionalProperties": False,
    }

    def __init__(self, service: TicketService) -> None:
        self._svc = service

    def execute(self, ticket_id: str, status: str, note: str | None = None) -> ToolResult:
        try:
            ticket = self._svc.update_status(ticket_id, TicketStatus(status), note=note)
        except ValueError as exc:
            raise ExpectedToolError(str(exc)) from exc
        return ToolResult(tool=self.name, data=ticket.model_dump(mode="json"),
                          sources=[_ref(ticket.ticket_id, ticket.equipment_id)],
                          summary=f"{ticket.ticket_id} -> {ticket.status}")


def build_ticket_tools(service: TicketService) -> dict[str, DataTool]:
    return {
        "get_ticket": GetTicketTool(service),
        "list_tickets": ListTicketsTool(service),
        "create_ticket": CreateTicketTool(service),
        "update_ticket": UpdateTicketTool(service),
    }
