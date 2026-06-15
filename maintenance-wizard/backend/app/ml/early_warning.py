"""Catastrophic-failure early warning: combine anomaly + RUL + procurement.

Explicit triggers:
  - acute_anomaly: a flagged anomaly whose worst sample is in the ISO action/damage zone.
  - imminent_failure: RUL at/over the failure threshold, or <= rul_critical_weeks.
  - procurement_at_risk: the RUL interval LOWER BOUND <= the spare lead time
    (conservative "order now" logic -- plan against worst-case RUL).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.core.config import get_settings
from backend.app.data_access.repositories import Repositories
from backend.app.ml.anomaly import AnomalyDetector
from backend.app.ml.rul import RULEstimator


@dataclass
class EarlyWarningResult:
    equipment_id: str
    early_warning: bool
    severity: str  # none | high | critical
    triggers: list[dict] = field(default_factory=list)
    recommended_horizon: str | None = None
    anomaly_summary: dict = field(default_factory=dict)
    rul_summary: dict = field(default_factory=dict)


class EarlyWarningService:
    def __init__(self, anomaly: AnomalyDetector, rul: RULEstimator,
                 repos: Repositories, rul_critical_weeks: float | None = None) -> None:
        self._anomaly = anomaly
        self._rul = rul
        self._repos = repos
        settings = get_settings()
        self._rul_critical = (rul_critical_weeks if rul_critical_weeks is not None
                              else settings.rul_critical_weeks)

    def assess(self, equipment_id: str) -> EarlyWarningResult:
        if not self._rul.available(equipment_id):
            return EarlyWarningResult(equipment_id, False, "none",
                                      recommended_horizon=None,
                                      anomaly_summary={}, rul_summary={"status": "no_sensor_data"})

        anomaly = self._anomaly.score(equipment_id) if self._anomaly.available(equipment_id) else None
        rul = self._rul.estimate(equipment_id)
        triggers: list[dict] = []

        if anomaly and anomaly.is_anomaly and anomaly.iso_regime.get("at_anomaly") == "action":
            triggers.append({
                "type": "acute_anomaly",
                "detail": f"vibration in ISO action/damage zone (anomaly score {anomaly.anomaly_score})",
                "channels": [c["channel"] for c in anomaly.contributing_channels],
            })

        if rul.status == "at_or_over_threshold" or (
            rul.rul_weeks is not None and rul.rul_weeks <= self._rul_critical
        ):
            triggers.append({
                "type": "imminent_failure",
                "detail": f"RUL {rul.rul_weeks} wk at/under critical {self._rul_critical} wk",
            })

        asset = self._repos.equipment.get(equipment_id)
        lead = asset.get("procurement_lead_time_weeks") if asset else None
        if lead is not None and rul.rul_interval_weeks is not None and rul.rul_interval_weeks[0] <= lead:
            triggers.append({
                "type": "procurement_at_risk",
                "detail": f"RUL lower bound {rul.rul_interval_weeks[0]} wk <= spare lead time "
                          f"{lead} wk -- order the spare now",
            })

        acute = any(t["type"] in ("acute_anomaly", "imminent_failure") for t in triggers)
        early = bool(triggers)
        severity = "critical" if acute else ("high" if early else "none")
        horizon = None
        if acute:
            horizon = "immediate intervention"
        elif early:
            horizon = f"order spare now; plan repair within RUL ~{rul.rul_weeks} wk"

        return EarlyWarningResult(
            equipment_id=equipment_id, early_warning=early, severity=severity, triggers=triggers,
            recommended_horizon=horizon,
            anomaly_summary=({
                "is_anomaly": anomaly.is_anomaly, "anomaly_score": anomaly.anomaly_score,
                "severity": anomaly.severity, "at_anomaly_regime": anomaly.iso_regime.get("at_anomaly"),
                "channels": [c["channel"] for c in anomaly.contributing_channels],
            } if anomaly else {}),
            rul_summary={
                "status": rul.status, "rul_weeks": rul.rul_weeks,
                "rul_interval_weeks": rul.rul_interval_weeks,
                "time_to_action_weeks": rul.time_to_action_weeks,
            },
        )
