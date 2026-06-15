"""Anomaly detection: flags Story B's spike with named channels; calm is clean."""

from __future__ import annotations


def test_f2_bearing_spike_flagged_with_channels(anomaly_detector):
    r = anomaly_detector.score("HSM-F2-WRB")
    assert r.is_anomaly
    drivers = [c["channel"] for c in r.contributing_channels]
    assert "vibration_rms_mm_s" in drivers
    assert r.severity > 0.5  # the spike reaches the ISO damage zone
    assert r.iso_regime  # reconciliation present
    assert r.contributing_channels[0]["z_score"] != 0


def test_f3_baseline_window_not_flagged(anomaly_detector):
    # First weeks are the calm baseline regime.
    r = anomaly_detector.score("HSM-F3-GBX", start="2026-02-14", end="2026-03-14")
    assert not r.is_anomaly


def test_isolation_forest_corroboration_reported(anomaly_detector):
    r = anomaly_detector.score("HSM-F2-WRB")
    assert isinstance(r.isolation_forest_score, float)
    assert "at_anomaly" in r.iso_regime


def test_score_accepts_timezone_aware_window(anomaly_detector):
    # The orchestrating LLM may pass tz-aware ISO timestamps; read_window must cope.
    r = anomaly_detector.score(
        "HSM-F3-GBX", start="2026-05-01T00:00:00Z", end="2026-06-06T06:00:00Z"
    )
    assert r.window["n_samples"] > 0
