"""Dynamic risk for the priority risk_modifier hook.

Combines RUL risk (low RUL -> high) and anomaly severity (ISO-zone based) by
``max`` -- the worst signal drives urgency. Returns a ``RiskAssessment`` with a
human-readable detail so compute_priority can show it transparently. Degrades to
None when an asset has no sensors or its models are unavailable.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from backend.app.core.config import get_settings
from backend.app.ml.anomaly import AnomalyDetector
from backend.app.ml.rul import RULEstimator


@dataclass
class RiskAssessment:
    score: float        # 0..1
    detail: str
    basis: dict


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def build_risk_modifier(
    anomaly: AnomalyDetector, rul: RULEstimator, horizon_weeks: float | None = None
) -> Callable[[str], RiskAssessment | None]:
    settings = get_settings()
    horizon = horizon_weeks if horizon_weeks is not None else settings.rul_horizon_weeks
    cache: dict[str, RiskAssessment | None] = {}

    def modifier(equipment_id: str) -> RiskAssessment | None:
        if equipment_id in cache:
            return cache[equipment_id]

        if not rul.available(equipment_id):
            cache[equipment_id] = None
            return None

        rul_risk, rul_desc = 0.0, "stable"
        try:
            r = rul.estimate(equipment_id)
            if r.status == "at_or_over_threshold":
                rul_risk, rul_desc = 1.0, "at/over failure threshold"
            elif r.status == "degrading" and r.rul_weeks is not None:
                rul_risk = _clamp(1 - r.rul_weeks / horizon)
                rul_desc = f"RUL {r.rul_weeks}wk"
        except Exception:  # noqa: BLE001 -- risk must never crash priority
            rul_desc = "rul_unavailable"

        anomaly_risk, anomaly_desc = 0.0, "no anomaly model"
        if anomaly.available(equipment_id):
            try:
                a = anomaly.score(equipment_id)
                anomaly_risk = a.severity
                anomaly_desc = f"anomaly severity {a.severity}"
            except Exception:  # noqa: BLE001
                anomaly_desc = "anomaly_unavailable"

        risk = max(rul_risk, anomaly_risk)
        result = None if risk <= 0 else RiskAssessment(
            score=round(risk, 3),
            detail=f"{rul_desc}; {anomaly_desc}",
            basis={"rul_risk": round(rul_risk, 3), "anomaly_risk": round(anomaly_risk, 3)},
        )
        cache[equipment_id] = result
        return result

    return modifier
