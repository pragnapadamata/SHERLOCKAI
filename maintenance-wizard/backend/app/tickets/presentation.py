"""Presentation helpers for autonomous alerts.

The proactive engine stores a raw, code-generated ``message`` on each alert (it is
also fed verbatim into the cached orchestrator query, so it must not change). For
display we instead DERIVE a clean, human headline and a muted technical sub-line
from the structured detection fields -- so the UI always shows readable prose
regardless of what raw text sits in the record. Generic across assets; driven by
the detection result plus the channel mapping in ``core.channels``.
"""

from __future__ import annotations

from backend.app.core.channels import CHANNEL_FAMILY, humanize_drivers
from backend.app.tickets.models import Severity, TicketKind

_SEVERITY_WORD = {
    Severity.CRITICAL: "Critical",
    Severity.HIGH: "High",
    Severity.MEDIUM: "Elevated",
    Severity.LOW: "Low",
}

# Acute-distress phrasing keyed by equipment category (substring match on type).
_DISTRESS = {
    "bearing": "acute bearing distress",
    "gearbox": "acute gear-train distress",
    "gear": "acute gear-train distress",
    "motor": "acute motor distress",
    "pump": "acute pump distress",
}


def _severity_word(severity: object) -> str:
    try:
        return _SEVERITY_WORD.get(Severity(severity), str(severity).title())
    except (ValueError, KeyError):
        return str(severity).title()


def _condition(kind: str, equipment_type: str | None) -> str:
    if kind == TicketKind.ACUTE_ALARM.value:
        type_text = (equipment_type or "").lower()
        for key, phrase in _DISTRESS.items():
            if key in type_text:
                return phrase
        return "an acute anomaly"
    if kind == TicketKind.PREDICTIVE_ADVISORY.value:
        return "an early-warning trend"
    return "an anomaly"


def _trend_clause(channels: list[str]) -> str:
    families = {CHANNEL_FAMILY.get(c) for c in channels}
    temp = "temperature" in families
    vib = "vibration" in families
    if temp and vib:
        return "Temperature and vibration are climbing together."
    if vib:
        return "Vibration is climbing."
    if temp:
        return "Temperature is climbing."
    if "oil" in families:
        return "Oil condition is degrading."
    return "Multiple channels are deviating together."


def _fmt_num(value: float | None) -> str:
    if value is None:
        return ""
    return str(int(value)) if float(value).is_integer() else f"{value:.2f}"


def alert_headline(
    *, equipment_name: str, equipment_type: str | None, severity: object, kind: str, channels: list[str]
) -> str:
    """Clean one-line headline, e.g. 'Critical - <asset>: acute bearing distress. ...'."""

    return (
        f"{_severity_word(severity)}, {equipment_name}: "
        f"{_condition(kind, equipment_type)}. {_trend_clause(channels)}"
    )


def alert_subline(*, anomaly_score: float | None, threshold: float, channels: list[str]) -> str:
    """Muted technical sub-line: score, alarm gate, and humanized drivers."""

    parts: list[str] = []
    if anomaly_score is not None:
        parts.append(f"Anomaly score {_fmt_num(anomaly_score)} (alarm ≥ {_fmt_num(threshold)}).")
    drivers = humanize_drivers(channels)
    if drivers:
        parts.append(f"Drivers: {drivers}.")
    return " ".join(parts)


def autonomous_logbook_text(*, equipment_name: str, kind: str, ticket_id: str) -> str:
    """Clean human summary for the autonomous logbook entry (never raw/degraded text)."""

    return (
        f"Autonomous monitor flagged {_condition(kind, None)} on {equipment_name} "
        f"and opened ticket {ticket_id}."
    )


def alert_view(alert: object, *, equipment: dict | None, threshold: float) -> dict:
    """Serialize an Alert to a dict and attach the derived ``headline``/``subline``."""

    data = alert.model_dump(mode="json")  # type: ignore[attr-defined]
    name = (equipment or {}).get("name") or data.get("equipment_id")
    etype = (equipment or {}).get("type")
    channels = list(data.get("contributing_channels") or [])
    data["headline"] = alert_headline(
        equipment_name=name, equipment_type=etype, severity=data.get("severity"),
        kind=data.get("kind"), channels=channels,
    )
    data["subline"] = alert_subline(
        anomaly_score=data.get("anomaly_score"), threshold=threshold, channels=channels
    )
    return data
