"""Request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    session_id: str | None = None


class FeedbackRequest(BaseModel):
    target_type: str
    feedback_type: str
    target_id: str | None = None
    rating: int | None = None
    correction: str | None = None
    author_user_id: str | None = None
    notes: str | None = None


class TicketStatusUpdate(BaseModel):
    status: str
    note: str | None = None


class TimelineNote(BaseModel):
    note: str


class ReportRequest(BaseModel):
    equipment_id: str


class PollRequest(BaseModel):
    advance_to: str | None = None
    steps: int | None = None
    equipment_id: str | None = None


class Report(BaseModel):
    equipment_id: str
    generated_at: str
    title: str
    body: str
    sections: list[dict] = []
    provenance: list[dict] = []
    specialists_used: list[str] = []
    tokens_in: int = 0
    tokens_out: int = 0


class UserOut(BaseModel):
    user_id: str
    name: str
    role: str
    area: str
