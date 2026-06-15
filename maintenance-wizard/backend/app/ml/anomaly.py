"""Multivariate anomaly detection per hero asset, explainable by channel.

Decision is a transparent robust residual z-score from a per-asset baseline
(median + scaled MAD over the baseline-regime window); an IsolationForest fit on
the same baseline corroborates as a recognized multivariate method. Attribution
names the channels that drove the score. Severity is mapped from the ISO zone of
the worst sample (for the priority risk_modifier), reconciling with the ISO
``regime`` column already in the data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np

from backend.app.core.config import RAW_SENSORS, get_settings
from backend.app.core.logging import get_logger
from backend.app.data_access import sensors

log = get_logger(__name__)

_EPS = 1e-6


@dataclass
class AnomalyResult:
    equipment_id: str
    window: dict
    is_anomaly: bool
    anomaly_score: float
    threshold: float
    severity: float  # 0..1 from ISO zone of the worst sample (for risk)
    isolation_forest_score: float
    iforest_outlier: bool
    contributing_channels: list[dict] = field(default_factory=list)
    iso_regime: dict = field(default_factory=dict)
    max_anomaly_at: str | None = None


def _equipment_ids(sensors_dir: Path) -> list[str]:
    return sorted(p.name.replace("_sensors.parquet", "") for p in sensors_dir.glob("*_sensors.parquet"))


def train_anomaly_models(models_dir: str | Path | None = None,
                         sensors_dir: Path | None = None, seed: int | None = None) -> list[str]:
    """Fit and persist a baseline + IsolationForest per monitored asset."""

    from sklearn.ensemble import IsolationForest

    settings = get_settings()
    seed = seed if seed is not None else settings.random_seed
    sensors_dir = sensors_dir or RAW_SENSORS
    out_dir = Path(models_dir or settings.models_dir) / "anomaly"
    out_dir.mkdir(parents=True, exist_ok=True)

    trained = []
    for eid in _equipment_ids(sensors_dir):
        df = sensors.read_window(eid, sensors_dir=sensors_dir)
        channels = sensors.channel_names(df)
        baseline = df[df["regime"] == "baseline"] if "regime" in df.columns else df
        if len(baseline) < 50:
            baseline = df

        median = {c: float(baseline[c].median()) for c in channels}
        sigma = {
            c: float(max(1.4826 * (baseline[c] - baseline[c].median()).abs().median(), _EPS))
            for c in channels
        }
        iforest = IsolationForest(n_estimators=200, random_state=seed)
        iforest.fit(baseline[channels].to_numpy())

        primary = "vibration_rms_mm_s" if "vibration_rms_mm_s" in channels else channels[0]
        joblib.dump(
            {"channels": channels, "median": median, "sigma": sigma,
             "iforest": iforest, "primary_channel": primary},
            out_dir / f"{eid}.joblib",
        )
        trained.append(eid)
    log.info("anomaly_models_trained", count=len(trained))
    return trained


class AnomalyDetector:
    def __init__(self, models_dir: str | Path | None = None, sensors_dir: Path | None = None,
                 z_threshold: float | None = None, window_days: int | None = None) -> None:
        settings = get_settings()
        self._dir = Path(models_dir or settings.models_dir) / "anomaly"
        self._sensors_dir = sensors_dir or RAW_SENSORS
        self._z = z_threshold if z_threshold is not None else settings.anomaly_z_threshold
        self._window_days = window_days or settings.anomaly_window_days
        self._cache: dict[str, dict] = {}

    def available(self, equipment_id: str) -> bool:
        return (self._dir / f"{equipment_id}.joblib").exists()

    def _model(self, equipment_id: str) -> dict:
        if equipment_id not in self._cache:
            path = self._dir / f"{equipment_id}.joblib"
            if not path.exists():
                raise FileNotFoundError(f"No anomaly model for {equipment_id}; run train_models.")
            self._cache[equipment_id] = joblib.load(path)
        return self._cache[equipment_id]

    def score(self, equipment_id: str, *, last_n: int | None = None,
              start: str | None = None, end: str | None = None) -> AnomalyResult:
        model = self._model(equipment_id)
        if last_n is None and start is None and end is None:
            last_n = self._window_days * 144  # 10-minute sampling -> 144 samples/day
        df = sensors.read_window(equipment_id, last_n=last_n, start=start, end=end,
                                 sensors_dir=self._sensors_dir).reset_index(drop=True)
        if len(df) == 0:
            # Requested window is empty / out of range (e.g. a wrong-year date the agent
            # guessed) -> fall back to the latest available window so detection never
            # crashes mid-analysis ("argmax of an empty sequence").
            df = sensors.read_window(equipment_id, last_n=self._window_days * 144,
                                     sensors_dir=self._sensors_dir).reset_index(drop=True)
        if len(df) == 0:
            return AnomalyResult(
                equipment_id=equipment_id,
                window={"start": None, "end": None, "n_samples": 0},
                is_anomaly=False, anomaly_score=0.0, threshold=self._z, severity=0.0,
                isolation_forest_score=0.0, iforest_outlier=False,
            )

        channels = [c for c in model["channels"] if c in df.columns]
        z = np.zeros((len(df), len(channels)))
        for j, c in enumerate(channels):
            z[:, j] = (df[c].to_numpy() - model["median"][c]) / model["sigma"][c]
        per_sample = np.max(np.abs(z), axis=1)
        max_idx = int(np.argmax(per_sample))
        anomaly_score = float(per_sample[max_idx])

        order = np.argsort(-np.abs(z[max_idx]))
        contributing = [
            {
                "channel": channels[j],
                "z_score": round(float(z[max_idx, j]), 2),
                "value": round(float(df[channels[j]].iloc[max_idx]), 4),
                "baseline_median": round(model["median"][channels[j]], 4),
                "direction": "above" if z[max_idx, j] >= 0 else "below",
            }
            for j in order if abs(z[max_idx, j]) >= 1.0
        ][:4]

        iforest = model["iforest"]
        decision = iforest.decision_function(df[channels].to_numpy())
        iforest_score = float(np.min(decision))
        iforest_outlier = bool((iforest.predict(df[channels].to_numpy()) == -1).any())

        primary = model["primary_channel"]
        primary_max = float(df[primary].max()) if primary in df.columns else 0.0
        severity = float(np.clip(
            (primary_max - sensors.ISO_RMS_ALERT) / (sensors.ISO_RMS_DAMAGE - sensors.ISO_RMS_ALERT),
            0.0, 1.0,
        ))

        iso_regime = {}
        if "regime" in df.columns:
            iso_regime = {
                "at_anomaly": str(df["regime"].iloc[max_idx]),
                "current": str(df["regime"].iloc[-1]),
                "counts": {str(k): int(v) for k, v in df["regime"].value_counts().items()},
            }

        return AnomalyResult(
            equipment_id=equipment_id,
            window={"start": str(df["timestamp_utc"].min()), "end": str(df["timestamp_utc"].max()),
                    "n_samples": int(len(df))},
            is_anomaly=anomaly_score > self._z,
            anomaly_score=round(anomaly_score, 2),
            threshold=self._z,
            severity=round(severity, 3),
            isolation_forest_score=round(iforest_score, 4),
            iforest_outlier=iforest_outlier,
            contributing_channels=contributing,
            iso_regime=iso_regime,
            max_anomaly_at=str(df["timestamp_utc"].iloc[max_idx]),
        )
