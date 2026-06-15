"""Early warning: F2 acute, F3 procurement-at-risk, non-sensor assets quiet."""

from __future__ import annotations


def test_f2_acute_anomaly_is_critical(early_warning_service):
    r = early_warning_service.assess("HSM-F2-WRB")
    assert r.early_warning
    assert "acute_anomaly" in [t["type"] for t in r.triggers]
    assert r.severity == "critical"


def test_f3_procurement_at_risk_fires(early_warning_service):
    r = early_warning_service.assess("HSM-F3-GBX")
    assert r.early_warning
    types = [t["type"] for t in r.triggers]
    assert "procurement_at_risk" in types  # RUL lower bound <= 8-wk lead time


def test_non_sensor_asset_has_no_warning(early_warning_service):
    r = early_warning_service.assess("HSM-DSC-PMP")
    assert not r.early_warning
    assert r.severity == "none"
