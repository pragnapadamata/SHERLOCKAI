"""ML predictive tools: detect_anomaly, predict_rul, assess_early_warning."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, ClassVar

from backend.app.core.channels import humanize_drivers
from backend.app.ml.anomaly import AnomalyDetector
from backend.app.ml.early_warning import EarlyWarningService
from backend.app.ml.rul import RULEstimator
from backend.app.tools.results import DataTool, ExpectedToolError, SourceRef, ToolResult


class DetectAnomalyTool(DataTool):
    name: ClassVar[str] = "detect_anomaly"
    description: ClassVar[str] = (
        "Multivariate anomaly detection over a monitored asset's sensor channels. "
        "Returns whether the window is anomalous, the score, the channels that drove "
        "it (with z-scores), an IsolationForest corroboration, and reconciliation "
        "with the ISO 10816-3 regime."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "Monitored asset id."},
            "last_n": {"type": "integer", "description": "Use only the most recent N samples."},
            "start": {"type": "string", "description": "Window start (ISO timestamp). Omit to "
                      "use the latest window (recommended); the dataset is recent 2026 data."},
            "end": {"type": "string", "description": "Window end (ISO timestamp). Omit to use "
                    "the latest window; the dataset is recent 2026 data."},
        },
        "required": ["equipment_id"],
        "additionalProperties": False,
    }

    def __init__(self, detector: AnomalyDetector) -> None:
        self._detector = detector

    def execute(self, equipment_id: str, last_n: int | None = None,
                start: str | None = None, end: str | None = None) -> ToolResult:
        if not self._detector.available(equipment_id):
            raise ExpectedToolError(
                f"No anomaly model for {equipment_id!r} (only monitored assets have one)."
            )
        result = self._detector.score(equipment_id, last_n=last_n, start=start, end=end)
        drivers = [c["channel"] for c in result.contributing_channels]
        verdict = "ANOMALY" if result.is_anomaly else "normal"
        return ToolResult(
            tool=self.name, data=asdict(result),
            sources=[
                SourceRef.sensor(source=f"data/raw/sensors/{equipment_id}_sensors.parquet",
                                 equipment_id=equipment_id, window=result.window,
                                 n_samples=result.window["n_samples"]),
                SourceRef.computation(
                    method="robust residual z-score (decision) + IsolationForest (corroboration)",
                    model="IsolationForest", drivers=drivers,
                    detail=f"score {result.anomaly_score} vs threshold {result.threshold}",
                ),
            ],
            summary=f"{equipment_id}: {verdict} (score {result.anomaly_score})"
                    + (f"; drivers {humanize_drivers(drivers)}" if drivers else ""),
        )


class PredictRulTool(DataTool):
    name: ClassVar[str] = "predict_rul"
    description: ClassVar[str] = (
        "Estimate remaining useful life by robust degradation-trend extrapolation to "
        "the ISO 10816-3 damage threshold (fracture-equivalent). Returns RUL in weeks "
        "with a planning interval, the trend basis, and the earlier time-to-action "
        "(ISO action threshold) horizon."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "Monitored asset id."},
            "channel": {"type": "string", "description": "Override the governing channel."},
        },
        "required": ["equipment_id"],
        "additionalProperties": False,
    }

    def __init__(self, estimator: RULEstimator) -> None:
        self._estimator = estimator

    def execute(self, equipment_id: str, channel: str | None = None) -> ToolResult:
        if not self._estimator.available(equipment_id):
            raise ExpectedToolError(
                f"No sensor data for {equipment_id!r}; RUL needs a monitored asset."
            )
        result = self._estimator.estimate(equipment_id, channel=channel)
        if result.status == "degrading":
            summary = (f"{equipment_id}: RUL ~{result.rul_weeks} wk "
                       f"(interval {result.rul_interval_weeks} wk); "
                       f"action in ~{result.time_to_action_weeks} wk")
        else:
            summary = f"{equipment_id}: {result.status}"
        return ToolResult(
            tool=self.name, data=asdict(result),
            sources=[
                SourceRef.sensor(source=f"data/raw/sensors/{equipment_id}_sensors.parquet",
                                 equipment_id=equipment_id, window=result.trend.get("fit_window", {}),
                                 n_samples=result.trend.get("n_points", 0)),
                SourceRef.computation(
                    method="Theil-Sen robust extrapolation to ISO 10816-3 damage threshold",
                    model="Theil-Sen", drivers=[result.governing_channel],
                    detail=f"slope {result.trend.get('slope_per_day')}/day to "
                           f"{result.failure_threshold} mm/s",
                ),
            ],
            summary=summary,
        )


class AssessEarlyWarningTool(DataTool):
    name: ClassVar[str] = "assess_early_warning"
    description: ClassVar[str] = (
        "Catastrophic-failure early warning for a monitored asset, combining anomaly, "
        "RUL, and procurement-vs-RUL logic. Returns the verdict, severity, and the "
        "explicit triggers that fired."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {"equipment_id": {"type": "string", "description": "Monitored asset id."}},
        "required": ["equipment_id"],
        "additionalProperties": False,
    }

    def __init__(self, service: EarlyWarningService) -> None:
        self._service = service

    def execute(self, equipment_id: str) -> ToolResult:
        result = self._service.assess(equipment_id)
        trigger_types = [t["type"] for t in result.triggers]
        return ToolResult(
            tool=self.name, data=asdict(result),
            sources=[
                SourceRef.computation(
                    method="early warning = acute anomaly OR imminent RUL OR procurement-at-risk",
                    drivers=trigger_types,
                    detail=result.recommended_horizon,
                ),
            ],
            summary=f"{equipment_id}: early_warning={result.early_warning} "
                    f"severity={result.severity} triggers={', '.join(trigger_types) or 'none'}",
        )
