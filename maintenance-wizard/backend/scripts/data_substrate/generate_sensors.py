"""Generate per-asset sensor time-series parquet for the three hero assets.

Each channel is baseline + piecewise-linear degradation trend + small diurnal
cycle + Gaussian noise, with scripted discrete anomalies layered on top. The
``regime`` column is derived from ISO 10816-3 velocity RMS zone boundaries so
downstream code reads the zone rather than recomputing it. Deterministic given
the fixed seed.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from backend.scripts.data_substrate import spec


def _channel_series(
    plan: spec.SensorPlan, channel: spec.ChannelPlan, n: int, seed: int
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    i = np.arange(n)
    t_day = i / spec.SAMPLES_PER_DAY
    baseline_end_day = plan.baseline_weeks * 7

    if channel.end_value is None or plan.degradation_weeks == 0:
        trend = np.zeros(n)
    else:
        deg_days = plan.degradation_weeks * 7
        progress = np.clip((t_day - baseline_end_day) / deg_days, 0.0, 1.0)
        trend = (channel.end_value - channel.baseline) * progress

    diurnal = 0.3 * channel.noise_sigma * np.sin(
        2 * np.pi * (i % spec.SAMPLES_PER_DAY) / spec.SAMPLES_PER_DAY
    )
    noise = rng.normal(0.0, channel.noise_sigma, n)
    return channel.baseline + trend + diurnal + noise


def _build_asset_frame(plan: spec.SensorPlan, asset_index: int) -> pd.DataFrame:
    n = spec.WINDOW_WEEKS * 7 * spec.SAMPLES_PER_DAY
    start = spec.window_start()
    timestamps = [start + timedelta(minutes=spec.SENSOR_PERIOD_MINUTES * k) for k in range(n)]

    series: dict[str, np.ndarray] = {}
    for ci, channel in enumerate(plan.channels):
        seed = spec.RANDOM_SEED * 1000 + asset_index * 100 + ci
        series[channel.name] = _channel_series(plan, channel, n, seed)

    # Layer scripted anomalies on top.
    anomaly_mask = np.zeros(n, dtype=bool)
    notes = np.array([""] * n, dtype=object)
    for event in plan.anomalies:
        start_idx = event.day * spec.SAMPLES_PER_DAY
        end_idx = min(start_idx + event.duration_samples, n)
        if start_idx >= n:
            continue
        for channel_name, value in event.overrides.items():
            series[channel_name][start_idx:end_idx] = value
        anomaly_mask[start_idx:end_idx] = True
        notes[start_idx] = event.note

    # Round each channel to its documented precision.
    for channel in plan.channels:
        series[channel.name] = np.round(series[channel.name], channel.decimals)

    # Derive ISO regime from the primary (RMS) channel.
    primary = series[plan.primary_channel]
    baseline_end_day = plan.baseline_weeks * 7
    day_index = np.arange(n) // spec.SAMPLES_PER_DAY
    regime = np.empty(n, dtype=object)
    for k in range(n):
        rms = primary[k]
        if rms > spec.ISO_RMS_ACTION:
            regime[k] = "action"
        elif rms > spec.ISO_RMS_ALERT:
            regime[k] = "alert"
        elif plan.degradation_weeks > 0 and day_index[k] >= baseline_end_day:
            regime[k] = "degrading"
        else:
            regime[k] = "baseline"

    anomaly_flag = anomaly_mask | np.isin(regime, ["alert", "action"])

    # Mark the first ISO alert-zone crossing where it is not already noted.
    first_alert = next((k for k in range(n) if regime[k] in ("alert", "action")), None)
    if first_alert is not None and notes[first_alert] == "":
        notes[first_alert] = "First ISO 10816-3 alert-zone crossing."

    frame: dict[str, object] = {"timestamp_utc": timestamps, "equipment_id": plan.equipment_id}
    for channel in plan.channels:
        frame[channel.name] = series[channel.name]
    frame["regime"] = regime
    frame["anomaly_flag"] = anomaly_flag
    frame["note"] = notes

    df = pd.DataFrame(frame)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
    return df


def generate_all() -> dict[str, int]:
    spec.RAW_SENSORS.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for asset_index, plan in enumerate(spec.SENSOR_PLANS):
        df = _build_asset_frame(plan, asset_index)
        path = spec.RAW_SENSORS / f"{plan.equipment_id}_sensors.parquet"
        df.to_parquet(path, index=False, engine="pyarrow")
        counts[plan.equipment_id] = len(df)
    return counts


if __name__ == "__main__":
    for equipment_id, count in generate_all().items():
        print(f"{equipment_id}: {count} samples")
