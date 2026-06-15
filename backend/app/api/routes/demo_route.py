from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.live_sensor import (
    get_live_readings,
    get_live_events,
    get_live_kpi_deltas,
    inject_demo_alert,
)

router = APIRouter()


@router.get("/readings")
async def live_readings():
    """Current live sensor readings for all units."""
    return get_live_readings()


@router.get("/events")
async def live_events():
    """Last 20 live events — alerts, threshold breaches, anomalies."""
    return {"events": get_live_events()}


@router.get("/kpi-deltas")
async def live_kpi_deltas():
    """Live KPI values with delta vs baseline."""
    return get_live_kpi_deltas()


class AlertInjectRequest(BaseModel):
    plant:      Optional[str] = "Plant-A"
    alert_type: Optional[str] = "CRITICAL_FAILURE"


@router.post("/inject-alert")
async def inject_alert(req: AlertInjectRequest):
    """
    🔴 Demo endpoint — inject a dramatic alert for live presentation.
    alert_type options:
      CRITICAL_FAILURE  — equipment shutdown required
      GAS_LEAK          — coke oven gas leak
      ENERGY_SURGE      — abnormal energy consumption
      PRODUCTION_HALT   — rolling mill stoppage
    """
    event = inject_demo_alert(plant=req.plant, alert_type=req.alert_type)
    return {"injected": True, "event": event}


@router.get("/alert-types")
async def alert_types():
    return {
        "types": [
            {"id": "CRITICAL_FAILURE",  "label": "⚙️  Critical Equipment Failure", "severity": "CRITICAL"},
            {"id": "GAS_LEAK",          "label": "☣️  Gas Leak Detection",          "severity": "CRITICAL"},
            {"id": "ENERGY_SURGE",      "label": "⚡ Energy Consumption Surge",     "severity": "HIGH"},
            {"id": "PRODUCTION_HALT",   "label": "🏭 Production Stoppage",          "severity": "HIGH"},
        ]
    }
