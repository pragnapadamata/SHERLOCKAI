"""Phase 3 tools via the registry, including risk-wired compute_priority."""

from __future__ import annotations

import pandas as pd

from backend.app.core.config import ROUND1_DIR


def test_registry_has_sixteen_tools(ml_registry):
    assert len(ml_registry.names()) == 16  # 12 from Phase 2 + 4 ML tools


def test_detect_anomaly_tool_reports_model_and_drivers(ml_registry):
    out = ml_registry.get("detect_anomaly").run(equipment_id="HSM-F2-WRB")
    assert out["ok"] and out["data"]["is_anomaly"]
    comp = next(s for s in out["sources"] if s["kind"] == "computation")
    assert comp["model"] == "IsolationForest"
    assert comp["drivers"]


def test_predict_rul_tool_in_range(ml_registry):
    out = ml_registry.get("predict_rul").run(equipment_id="HSM-F3-GBX")
    assert out["ok"]
    data = out["data"]
    assert 8.0 <= data["rul_weeks"] <= 14.0
    assert data["time_to_action_weeks"] < data["rul_weeks"]
    comp = next(s for s in out["sources"] if s["kind"] == "computation")
    assert comp["model"] == "Theil-Sen"


def test_assess_alpha_defect_risk_tool(ml_registry):
    train = pd.read_csv(ROUND1_DIR / "train.csv")
    coil_id = str(train.loc[train["Y"] == 1, "CoilID"].iloc[0])
    out = ml_registry.get("assess_alpha_defect_risk").run(coil_id=coil_id)
    assert out["ok"]
    assert 0.0 <= out["data"]["risk_score"] <= 1.0
    assert out["data"]["cv_metrics"]["recall_at_threshold"] >= 0.90 - 1e-9
    assert out["data"]["top_driver_features"]


def test_assess_early_warning_tool_fires_procurement(ml_registry):
    out = ml_registry.get("assess_early_warning").run(equipment_id="HSM-F3-GBX")
    assert out["ok"] and out["data"]["early_warning"]
    assert "procurement_at_risk" in [t["type"] for t in out["data"]["triggers"]]


def test_compute_priority_shows_dynamic_risk_and_bumps_f3(ml_registry):
    out = ml_registry.get("compute_priority").run()
    assert out["ok"]
    f3 = next(d for d in out["data"] if d["equipment_id"] == "HSM-F3-GBX")
    assert "dynamic_risk" in [c["dimension"] for c in f3["components"]]
    assert f3["priority_score"] > f3["base_score"]  # bumped by low RUL


def test_compute_priority_single_asset_has_risk_component(ml_registry):
    out = ml_registry.get("compute_priority").run(equipment_id="HSM-F3-GBX")
    assert out["ok"]
    assert any(c["dimension"] == "dynamic_risk" for c in out["components"])
    assert out["data"]["priority_score"] > out["data"]["base_score"]
