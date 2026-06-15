"""detect_anomaly must never crash on an empty/out-of-range window (it falls back to the
latest available window) -- the bug that crashed the agent when it guessed a 2024 date.
"""

from __future__ import annotations


def test_out_of_range_window_falls_back_to_latest(anomaly_detector):
    # A wrong-year window has zero samples; the scorer must fall back, not raise
    # "argmax of an empty sequence".
    result = anomaly_detector.score(
        "HSM-F2-WRB", start="2024-01-01T00:00:00", end="2024-01-08T00:00:00"
    )
    assert result.equipment_id == "HSM-F2-WRB"
    assert result.window["n_samples"] > 0  # fell back to the latest (2026) window


def test_normal_window_still_works(anomaly_detector):
    result = anomaly_detector.score("HSM-F2-WRB")
    assert result.window["n_samples"] > 0
    assert result.threshold > 0
