"""POST /api/chat -- streaming agentic chat (SSE)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.app.api.deps import get_current_user, get_system
from backend.app.api.schemas import ChatRequest
from backend.app.api.sse import stream_orchestrator

router = APIRouter()


@router.post("/api/chat")
async def chat(req: ChatRequest, system: Any = Depends(get_system),
               user: Any = Depends(get_current_user)) -> StreamingResponse:
    session_id = req.session_id or f"chat-{user.user_id}"
    return StreamingResponse(
        stream_orchestrator(system.orchestrator, req.query, session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
