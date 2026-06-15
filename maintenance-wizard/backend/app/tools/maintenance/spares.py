"""get_spare_parts -- availability and procurement lead time."""

from __future__ import annotations

from typing import Any, ClassVar

from backend.app.data_access.repositories import Repositories
from backend.app.tools.results import DataTool, ExpectedToolError, SourceRef, ToolResult


class GetSparePartsTool(DataTool):
    name: ClassVar[str] = "get_spare_parts"
    description: ClassVar[str] = (
        "Return spare parts with on-hand quantity, availability, and procurement "
        "lead time. Look up by part_id, by equipment_id, or all if neither is given."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "part_id": {"type": "string", "description": "Specific spare part id."},
            "equipment_id": {"type": "string", "description": "All spares for this asset."},
        },
        "additionalProperties": False,
    }

    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    def execute(self, part_id: str | None = None, equipment_id: str | None = None) -> ToolResult:
        if part_id:
            row = self._repos.spares.by_part(part_id)
            if not row:
                raise ExpectedToolError(f"Unknown part_id {part_id!r}.")
            rows = [row]
        elif equipment_id:
            rows = self._repos.spares.by_equipment(equipment_id)
            if not rows:
                raise ExpectedToolError(f"No spares mapped to {equipment_id!r}.")
        else:
            rows = self._repos.spares.all()
        sources = [
            SourceRef.record(table="spare_parts_master", id=r["part_id"], equipment_id=r["equipment_id"])
            for r in rows
        ]
        data = rows[0] if part_id else rows
        return ToolResult(tool=self.name, data=data, sources=sources,
                          summary=f"{len(rows)} spare(s)")
