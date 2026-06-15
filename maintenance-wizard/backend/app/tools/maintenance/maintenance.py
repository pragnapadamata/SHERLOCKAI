"""get_maintenance_history, log_maintenance_action, get_logbook."""

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

_ENTRY_TYPES = ["observation", "action", "confirmation"]


class GetMaintenanceHistoryTool(DataTool):
    name: ClassVar[str] = "get_maintenance_history"
    description: ClassVar[str] = (
        "Return past work orders for an asset (or all), optionally filtered by date "
        "(since, YYYY-MM-DD) and work type."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "Asset id; omit for all."},
            "since": {"type": "string", "description": "Only work orders on/after this date."},
            "type": {"type": "string", "description": "Work type, e.g. lubrication, inspection, corrective."},
            "limit": {"type": "integer", "description": "Max rows."},
        },
        "additionalProperties": False,
    }

    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    def execute(self, equipment_id: str | None = None, since: str | None = None,
                type: str | None = None, limit: int | None = None) -> ToolResult:
        rows = self._repos.history.query(
            equipment_id=equipment_id, since=since, type=type, limit=limit or 50
        )
        sources = [
            SourceRef.record(table="maintenance_history", id=r["work_order_id"],
                             equipment_id=r["equipment_id"])
            for r in rows
        ]
        return ToolResult(tool=self.name, data=rows, sources=sources,
                          summary=f"{len(rows)} work order(s)")


class GetLogbookTool(DataTool):
    name: ClassVar[str] = "get_logbook"
    description: ClassVar[str] = (
        "Return digital logbook entries for an asset (or all), newest first."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "Asset id; omit for all."},
            "limit": {"type": "integer", "description": "Max entries (default 20)."},
        },
        "additionalProperties": False,
    }

    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    def execute(self, equipment_id: str | None = None, limit: int | None = None) -> ToolResult:
        rows = self._repos.logbook.query(equipment_id=equipment_id, limit=limit or 20)
        sources = [
            SourceRef.record(table="logbook", id=r["entry_id"], equipment_id=r["equipment_id"])
            for r in rows
        ]
        return ToolResult(tool=self.name, data=rows, sources=sources,
                          summary=f"{len(rows)} entr(y/ies)")


class LogMaintenanceActionTool(DataTool):
    name: ClassVar[str] = "log_maintenance_action"
    description: ClassVar[str] = (
        "Append an entry to the digital maintenance logbook for an asset and return "
        "the written record."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "Asset the entry concerns."},
            "text": {"type": "string", "description": "The observation, action, or confirmation."},
            "author_user_id": {"type": "string", "description": "Authoring user id."},
            "entry_type": {"type": "string", "enum": _ENTRY_TYPES, "description": "Entry type."},
            "related_fault_code": {"type": "string", "description": "Related fault code, if any."},
        },
        "required": ["equipment_id", "text"],
        "additionalProperties": False,
    }

    def __init__(self, repos: Repositories, clock: Callable[[], str] | None = None) -> None:
        self._repos = repos
        self._clock = clock or default_clock

    def execute(self, equipment_id: str, text: str, author_user_id: str | None = None,
                entry_type: str = "observation", related_fault_code: str | None = None) -> ToolResult:
        if not self._repos.equipment.get(equipment_id):
            raise ExpectedToolError(f"Unknown equipment_id {equipment_id!r}.")
        if entry_type not in _ENTRY_TYPES:
            raise ExpectedToolError(f"entry_type must be one of {_ENTRY_TYPES}.")
        if author_user_id and not self._repos.users.get(author_user_id):
            raise ExpectedToolError(f"Unknown author_user_id {author_user_id!r}.")

        record = self._repos.logbook.append(
            equipment_id=equipment_id, author_user_id=author_user_id, entry_type=entry_type,
            text=text, related_fault_code=related_fault_code, timestamp=self._clock(),
        )
        return ToolResult(
            tool=self.name, data=record,
            sources=[SourceRef.record(table="logbook", id=record["entry_id"], equipment_id=equipment_id)],
            summary=f"Logged {record['entry_id']} on {equipment_id}",
        )
