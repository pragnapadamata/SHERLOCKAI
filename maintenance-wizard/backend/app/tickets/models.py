"""Ticket and alert data models (pydantic, for clean API serialization later)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class TicketStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketKind(StrEnum):
    ACUTE_ALARM = "acute_alarm"            # an acute anomaly crossing
    PREDICTIVE_ADVISORY = "predictive_advisory"  # an early-warning / RUL sweep
    USER_REQUEST = "user_request"          # explicitly opened by a user


# Legal status transitions (lightweight lifecycle; no SLA/assignment/escalation).
TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.OPEN: {TicketStatus.ACKNOWLEDGED, TicketStatus.IN_PROGRESS, TicketStatus.CLOSED},
    TicketStatus.ACKNOWLEDGED: {TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED},
    TicketStatus.IN_PROGRESS: {TicketStatus.RESOLVED, TicketStatus.CLOSED},
    TicketStatus.RESOLVED: {TicketStatus.CLOSED, TicketStatus.IN_PROGRESS},
    TicketStatus.CLOSED: set(),
}


class TicketUpdate(BaseModel):
    timestamp: str
    note: str
    status: TicketStatus | None = None
    author: str | None = None


class Ticket(BaseModel):
    ticket_id: str
    status: TicketStatus = TicketStatus.OPEN
    severity: Severity
    kind: TicketKind
    equipment_id: str
    title: str
    originating_event: dict = Field(default_factory=dict)
    created_at: str
    updated_at: str
    answer: str = ""                      # the orchestrator's synthesized analysis
    findings: list[dict] = Field(default_factory=list)   # per-specialist compact results
    provenance: list[dict] = Field(default_factory=list)
    recommended_actions: str = ""
    timeline: list[TicketUpdate] = Field(default_factory=list)
    feedback: list[dict] = Field(default_factory=list)


class Alert(BaseModel):
    alert_id: str
    timestamp: str
    equipment_id: str
    severity: Severity
    kind: TicketKind
    message: str
    ticket_id: str | None = None
    anomaly_score: float | None = None
    contributing_channels: list[str] = Field(default_factory=list)
    analysis_summary: str = ""
    acknowledged: bool = False
    audience_roles: list[str] = Field(default_factory=list)


def audience_for(severity: Severity) -> list[str]:
    """Lightweight role-based targeting; the UI filters by role in Phase 7."""

    if severity == Severity.CRITICAL:
        return ["plant_manager", "supervisor", "engineer"]
    if severity == Severity.HIGH:
        return ["supervisor", "engineer"]
    return ["engineer"]
