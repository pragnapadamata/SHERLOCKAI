"""Alerts: list (poll-based) and acknowledge. The UI tracks seen ids to fire once."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_system
from backend.app.core.config import get_settings
from backend.app.tickets.presentation import alert_view

router = APIRouter(prefix="/api/alerts")


def _view(system: Any, alert: Any) -> dict:
    """Serialize with a clean, derived headline/subline (never the raw message)."""

    equipment = system.repos.equipment.get(alert.equipment_id)
    return alert_view(alert, equipment=equipment, threshold=get_settings().anomaly_z_threshold)


@router.get("")
def list_alerts(unacknowledged: bool = False, equipment_id: str | None = None,
                system: Any = Depends(get_system)) -> list[dict]:
    alerts = system.alert_service.list()
    if unacknowledged:
        alerts = [a for a in alerts if not a.acknowledged]
    if equipment_id:
        alerts = [a for a in alerts if a.equipment_id == equipment_id]
    return [_view(system, a) for a in alerts]


@router.post("/{alert_id}/ack")
def acknowledge(alert_id: str, system: Any = Depends(get_system)) -> dict:
    alert = system.alert_service.acknowledge(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="unknown alert")
    return _view(system, alert)
