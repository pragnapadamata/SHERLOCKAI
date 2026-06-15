"""POST /api/reports -- structured maintenance report via the orchestrator (tokens)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_system
from backend.app.api.schemas import Report, ReportRequest

router = APIRouter()

_REPORT_QUERY = (
    "Generate a structured maintenance report for {equipment_id}: current condition, probable "
    "fault diagnosis, root cause, remaining useful life and early warning, risk and priority, "
    "and recommended immediate and long-term actions."
)


@router.post("/api/reports")
def generate_report(req: ReportRequest, system: Any = Depends(get_system)) -> Report:
    result = system.orchestrator.run(
        _REPORT_QUERY.format(equipment_id=req.equipment_id),
        session_id=f"report-{req.equipment_id}",
    )
    # The agent loop degrades gracefully (it never raises) on a quota 429 / tool failure,
    # returning an empty result. Surface that as a clear error instead of a blank report.
    if not result.findings and not result.provenance:
        raise HTTPException(
            status_code=503,
            detail="The report could not be generated; the analysis step did not complete. "
            "Please try again.",
        )
    sections = [
        {"role": f.get("role"), "summary": f.get("summary"), "key_facts": f.get("key_facts")}
        for f in result.findings
    ]
    return Report(
        equipment_id=req.equipment_id,
        generated_at=datetime.now().isoformat(timespec="seconds"),
        title=f"Maintenance report - {req.equipment_id}",
        body=result.answer, sections=sections, provenance=result.provenance,
        specialists_used=result.specialists_used,
        tokens_in=result.tokens_in, tokens_out=result.tokens_out,
    )
