"""record_feedback -- store a user correction, confirmation, or rating.

Feeds the Phase-later feedback-conditioned retrieval loop. Phase 2 only persists
the feedback; re-injection into retrieval is a later phase.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar

from backend.app.data_access.repositories import Repositories
from backend.app.tools.results import (
    DataTool,
    ExpectedToolError,
    SourceRef,
    ToolResult,
    default_clock,
)

_FEEDBACK_TYPES = ["confirmation", "correction", "rating"]


class RecordFeedbackTool(DataTool):
    name: ClassVar[str] = "record_feedback"
    description: ClassVar[str] = (
        "Record engineer feedback on a system output (a confirmation, a correction, "
        "or a 1-5 rating), so future recommendations can improve."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "target_type": {
                "type": "string",
                "description": "What the feedback concerns, e.g. diagnosis, recommendation, fault.",
            },
            "feedback_type": {"type": "string", "enum": _FEEDBACK_TYPES, "description": "Kind of feedback."},
            "target_id": {"type": "string", "description": "Id of the thing being rated, if any."},
            "rating": {"type": "integer", "description": "1-5 rating (for feedback_type=rating)."},
            "correction": {"type": "string", "description": "The corrected statement (for corrections)."},
            "author_user_id": {"type": "string", "description": "Authoring user id."},
            "notes": {"type": "string", "description": "Free-text notes."},
        },
        "required": ["target_type", "feedback_type"],
        "additionalProperties": False,
    }

    def __init__(self, repos: Repositories, clock: Callable[[], str] | None = None) -> None:
        self._repos = repos
        self._clock = clock or default_clock

    def execute(self, target_type: str, feedback_type: str, target_id: str | None = None,
                rating: int | None = None, correction: str | None = None,
                author_user_id: str | None = None, notes: str | None = None) -> ToolResult:
        if feedback_type not in _FEEDBACK_TYPES:
            raise ExpectedToolError(f"feedback_type must be one of {_FEEDBACK_TYPES}.")
        if feedback_type == "rating" and rating is None:
            raise ExpectedToolError("rating is required when feedback_type is 'rating'.")
        if rating is not None and not (1 <= int(rating) <= 5):
            raise ExpectedToolError("rating must be between 1 and 5.")
        if author_user_id and not self._repos.users.get(author_user_id):
            raise ExpectedToolError(f"Unknown author_user_id {author_user_id!r}.")

        record = self._repos.feedback.append(
            target_type=target_type, target_id=target_id, feedback_type=feedback_type,
            rating=rating, correction=correction, author_user_id=author_user_id,
            notes=notes, created_at=self._clock(),
        )
        return ToolResult(
            tool=self.name, data=record,
            sources=[SourceRef.record(table="feedback", id=record["feedback_id"])],
            summary=f"Recorded {record['feedback_id']} ({feedback_type} on {target_type})",
        )
