"""In-process ticket and alert stores (behind simple interfaces for the API phase).

Each store guards its dict with a per-store ``threading.Lock`` so concurrent writes (the
API threadpool, the proactive engine) cannot corrupt it or race a snapshot read. ID
allocation is made atomic one level up, in the services (see ``service.py``)."""

from __future__ import annotations

import threading

from backend.app.tickets.models import Alert, Ticket


class TicketStore:
    def __init__(self) -> None:
        self._tickets: dict[str, Ticket] = {}
        self._lock = threading.Lock()

    def add(self, ticket: Ticket) -> Ticket:
        with self._lock:
            self._tickets[ticket.ticket_id] = ticket
            return ticket

    def get(self, ticket_id: str) -> Ticket | None:
        return self._tickets.get(ticket_id)

    def all(self) -> list[Ticket]:
        with self._lock:
            return list(self._tickets.values())

    def count(self) -> int:
        with self._lock:
            return len(self._tickets)


class AlertStore:
    def __init__(self) -> None:
        self._alerts: dict[str, Alert] = {}
        self._lock = threading.Lock()

    def add(self, alert: Alert) -> Alert:
        with self._lock:
            self._alerts[alert.alert_id] = alert
            return alert

    def get(self, alert_id: str) -> Alert | None:
        return self._alerts.get(alert_id)

    def all(self) -> list[Alert]:
        with self._lock:
            return list(self._alerts.values())

    def count(self) -> int:
        with self._lock:
            return len(self._alerts)
