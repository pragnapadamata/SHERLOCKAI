"""Dashboard read endpoints (equipment, priority, sensors). All local, no tokens."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_system

router = APIRouter(prefix="/api/dashboard")


@router.get("/equipment")
def equipment(system: Any = Depends(get_system)) -> list[dict]:
    monitored = set(system.engine.monitored_assets)
    rows = system.repos.equipment.all()
    for row in rows:
        row["monitored"] = row["equipment_id"] in monitored
    return rows


@router.get("/priority")
def priority(system: Any = Depends(get_system)) -> list[dict]:
    result = system.data_registry.get("compute_priority").run()
    return result.get("data") or []


@router.get("/sensors/{equipment_id}")
def sensors(equipment_id: str, last_n: int | None = None, series: bool = False,
            system: Any = Depends(get_system)) -> dict:
    result = system.data_registry.get("get_sensor_data").run(
        equipment_id=equipment_id, last_n=last_n, include_series=series)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error", "no sensor data"))
    return result["data"]


@router.get("/equipment/{equipment_id}")
def equipment_detail(equipment_id: str, system: Any = Depends(get_system)) -> dict:
    asset = system.repos.equipment.get(equipment_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="unknown equipment")
    detail: dict = {"equipment": asset}
    if equipment_id in set(system.engine.monitored_assets):
        sensor_result = system.data_registry.get("get_sensor_data").run(equipment_id=equipment_id)
        detail["sensors"] = sensor_result["data"] if sensor_result.get("ok") else None
    detail["open_tickets"] = [
        t.model_dump(mode="json")
        for t in system.ticket_service.list(equipment_id=equipment_id)
        if t.status not in ("closed", "resolved")
    ]
    detail["logbook"] = system.repos.logbook.query(equipment_id=equipment_id, limit=10)
    return detail
