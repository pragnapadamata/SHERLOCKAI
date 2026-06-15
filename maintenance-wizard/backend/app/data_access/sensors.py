"""Read and summarize the per-asset sensor parquet.

Returns compact summaries by default (latest/mean/min/max/std/trend per channel,
plus the current ISO regime and anomaly count) rather than raw 16k-row dumps; a
downsampled series is available on request. Windows anchor to the latest sample
in the file (the simulation "now").
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from backend.app.core.config import RAW_SENSORS

# ISO 10816-3 velocity RMS zone boundaries (mm/s), Class III/IV. Published values.
ISO_RMS_ALERT = 1.4
ISO_RMS_ACTION = 2.8
ISO_RMS_DAMAGE = 4.5

_NON_CHANNEL = {"timestamp_utc", "equipment_id", "regime", "anomaly_flag", "note"}
_UNIT_SUFFIX = {
    "mm_s": "mm/s", "_C": "degC", "ppm": "ppm", "bar": "bar",
    "_A": "A", "kN": "kN", "db": "dB", "_g": "g",
}


def sensor_path(equipment_id: str, sensors_dir: Path | None = None) -> Path:
    return (sensors_dir or RAW_SENSORS) / f"{equipment_id}_sensors.parquet"


def has_sensors(equipment_id: str, sensors_dir: Path | None = None) -> bool:
    return sensor_path(equipment_id, sensors_dir).exists()


def _unit_for(channel: str) -> str:
    for suffix, unit in _UNIT_SUFFIX.items():
        if channel.endswith(suffix):
            return unit
    return ""


def channel_names(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in _NON_CHANNEL]


def _bound(value: str) -> pd.Timestamp:
    """Parse a window bound to a naive (tz-free) Timestamp the LLM may pass in any form."""

    ts = pd.Timestamp(value)
    return ts.tz_localize(None) if ts.tz is not None else ts


def read_window(
    equipment_id: str,
    *,
    channel: str | None = None,
    start: str | None = None,
    end: str | None = None,
    last_n: int | None = None,
    sensors_dir: Path | None = None,
) -> pd.DataFrame:
    df = pd.read_parquet(sensor_path(equipment_id, sensors_dir))
    # Parquet persists timestamps at microsecond resolution; normalize to naive ns
    # so comparisons against a parsed bound are valid under pandas 3.0.
    df["timestamp_utc"] = df["timestamp_utc"].astype("datetime64[ns]")
    df = df.sort_values("timestamp_utc").reset_index(drop=True)
    if start is not None:
        df = df[df["timestamp_utc"] >= _bound(start)]
    if end is not None:
        df = df[df["timestamp_utc"] <= _bound(end)]
    if last_n is not None:
        df = df.tail(last_n)
    if channel is not None:
        keep = [c for c in df.columns if c in _NON_CHANNEL or c == channel]
        df = df[keep]
    return df.reset_index(drop=True)


def _slope_per_day(times: pd.Series, values: pd.Series) -> float:
    valid = values.notna()
    if valid.sum() < 2:
        return 0.0
    t0 = times.min()
    days = (times[valid] - t0).dt.total_seconds() / 86400.0
    slope = np.polyfit(days.to_numpy(), values[valid].to_numpy(), 1)[0]
    return round(float(slope), 6)


def summarize(df: pd.DataFrame) -> dict:
    """Compact per-channel + regime summary of a windowed frame."""

    channels = channel_names(df)
    window = {
        "start": str(df["timestamp_utc"].min()),
        "end": str(df["timestamp_utc"].max()),
        "n_samples": int(len(df)),
    }
    channel_summ: dict[str, dict] = {}
    for ch in channels:
        s = df[ch]
        channel_summ[ch] = {
            "unit": _unit_for(ch),
            "latest": round(float(s.iloc[-1]), 4),
            "mean": round(float(s.mean()), 4),
            "min": round(float(s.min()), 4),
            "max": round(float(s.max()), 4),
            "std": round(float(s.std()), 4),
            "slope_per_day": _slope_per_day(df["timestamp_utc"], s),
        }

    regime = {}
    if "regime" in df.columns:
        counts = {str(k): int(v) for k, v in df["regime"].value_counts().items()}
        regime = {"current": str(df["regime"].iloc[-1]), "counts": counts}
    anomaly = {}
    if "anomaly_flag" in df.columns:
        flagged = df[df["anomaly_flag"]]
        anomaly = {
            "count": int(len(flagged)),
            "last_at": (str(flagged["timestamp_utc"].max()) if len(flagged) else None),
        }

    return {
        "window": window,
        "channels": channel_summ,
        "regime": regime,
        "anomalies": anomaly,
        "iso_thresholds_mm_s": {
            "alert": ISO_RMS_ALERT, "action": ISO_RMS_ACTION, "damage": ISO_RMS_DAMAGE
        },
    }


def downsample(df: pd.DataFrame, *, freq: str = "1D") -> list[dict]:
    """Mean of each channel per period, as a small series for charting."""

    channels = channel_names(df)
    if not channels:
        return []
    g = df.set_index("timestamp_utc")[channels].resample(freq).mean().round(4)
    out = []
    for ts, row in g.iterrows():
        record = {"timestamp": str(ts)}
        record.update({ch: (None if pd.isna(row[ch]) else float(row[ch])) for ch in channels})
        out.append(record)
    return out
