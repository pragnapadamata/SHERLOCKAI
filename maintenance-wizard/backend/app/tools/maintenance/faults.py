"""get_fault_info -- fault catalog lookup with linked SOPs and spares.

Lookup is by exact fault_code, or by lexical symptom match (transparent: the
matched terms are returned as provenance). Semantic symptom->fault discovery is
intentionally left to search_knowledge over the fault-catalog chunks.
"""

from __future__ import annotations

from typing import Any, ClassVar

from backend.app.core.config import RAW_DOCS
from backend.app.data_access.repositories import Repositories
from backend.app.tools.results import DataTool, ExpectedToolError, SourceRef, ToolResult

_MAX_SYMPTOM_MATCHES = 5


def _sop_source(sop_id: str) -> str | None:
    matches = sorted((RAW_DOCS / "sops").glob(f"{sop_id}_*.md"))
    return f"sops/{matches[0].name}" if matches else None


class GetFaultInfoTool(DataTool):
    name: ClassVar[str] = "get_fault_info"
    description: ClassVar[str] = (
        "Look up fault/error codes. Provide a fault_code for an exact entry, or "
        "symptoms for a transparent lexical match. Returns the fault with its "
        "likely cause, recommended action, and linked SOPs and spare parts."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "fault_code": {"type": "string", "description": "Exact fault code, e.g. F3-GBX-002."},
            "symptoms": {"type": "string", "description": "Free-text symptoms to match lexically."},
            "equipment_id": {"type": "string", "description": "Scope a symptom search to one asset."},
        },
        "additionalProperties": False,
    }

    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    def _resolve(self, fault: dict) -> tuple[dict, list[SourceRef]]:
        sop_ids = [s for s in str(fault.get("related_sops", "")).split(";") if s]
        spare_ids = [s for s in str(fault.get("related_spares", "")).split(";") if s]

        sop_docs = [{"id": sid, "source": _sop_source(sid)} for sid in sop_ids]
        spares = []
        for pid in spare_ids:
            row = self._repos.spares.by_part(pid)
            if row:
                spares.append({
                    "part_id": pid, "spare_availability": row["spare_availability"],
                    "procurement_lead_time_weeks": row["procurement_lead_time_weeks"],
                    "on_hand_qty": row["on_hand_qty"],
                })

        item = {k: v for k, v in fault.items() if not k.startswith("_")}
        item["related_sop_docs"] = sop_docs
        item["related_spares_detail"] = spares
        if "_matched_terms" in fault:
            item["matched_terms"] = fault["_matched_terms"]

        sources: list[SourceRef] = [
            SourceRef.record(table="fault_catalog", id=fault["fault_code"],
                             equipment_id=fault["equipment_id"])
        ]
        for d in sop_docs:
            sources.append(SourceRef.document(
                doc_id=d["id"], doc_type="sop", source=d["source"], section="(SOP)"
            ))
        for s in spares:
            sources.append(SourceRef.record(table="spare_parts_master", id=s["part_id"]))
        return item, sources

    def execute(self, fault_code: str | None = None, symptoms: str | None = None,
                equipment_id: str | None = None) -> ToolResult:
        if fault_code:
            fault = self._repos.faults.by_code(fault_code)
            if not fault:
                raise ExpectedToolError(f"Unknown fault_code {fault_code!r}.")
            item, sources = self._resolve(fault)
            return ToolResult(tool=self.name, data=item, sources=sources,
                              summary=f"{fault_code}: {fault['title']}")

        if symptoms:
            matches = self._repos.faults.search_symptoms(symptoms, equipment_id)[:_MAX_SYMPTOM_MATCHES]
            if not matches:
                raise ExpectedToolError(f"No fault matched symptoms {symptoms!r}.")
            items, sources = [], []
            for fault in matches:
                item, item_sources = self._resolve(fault)
                items.append(item)
                sources.extend(item_sources)
            top = items[0]
            return ToolResult(
                tool=self.name, data=items, sources=sources,
                summary=f"{len(items)} fault(s); top {top['fault_code']} "
                        f"(matched {', '.join(top.get('matched_terms') or [])})",
            )

        raise ExpectedToolError("Provide either fault_code or symptoms.")
