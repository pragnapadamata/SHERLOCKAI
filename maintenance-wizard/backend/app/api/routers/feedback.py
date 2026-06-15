"""POST /api/feedback -- record feedback (feeds feedback-conditioned retrieval)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_current_user, get_system
from backend.app.api.schemas import FeedbackRequest

router = APIRouter()


@router.post("/api/feedback")
def submit_feedback(req: FeedbackRequest, system: Any = Depends(get_system),
                    user: Any = Depends(get_current_user)) -> dict:
    result = system.data_registry.get("record_feedback").run(
        target_type=req.target_type, feedback_type=req.feedback_type, target_id=req.target_id,
        rating=req.rating, correction=req.correction,
        author_user_id=req.author_user_id or user.user_id, notes=req.notes,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "invalid feedback"))
    record = result["data"]
    if req.target_type == "ticket" and req.target_id:
        try:
            system.ticket_service.attach_feedback(req.target_id, record)
        except ValueError:
            pass  # unknown ticket -> feedback still recorded
    return record
