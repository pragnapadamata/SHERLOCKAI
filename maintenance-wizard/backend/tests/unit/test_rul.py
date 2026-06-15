"""RUL: F3 lands ~8-14 wk to the ISO damage threshold; DC is stable."""

from __future__ import annotations


def test_f3_gearbox_rul_in_story_range(rul_estimator):
    r = rul_estimator.estimate("HSM-F3-GBX")
    assert r.status == "degrading"
    assert 8.0 <= r.rul_weeks <= 14.0
    assert r.governing_channel == "vibration_rms_mm_s"
    assert r.failure_threshold == 4.5  # ISO damage onset, not action
    assert r.rul_interval_weeks[0] < r.rul_weeks < r.rul_interval_weeks[1]
    assert r.time_to_action_weeks is not None and r.time_to_action_weeks < r.rul_weeks
    assert r.trend["method"].startswith("Theil-Sen")


def test_f3_rul_interval_low_supports_procurement_trigger(rul_estimator):
    # Lower bound must reach the 8-week spare lead time so "order now" fires.
    r = rul_estimator.estimate("HSM-F3-GBX")
    assert r.rul_interval_weeks[0] <= 8.0


def test_downcoiler_is_stable(rul_estimator):
    r = rul_estimator.estimate("HSM-DC-MND")
    assert r.status == "stable"
    assert r.rul_weeks is None
