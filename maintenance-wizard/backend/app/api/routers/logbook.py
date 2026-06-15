"""GET /api/logbook -- digital logbook entries (incl. autonomous system entries)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from backend.app.api.deps import get_system

router = APIRouter()


@router.get("/api/logbook")
def logbook(equipment_id: str | None = None, limit: int = 50,
            system: Any = Depends(get_system)) -> list[dict]:
    return system.repos.logbook.query(equipment_id=equipment_id, limit=limit)
