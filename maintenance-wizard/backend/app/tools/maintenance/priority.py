"""compute_priority -- transparent maintenance prioritization (MTR 20/80).

Combines the four spec dimensions (process criticality, typical delay severity,
spares availability, procurement lead time) into a 0-100 score, returning the
full component breakdown for explainability and flagging the top ~20% as the MTR
"vital few". A Phase 3 RUL/anomaly risk modifier can extend the score via the
``risk_modifier`` hook without changing the four-dimension base.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any, ClassVar

from backend.app.core.config import get_settings
from backend.app.data_access.repositories import Repositories
from backend.app.ml.risk import RiskAssessment
from backend.app.tools.results import (
    DataTool,
    ExpectedToolError,
    ScoreComponent,
    SourceRef,
    ToolResult,
)

_CRITICALITY = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}
_SPARES_RISK = {"in_stock": 0.0, "on_order": 0.5, "none": 1.0}
_DELAY_CAP_MIN = 480.0    # 8 hours
_LEADTIME_CAP_WK = 12.0

# Phase 3 hook: maps an equipment_id to a dynamic RUL/anomaly risk (or None).
RiskModifier = Callable[[str], "RiskAssessment | None"]


class ComputePriorityTool(DataTool):
    name: ClassVar[str] = "compute_priority"
    description: ClassVar[str] = (
        "Compute a transparent maintenance priority score (0-100) from the four "
        "factors -- process criticality, typical delay severity, spares "
        "availability, and procurement lead time -- after Tata's MTR 20/80 "
        "principle. Returns the per-factor component breakdown. Pass an "
        "equipment_id for one asset, or omit for a ranked plant-wide list."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "One asset; omit for all, ranked."},
        },
        "additionalProperties": False,
    }

    def __init__(self, repos: Repositories, weights: dict[str, float] | None = None,
                 risk_modifier: RiskModifier | None = None,
                 risk_weight: float | None = None) -> None:
        self._repos = repos
        self._weights = weights or {
            "criticality": 0.40, "delay": 0.25, "spares": 0.15, "leadtime": 0.20
        }
        self._risk_modifier = risk_modifier
        self._risk_weight = risk_weight if risk_weight is not None else get_settings().risk_weight

    def _components(self, asset: dict) -> tuple[list[ScoreComponent], float]:
        w = self._weights
        crit = _CRITICALITY.get(str(asset["process_criticality"]), 0.5)
        delay_min = float(asset["typical_delay_severity_min"])
        delay = min(delay_min / _DELAY_CAP_MIN, 1.0)
        spares = _SPARES_RISK.get(str(asset["spare_availability"]), 0.5)
        lead_wk = float(asset["procurement_lead_time_weeks"])
        leadtime = min(lead_wk / _LEADTIME_CAP_WK, 1.0)

        raw = {
            "criticality": (asset["process_criticality"], crit),
            "delay": (delay_min, delay),
            "spares": (asset["spare_availability"], spares),
            "leadtime": (lead_wk, leadtime),
        }
        components: list[ScoreComponent] = []
        for dim, (raw_value, normalized) in raw.items():
            weight = w[dim]
            components.append(ScoreComponent(
                dimension=dim, raw_value=raw_value, normalized=round(normalized, 3),
                weight=weight, contribution=round(weight * normalized * 100, 2),
            ))
        score = round(sum(c.contribution for c in components), 1)
        return components, score

    def _apply_risk(self, asset: dict, base_components: list[ScoreComponent], base_score: float):
        """Fold dynamic risk in as an additive, capped component. Returns
        (components, final_score, uncapped_score, capped, risk_detail)."""

        if self._risk_modifier is None:
            return base_components, base_score, base_score, False, None
        assessment = self._risk_modifier(asset["equipment_id"])
        if assessment is None or assessment.score <= 0:
            return base_components, base_score, base_score, False, None

        contribution = round(float(self._risk_weight * assessment.score * 100), 2)
        risk_component = ScoreComponent(
            dimension="dynamic_risk", raw_value=assessment.detail,
            normalized=round(float(assessment.score), 3), weight=self._risk_weight,
            contribution=contribution,
        )
        uncapped = round(float(base_score + contribution), 1)
        final = round(min(uncapped, 100.0), 1)
        return base_components + [risk_component], final, uncapped, bool(uncapped > 100.0), assessment.detail

    def _score_asset(self, asset: dict) -> dict:
        base_components, base_score = self._components(asset)
        components, final, uncapped, capped, risk_detail = self._apply_risk(
            asset, base_components, base_score
        )
        item = {
            "equipment_id": asset["equipment_id"],
            "name": asset["name"],
            "priority_score": final,
            "base_score": base_score,
            "components": [c.model_dump() for c in components],
        }
        if risk_detail is not None:
            item["dynamic_risk"] = risk_detail
            item["score_uncapped"] = uncapped
            item["capped"] = capped
        return item

    def execute(self, equipment_id: str | None = None) -> ToolResult:
        method = (
            "weighted MTR priority = 100 * sum(weight_i * normalized_i) over "
            "{criticality, delay, spares, leadtime}"
        )
        detail = "; ".join(f"{k}={v}" for k, v in self._weights.items())

        if equipment_id:
            asset = self._repos.equipment.get(equipment_id)
            if not asset:
                raise ExpectedToolError(f"Unknown equipment_id {equipment_id!r}.")
            base_components, base_score = self._components(asset)
            components, final, uncapped, capped, risk_detail = self._apply_risk(
                asset, base_components, base_score
            )
            data = {"equipment_id": equipment_id, "name": asset["name"],
                    "priority_score": final, "base_score": base_score}
            if risk_detail is not None:
                data["dynamic_risk"] = risk_detail
                data["score_uncapped"] = uncapped
                data["capped"] = capped
            summary = f"{equipment_id} priority {final}/100"
            if risk_detail is not None:
                summary += " (risk-adjusted)"
                if capped:
                    summary += " [capped at 100; components exceed score]"
            return ToolResult(
                tool=self.name, data=data, components=components,
                sources=[
                    SourceRef.record(table="equipment_master", id=equipment_id),
                    SourceRef.computation(method=method, detail=detail),
                ],
                summary=summary,
            )

        assets = self._repos.equipment.all()
        scored = sorted((self._score_asset(a) for a in assets),
                        key=lambda x: x["priority_score"], reverse=True)
        vital_few = max(1, math.ceil(0.2 * len(scored)))
        for rank, item in enumerate(scored, start=1):
            item["rank"] = rank
            item["vital_few"] = rank <= vital_few

        sources = [SourceRef.computation(method=method, detail=detail)]
        sources += [SourceRef.record(table="equipment_master", id=i["equipment_id"]) for i in scored]
        top = scored[0]
        return ToolResult(
            tool=self.name, data=scored, sources=sources,
            summary=f"Top priority: {top['equipment_id']} ({top['priority_score']}/100); "
                    f"MTR vital few = top {vital_few} of {len(scored)}",
        )
