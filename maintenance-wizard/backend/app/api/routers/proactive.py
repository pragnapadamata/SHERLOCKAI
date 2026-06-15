"""Proactive control: stream state + the controllable trigger (advance + poll).

The poll endpoints are the ONLY things that run the engine (and thus the
orchestrator). There is no continuous background loop. Use equipment_id to fire a
single asset (one orchestrator run) -- token-light for the demo. /poll/stream is the
same single run as /poll, but streams the self-diagnosis live.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.app.api.deps import get_system
from backend.app.api.schemas import PollRequest
from backend.app.api.sse import stream_events
from backend.app.core.config import get_settings
from backend.app.tickets.presentation import alert_view

router = APIRouter(prefix="/api/proactive")

_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


@router.get("/state")
def state(system: Any = Depends(get_system)) -> dict:
    engine = system.engine
    return {
        "cursor": engine.stream.now.isoformat(),
        "end": engine.stream.end.isoformat(),
        "monitored_assets": engine.monitored_assets,
        "last_polled_at": engine.last_polled_at,  # real wall-clock of the last scan
        "server_now": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def _advance_and_poll(system: Any, req: PollRequest) -> dict:
    engine = system.engine
    if req.advance_to:
        engine.stream.advance_to(req.advance_to)
    elif req.steps:
        for _ in range(req.steps):
            engine.stream.advance()

    assets = [req.equipment_id] if req.equipment_id else None
    outcomes = engine.poll(assets=assets)

    alert_map = {a.alert_id: a for a in system.alert_service.list()}
    threshold = get_settings().anomaly_z_threshold
    created_alerts = [
        alert_view(alert_map[o.alert_id],
                   equipment=system.repos.equipment.get(alert_map[o.alert_id].equipment_id),
                   threshold=threshold)
        for o in outcomes if o.alert_id in alert_map
    ]
    return {
        "cursor": engine.stream.now.isoformat(),
        "outcomes": [asdict(o) for o in outcomes],
        "alerts": created_alerts,
    }


@router.post("/poll")
def poll(req: PollRequest, system: Any = Depends(get_system)) -> dict:
    return _advance_and_poll(system, req)


@router.post("/poll/stream")
async def poll_stream(req: PollRequest, system: Any = Depends(get_system)) -> StreamingResponse:
    """Same single run as /poll, but streams the autonomous self-diagnosis live
    (status -> tool events) then a final event carrying the outcomes + alerts. Reuses
    the chat SSE bridge, so no second mechanism and no extra token cost."""

    return StreamingResponse(
        stream_events(lambda: _advance_and_poll(system, req), "proactive"),
        media_type="text/event-stream", headers=_SSE_HEADERS,
    )


@router.post("/reset")
def reset(system: Any = Depends(get_system)) -> dict:
    """Demo/ops control: rewind the replay cursor and clear the per-tier debounce so a
    planted scenario (e.g. the F2 acute alarm) can be re-fired between recording takes.
    Existing tickets and alerts are left intact."""

    system.engine.reset()
    engine = system.engine
    return {
        "cursor": engine.stream.now.isoformat(),
        "end": engine.stream.end.isoformat(),
        "monitored_assets": engine.monitored_assets,
    }
