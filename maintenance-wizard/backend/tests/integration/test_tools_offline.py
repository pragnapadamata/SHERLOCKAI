"""Every tool end-to-end through the registry (temp DB + fake retriever)."""

from __future__ import annotations


def test_all_twelve_tools_registered(registry):
    assert len(registry.names()) == 12


def test_search_knowledge_returns_citations(registry):
    out = registry.get("search_knowledge").run(query="gear pitting", equipment_id="HSM-F3-GBX")
    assert out["ok"]
    assert out["sources"][0]["kind"] == "document"
    assert out["data"][0]["doc_id"]


def test_get_equipment_one_and_all(registry):
    one = registry.get("get_equipment").run(equipment_id="HSM-F3-GBX")
    assert one["ok"] and one["data"]["process_criticality"] == "critical"
    assert one["sources"][0]["kind"] == "record"
    every = registry.get("get_equipment").run()
    assert len(every["data"]) == 10


def test_get_sensor_data_is_summary(registry):
    out = registry.get("get_sensor_data").run(equipment_id="HSM-F3-GBX")
    assert out["ok"]
    data = out["data"]
    assert "channels" in data and "oil_fe_ppm" in data["channels"]
    assert data["regime"]["current"] in ("baseline", "degrading", "alert", "action")
    assert out["sources"][0]["kind"] == "sensor"
    assert "series" not in data  # summary by default


def test_get_sensor_data_rejects_unmonitored(registry):
    out = registry.get("get_sensor_data").run(equipment_id="HSM-DSC-PMP")
    assert out["ok"] is False


def test_get_maintenance_history_filtered(registry):
    out = registry.get("get_maintenance_history").run(equipment_id="HSM-F2-WRB", type="lubrication")
    assert out["ok"]
    assert all(r["type"] == "lubrication" for r in out["data"])


def test_get_spare_parts_by_id(registry):
    out = registry.get("get_spare_parts").run(part_id="GBX-GEAR-SET-01")
    assert out["ok"] and out["data"]["procurement_lead_time_weeks"] == 8


def test_get_fault_info_by_code_links_spares(registry):
    out = registry.get("get_fault_info").run(fault_code="F3-GBX-002")
    assert out["ok"]
    parts = [s["part_id"] for s in out["data"]["related_spares_detail"]]
    assert "GBX-GEAR-SET-01" in parts


def test_get_fault_info_by_symptoms(registry):
    out = registry.get("get_fault_info").run(symptoms="gear sidebands oil iron particle trend")
    assert out["ok"]
    assert out["data"][0]["fault_code"] == "F3-GBX-002"
    assert out["data"][0]["matched_terms"]


def test_get_equipment_logs(registry):
    out = registry.get("get_equipment_logs").run(equipment_id="HSM-F3-GBX")
    assert out["ok"]
    assert "delays" in out["data"] and "incidents" in out["data"]


def test_get_process_conditions(registry):
    out = registry.get("get_process_conditions").run(equipment_id="HSM-F3-GBX")
    assert out["ok"] and out["data"]


def test_compute_priority_all_ranks_f3_high(registry):
    out = registry.get("compute_priority").run()
    assert out["ok"]
    f3 = next(d for d in out["data"] if d["equipment_id"] == "HSM-F3-GBX")
    assert f3["rank"] <= 2 and f3["vital_few"]


def test_log_action_then_get_logbook(registry):
    written = registry.get("log_maintenance_action").run(
        equipment_id="HSM-F3-GBX", text="trend re-checked", author_user_id="U-ENG-01",
    )
    assert written["ok"]
    entry_id = written["data"]["entry_id"]
    book = registry.get("get_logbook").run(equipment_id="HSM-F3-GBX")
    assert any(e["entry_id"] == entry_id for e in book["data"])


def test_log_action_rejects_unknown_equipment(registry):
    out = registry.get("log_maintenance_action").run(equipment_id="NOPE", text="x")
    assert out["ok"] is False


def test_record_feedback(registry):
    out = registry.get("record_feedback").run(
        target_type="diagnosis", feedback_type="confirmation", author_user_id="U-ENG-01",
    )
    assert out["ok"] and out["data"]["feedback_id"].startswith("FB-")
