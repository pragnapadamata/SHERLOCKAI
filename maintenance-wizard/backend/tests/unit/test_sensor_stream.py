"""The simulated sensor stream: cursor advance, window bounds, deterministic jump."""

from __future__ import annotations

from datetime import timedelta

from backend.app.proactive.stream import SensorStream


def test_cursor_starts_back_from_end_and_advances():
    stream = SensorStream(["HSM-F2-WRB"], start_days_back=21)
    start = stream.now
    assert start < stream.end
    stream.advance(timedelta(days=1))
    assert stream.now == start + timedelta(days=1)


def test_window_bounds_end_at_cursor():
    stream = SensorStream(["HSM-F2-WRB"])
    s, e = stream.window_bounds(timedelta(days=3))
    assert e == stream.now
    assert s == stream.now - timedelta(days=3)


def test_advance_to_jumps_and_clamps():
    stream = SensorStream(["HSM-F2-WRB"])
    stream.advance_to("2026-06-02T12:00:00")
    assert stream.now.isoformat().startswith("2026-06-02T12:00")
    # clamping beyond the recorded end
    stream.advance_to("2030-01-01T00:00:00")
    assert stream.now == stream.end


def test_current_readings_summarizes_live_window():
    stream = SensorStream(["HSM-F2-WRB"])
    stream.advance_to("2026-06-02T12:00:00")
    summary = stream.current_readings("HSM-F2-WRB", timedelta(days=3))
    assert summary["window"]["n_samples"] > 0
    assert "vibration_rms_mm_s" in summary["channels"]
