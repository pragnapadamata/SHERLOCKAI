"""Ticket and alert services: deterministic create/update over the stores."""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime

from backend.app.tickets.models import (
    TRANSITIONS,
    Alert,
    Severity,
    Ticket,
    TicketKind,
    TicketStatus,
    TicketUpdate,
    audience_for,
)
from backend.app.tickets.store import AlertStore, TicketStore


def _default_clock() -> str:
    return datetime.now().isoformat(timespec="seconds")


class TicketService:
    def __init__(self, store: TicketStore, clock: Callable[[], str] | None = None,
                 prefix: str = "MW") -> None:
        self._store = store
        self._clock = clock or _default_clock
        self._prefix = prefix
        # Serializes id allocation (count()+1) with the insert, so two concurrent creates
        # cannot derive the same ticket id and clobber each other.
        self._lock = threading.Lock()

    def _next_id(self) -> str:
        year = self._clock()[:4]
        return f"{self._prefix}-{year}-{self._store.count() + 1:04d}"

    def create(self, *, equipment_id: str, severity: Severity, kind: TicketKind, title: str,
               originating_event: dict | None = None, answer: str = "",
               findings: list[dict] | None = None, provenance: list[dict] | None = None,
               recommended_actions: str = "", author: str | None = None) -> Ticket:
        with self._lock:
            now = self._clock()
            ticket = Ticket(
                ticket_id=self._next_id(), status=TicketStatus.OPEN, severity=severity, kind=kind,
                equipment_id=equipment_id, title=title, originating_event=originating_event or {},
                created_at=now, updated_at=now, answer=answer, findings=findings or [],
                provenance=provenance or [], recommended_actions=recommended_actions,
                timeline=[TicketUpdate(timestamp=now, note="Ticket opened", status=TicketStatus.OPEN,
                                       author=author)],
            )
            return self._store.add(ticket)

    def get(self, ticket_id: str) -> Ticket | None:
        return self._store.get(ticket_id)

    def list(self, status: str | None = None, equipment_id: str | None = None) -> list[Ticket]:
        tickets = self._store.all()
        if status:
            tickets = [t for t in tickets if t.status == status]
        if equipment_id:
            tickets = [t for t in tickets if t.equipment_id == equipment_id]
        return sorted(tickets, key=lambda t: t.ticket_id)

    def _require(self, ticket_id: str) -> Ticket:
        ticket = self._store.get(ticket_id)
        if ticket is None:
            raise ValueError(f"Unknown ticket {ticket_id!r}.")
        return ticket

    def update_status(self, ticket_id: str, status: TicketStatus, note: str | None = None,
                      author: str | None = None) -> Ticket:
        ticket = self._require(ticket_id)
        status = TicketStatus(status)
        if status not in TRANSITIONS[ticket.status]:
            raise ValueError(f"Illegal transition {ticket.status} -> {status}.")
        now = self._clock()
        ticket.status = status
        ticket.updated_at = now
        ticket.timeline.append(TicketUpdate(
            timestamp=now, note=note or f"Status -> {status}", status=status, author=author))
        return ticket

    def add_timeline(self, ticket_id: str, note: str, author: str | None = None) -> Ticket:
        ticket = self._require(ticket_id)
        now = self._clock()
        ticket.updated_at = now
        ticket.timeline.append(TicketUpdate(timestamp=now, note=note, author=author))
        return ticket

    def attach_analysis(self, ticket_id: str, *, answer: str, findings: list[dict],
                        provenance: list[dict], recommended_actions: str) -> Ticket:
        ticket = self._require(ticket_id)
        ticket.answer = answer
        ticket.findings = findings
        ticket.provenance = provenance
        ticket.recommended_actions = recommended_actions
        return self.add_timeline(ticket_id, "Autonomous analysis attached.", author="U-SYS-AMDC")

    def attach_feedback(self, ticket_id: str, feedback: dict) -> Ticket:
        ticket = self._require(ticket_id)
        ticket.feedback.append(feedback)
        return self.add_timeline(ticket_id, "Feedback recorded.", author=feedback.get("author_user_id"))


class AlertService:
    def __init__(self, store: AlertStore, clock: Callable[[], str] | None = None) -> None:
        self._store = store
        self._clock = clock or _default_clock
        # Serializes id allocation (count()+1) with the insert against concurrent creates.
        self._lock = threading.Lock()

    def _next_id(self) -> str:
        return f"ALERT-{self._store.count() + 1:04d}"

    def create(self, *, equipment_id: str, severity: Severity, kind: TicketKind, message: str,
               ticket_id: str | None = None, anomaly_score: float | None = None,
               contributing_channels: list[str] | None = None, analysis_summary: str = "") -> Alert:
        with self._lock:
            alert = Alert(
                alert_id=self._next_id(), timestamp=self._clock(), equipment_id=equipment_id,
                severity=severity, kind=kind, message=message, ticket_id=ticket_id,
                anomaly_score=anomaly_score, contributing_channels=contributing_channels or [],
                analysis_summary=analysis_summary, audience_roles=audience_for(severity),
            )
            return self._store.add(alert)

    def acknowledge(self, alert_id: str) -> Alert | None:
        alert = self._store.get(alert_id)
        if alert:
            alert.acknowledged = True
        return alert

    def list(self) -> list[Alert]:
        return sorted(self._store.all(), key=lambda a: a.alert_id)
