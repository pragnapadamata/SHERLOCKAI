"""A replay cursor over the committed sensor parquet (the simulated IoT stream).

Tracks a simulated 'now' that advances over the recorded series; the live window
ending at the cursor is what the engine scores. No data is copied or mutated.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from backend.app.core.config import RAW_SENSORS
from backend.app.data_access import sensors


class SensorStream:
    def __init__(self, equipment_ids: list[str], *, sensors_dir: Path | None = None,
                 start_at: datetime | None = None, step: timedelta | None = None,
                 start_days_back: int = 21) -> None:
        self._ids = list(equipment_ids)
        self._dir = sensors_dir or RAW_SENSORS
        df = sensors.read_window(self._ids[0], sensors_dir=self._dir)
        self._start_min = df["timestamp_utc"].min().to_pydatetime()
        self._end = df["timestamp_utc"].max().to_pydatetime()
        self._step = step or timedelta(days=1)
        self._now = start_at or (self._end - timedelta(days=start_days_back))
        self._initial_now = self._now
        self._injected: set[str] = set()

    @property
    def now(self) -> datetime:
        return self._now

    @property
    def end(self) -> datetime:
        return self._end

    def at_end(self) -> bool:
        return self._now >= self._end

    def advance(self, step: timedelta | None = None) -> datetime:
        self._now = min(self._now + (step or self._step), self._end)
        return self._now

    def advance_to(self, when: str | datetime) -> datetime:
        ts = pd.Timestamp(when).to_pydatetime()
        self._now = max(self._start_min, min(ts, self._end))
        return self._now

    def reset(self) -> datetime:
        """Return the cursor to its initial position and clear any injected anomalies.

        Used by the demo/ops reset control so a planted scenario can be re-fired.
        """
        self._now = self._initial_now
        self._injected.clear()
        return self._now

    def window_bounds(self, lookback: timedelta) -> tuple[datetime, datetime]:
        return (self._now - lookback, self._now)

    def current_readings(self, equipment_id: str, lookback: timedelta) -> dict:
        start, end = self.window_bounds(lookback)
        df = sensors.read_window(equipment_id, start=start.isoformat(), end=end.isoformat(),
                                 sensors_dir=self._dir)
        return sensors.summarize(df) if len(df) else {}

    # Secondary, synthetic trigger for assets without a planted anomaly (demo only).
    def inject_anomaly(self, equipment_id: str) -> None:
        self._injected.add(equipment_id)

    def clear_injection(self, equipment_id: str) -> None:
        self._injected.discard(equipment_id)

    def is_injected(self, equipment_id: str) -> bool:
        return equipment_id in self._injected
