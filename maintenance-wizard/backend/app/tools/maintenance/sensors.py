"""get_sensor_data -- windowed sensor summary (optional downsampled series)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from backend.app.core.config import RAW_SENSORS
from backend.app.data_access import sensors
from backend.app.tools.results import DataTool, ExpectedToolError, SourceRef, ToolResult


class GetSensorDataTool(DataTool):
    name: ClassVar[str] = "get_sensor_data"
    description: ClassVar[str] = (
        "Return a sensor summary for a monitored asset: per-channel latest, mean, "
        "min, max, std, and per-day trend, plus the current ISO 10816-3 regime and "
        "anomaly count over the window. Set include_series for a downsampled series. "
        "Does not return raw high-frequency samples."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "Monitored asset id."},
            "channel": {"type": "string", "description": "Restrict to one channel."},
            "last_n": {"type": "integer", "description": "Use only the most recent N samples."},
            "start": {"type": "string", "description": "Window start (ISO timestamp). Omit to "
                      "use the latest window (recommended); the dataset is recent 2026 data."},
            "end": {"type": "string", "description": "Window end (ISO timestamp). Omit to use "
                    "the latest window; the dataset is recent 2026 data."},
            "include_series": {"type": "boolean", "description": "Include a downsampled series."},
            "downsample_freq": {"type": "string", "description": "Series period, e.g. '1D' (default)."},
        },
        "required": ["equipment_id"],
        "additionalProperties": False,
    }

    def __init__(self, sensors_dir: Path | None = None) -> None:
        self._dir = sensors_dir or RAW_SENSORS

    def execute(self, equipment_id: str, channel: str | None = None, last_n: int | None = None,
                start: str | None = None, end: str | None = None,
                include_series: bool = False, downsample_freq: str = "1D") -> ToolResult:
        if not sensors.has_sensors(equipment_id, self._dir):
            raise ExpectedToolError(
                f"No sensor data for {equipment_id!r} (only monitored assets have sensors)."
            )
        df = sensors.read_window(
            equipment_id, channel=channel, start=start, end=end, last_n=last_n, sensors_dir=self._dir
        )
        if channel is not None and channel not in df.columns:
            raise ExpectedToolError(f"Unknown channel {channel!r} for {equipment_id}.")
        if len(df) == 0:
            raise ExpectedToolError("Selected window contains no samples.")

        summary = sensors.summarize(df)
        if include_series:
            summary["series"] = sensors.downsample(df, freq=downsample_freq)

        source = SourceRef.sensor(
            source=f"data/raw/sensors/{equipment_id}_sensors.parquet",
            equipment_id=equipment_id, window=summary["window"],
            n_samples=summary["window"]["n_samples"],
        )
        regime = summary.get("regime", {}).get("current", "n/a")
        return ToolResult(
            tool=self.name, data=summary, sources=[source],
            summary=f"{equipment_id}: {summary['window']['n_samples']} samples, current regime {regime}",
        )
