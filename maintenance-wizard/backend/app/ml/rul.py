"""Remaining useful life by classical robust degradation-trend extrapolation.

A Theil-Sen line (robust to transient spikes, deterministic) is fit on the
degradation portion of the governing channel and extrapolated to the ISO
10816-3 damage-zone onset (4.5 mm/s) -- the fracture-equivalent end of life. The
earlier ISO action crossing (2.8) is reported separately as the "plan the
repair" horizon. The RUL interval is a +/- degradation-rate planning allowance,
which is more realistic than the (unrealistically tight) statistical slope CI on
the clean synthetic trend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from backend.app.core.config import RAW_SENSORS, get_settings
from backend.app.data_access import sensors

_FLAT_SLOPE = 1e-5


@dataclass
class RULResult:
    equipment_id: str
    governing_channel: str
    current_value: float
    failure_threshold: float
    failure_basis: str
    status: str  # degrading | stable | at_or_over_threshold
    rul_weeks: float | None
    rul_interval_weeks: list[float] | None
    time_to_action_weeks: float | None
    trend: dict = field(default_factory=dict)


class RULEstimator:
    def __init__(self, sensors_dir: Path | None = None, interval_frac: float | None = None) -> None:
        settings = get_settings()
        self._sensors_dir = sensors_dir or RAW_SENSORS
        self._frac = interval_frac if interval_frac is not None else settings.rul_interval_frac

    def available(self, equipment_id: str) -> bool:
        return sensors.has_sensors(equipment_id, self._sensors_dir)

    def estimate(self, equipment_id: str, channel: str | None = None) -> RULResult:
        from scipy.stats import theilslopes

        df = sensors.read_window(equipment_id, sensors_dir=self._sensors_dir).reset_index(drop=True)
        channels = sensors.channel_names(df)
        governing = channel or ("vibration_rms_mm_s" if "vibration_rms_mm_s" in channels else channels[0])
        failure_threshold = sensors.ISO_RMS_DAMAGE
        action_threshold = sensors.ISO_RMS_ACTION

        deg = df[df["regime"] != "baseline"] if "regime" in df.columns else df
        if len(deg) < 50:
            deg = df.tail(4 * 7 * 144)  # fall back to the last 4 weeks
        deg = deg.reset_index(drop=True)

        t0 = deg["timestamp_utc"].min()
        days = ((deg["timestamp_utc"] - t0).dt.total_seconds() / 86400.0).to_numpy()
        y = deg[governing].to_numpy()
        slope, intercept, lo_slope, hi_slope = theilslopes(y, days)

        t_last = float(days[-1])
        current = float(intercept + slope * t_last)
        fitted = intercept + slope * days
        ss_res = float(np.sum((y - fitted) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2)) or _FLAT_SLOPE
        trend = {
            "governing_channel": governing,
            "method": "Theil-Sen robust linear regression",
            "slope_per_day": round(float(slope), 6),
            "slope_ci_per_day": [round(float(lo_slope), 6), round(float(hi_slope), 6)],
            "r_squared": round(1 - ss_res / ss_tot, 4),
            "n_points": int(len(deg)),
            "fit_window": {"start": str(deg["timestamp_utc"].min()), "end": str(deg["timestamp_utc"].max())},
        }

        def weeks(days_value: float) -> float:
            return float(round(days_value / 7.0, 1))

        if slope <= _FLAT_SLOPE:
            return RULResult(equipment_id, governing, round(current, 4), failure_threshold,
                             "ISO 10816-3 damage-zone onset", "stable", None, None, None, trend)

        if current >= failure_threshold:
            return RULResult(equipment_id, governing, round(current, 4), failure_threshold,
                             "ISO 10816-3 damage-zone onset", "at_or_over_threshold",
                             0.0, [0.0, 0.0], 0.0, trend)

        rul_days = (failure_threshold - current) / slope
        rul_weeks = weeks(rul_days)
        interval = [max(weeks(rul_days * (1 - self._frac)), 0.0), weeks(rul_days * (1 + self._frac))]
        tta = weeks(max((action_threshold - current) / slope, 0.0)) if current < action_threshold else 0.0

        return RULResult(
            equipment_id=equipment_id, governing_channel=governing, current_value=round(current, 4),
            failure_threshold=failure_threshold, failure_basis="ISO 10816-3 damage-zone onset",
            status="degrading", rul_weeks=rul_weeks, rul_interval_weeks=interval,
            time_to_action_weeks=tta, trend=trend,
        )
