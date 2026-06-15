"""get_equipment, get_process_conditions, get_equipment_logs."""

from __future__ import annotations

from typing import Any, ClassVar

from backend.app.data_access.repositories import Repositories
from backend.app.tools.results import DataTool, ExpectedToolError, SourceRef, ToolResult


class GetEquipmentTool(DataTool):
    name: ClassVar[str] = "get_equipment"
    description: ClassVar[str] = (
        "Return the equipment master record for one asset, or all assets if no id "
        "is given. Includes the four prioritization dimensions."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {"equipment_id": {"type": "string", "description": "Asset id; omit for all."}},
        "additionalProperties": False,
    }

    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    def execute(self, equipment_id: str | None = None) -> ToolResult:
        if equipment_id:
            row = self._repos.equipment.get(equipment_id)
            if not row:
                raise ExpectedToolError(f"Unknown equipment_id {equipment_id!r}.")
            rows = [row]
        else:
            rows = self._repos.equipment.all()
        sources = [SourceRef.record(table="equipment_master", id=r["equipment_id"]) for r in rows]
        data = rows[0] if equipment_id else rows
        summary = (f"{rows[0]['name']}" if equipment_id else f"{len(rows)} assets")
        return ToolResult(tool=self.name, data=data, sources=sources, summary=summary)


class GetProcessConditionsTool(DataTool):
    name: ClassVar[str] = "get_process_conditions"
    description: ClassVar[str] = (
        "Return reference operating conditions (nominal / alert / action thresholds) "
        "for one asset, or all assets if no id is given."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {"equipment_id": {"type": "string", "description": "Asset id; omit for all."}},
        "additionalProperties": False,
    }

    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    def execute(self, equipment_id: str | None = None) -> ToolResult:
        rows = self._repos.process.by_equipment(equipment_id)
        if not rows:
            raise ExpectedToolError(
                f"No process conditions for {equipment_id!r}." if equipment_id
                else "No process conditions found."
            )
        sources = [
            SourceRef.record(table="process_conditions", id=f"{r['equipment_id']}:{r['indicator']}",
                             equipment_id=r["equipment_id"])
            for r in rows
        ]
        return ToolResult(tool=self.name, data=rows, sources=sources,
                          summary=f"{len(rows)} indicator(s)")


class GetEquipmentLogsTool(DataTool):
    name: ClassVar[str] = "get_equipment_logs"
    description: ClassVar[str] = (
        "Return delay logs and incident records for an asset (or all), optionally "
        "since a date (YYYY-MM-DD). Useful for delay-severity context."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "Asset id; omit for all."},
            "since": {"type": "string", "description": "Only logs on/after this date (YYYY-MM-DD)."},
            "limit": {"type": "integer", "description": "Max rows per category."},
        },
        "additionalProperties": False,
    }

    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    def execute(self, equipment_id: str | None = None, since: str | None = None,
                limit: int | None = None) -> ToolResult:
        delays = self._repos.delays.query(equipment_id=equipment_id, since=since, limit=limit)
        incidents = self._repos.incidents.query(equipment_id=equipment_id, since=since, limit=limit)
        sources = (
            [SourceRef.record(table="delay_logs", id=d["delay_id"], equipment_id=d["equipment_id"])
             for d in delays]
            + [SourceRef.record(table="incident_records", id=i["incident_id"],
                                equipment_id=i["equipment_id"]) for i in incidents]
        )
        data = {"delays": delays, "incidents": incidents}
        return ToolResult(
            tool=self.name, data=data, sources=sources,
            summary=f"{len(delays)} delay(s), {len(incidents)} incident(s)",
        )
