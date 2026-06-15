"""Uniform tool-result envelope with explainable provenance.

Every Phase 2 tool returns a ``ToolResult`` carrying its data plus ``sources``
(document citations, record ids, sensor windows, or computation notes) and, for
scored tools, a ``components`` breakdown. ``DataTool`` standardizes serialization
and turns expected failures into ``ok=False`` results (unexpected exceptions
still propagate to the agent loop's catch).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from backend.app.tools.base import Tool


def default_clock() -> str:
    """Wall-clock ISO timestamp for write tools. Tests inject a fixed clock."""

    return datetime.now().isoformat(timespec="seconds")


class SourceRef(BaseModel):
    """One provenance item. ``kind`` selects which fields are meaningful."""

    kind: Literal["document", "record", "sensor", "computation"]
    # document
    doc_id: str | None = None
    doc_type: str | None = None
    source: str | None = None
    section: str | None = None
    equipment_id: str | None = None
    score: float | None = None
    # record
    table: str | None = None
    id: str | None = None
    # sensor
    window: dict | None = None
    n_samples: int | None = None
    # computation
    method: str | None = None
    detail: str | None = None
    model: str | None = None
    drivers: list[str] | None = None

    @classmethod
    def document(cls, *, doc_id, source, section, equipment_id=None, doc_type=None,
                 score=None) -> SourceRef:
        return cls(kind="document", doc_id=doc_id, source=source, section=section,
                   equipment_id=equipment_id, doc_type=doc_type, score=score)

    @classmethod
    def record(cls, *, table: str, id: str, equipment_id: str | None = None) -> SourceRef:
        return cls(kind="record", table=table, id=id, equipment_id=equipment_id)

    @classmethod
    def sensor(cls, *, source: str, equipment_id: str, window: dict, n_samples: int) -> SourceRef:
        return cls(kind="sensor", source=source, equipment_id=equipment_id,
                   window=window, n_samples=n_samples)

    @classmethod
    def computation(cls, *, method: str, detail: str | None = None,
                    model: str | None = None, drivers: list[str] | None = None) -> SourceRef:
        return cls(kind="computation", method=method, detail=detail, model=model, drivers=drivers)


class ScoreComponent(BaseModel):
    """One term of a transparent computed score (e.g. priority)."""

    dimension: str
    raw_value: str | float
    normalized: float
    weight: float
    contribution: float


class ToolResult(BaseModel):
    tool: str
    ok: bool = True
    summary: str | None = None
    data: Any = None
    sources: list[SourceRef] = []
    components: list[ScoreComponent] | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return self.model_dump(mode="json", exclude_none=True)


class ExpectedToolError(Exception):
    """A handled, user-facing tool failure (e.g. unknown id, empty result)."""


class DataTool(Tool):
    """Base for substrate tools: implement ``execute`` returning a ``ToolResult``."""

    def execute(self, **kwargs: Any) -> ToolResult:  # pragma: no cover - overridden
        raise NotImplementedError

    def run(self, **kwargs: Any) -> dict:
        try:
            result = self.execute(**kwargs)
        except ExpectedToolError as exc:
            result = ToolResult(tool=self.name, ok=False, error=str(exc))
        return result.to_dict()
