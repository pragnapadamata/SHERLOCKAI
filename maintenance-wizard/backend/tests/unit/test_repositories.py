"""Repository reads/writes over a temp SQLite built from the committed CSVs."""

from __future__ import annotations


def test_equipment_get_and_all(tmp_repos):
    assert len(tmp_repos.equipment.all()) == 10
    f3 = tmp_repos.equipment.get("HSM-F3-GBX")
    assert f3["process_criticality"] == "critical"
    assert tmp_repos.equipment.get("NOPE") is None


def test_spares_lookup(tmp_repos):
    gear = tmp_repos.spares.by_part("GBX-GEAR-SET-01")
    assert gear["procurement_lead_time_weeks"] == 8
    assert any(s["part_id"] == "GBX-GEAR-SET-01" for s in tmp_repos.spares.by_equipment("HSM-F3-GBX"))


def test_fault_by_code_and_symptom_search(tmp_repos):
    fault = tmp_repos.faults.by_code("F3-GBX-002")
    assert "GBX-GEAR-SET-01" in fault["related_spares"]

    results = tmp_repos.faults.search_symptoms("gear sidebands oil iron particle trend")
    assert results
    assert results[0]["fault_code"] == "F3-GBX-002"
    assert results[0]["_matched_terms"]


def test_history_filtering(tmp_repos):
    rows = tmp_repos.history.query(equipment_id="HSM-F2-WRB", type="lubrication")
    assert rows
    assert all(r["type"] == "lubrication" and r["equipment_id"] == "HSM-F2-WRB" for r in rows)


def test_logbook_append_and_read(tmp_repos):
    rec = tmp_repos.logbook.append(
        equipment_id="HSM-F3-GBX", author_user_id="U-ENG-01", entry_type="observation",
        text="trend check", related_fault_code="F3-GBX-002", timestamp="2026-06-06T12:00:00",
    )
    assert rec["entry_id"].startswith("LB-")
    assert any(e["entry_id"] == rec["entry_id"] for e in tmp_repos.logbook.query("HSM-F3-GBX"))


def test_feedback_append(tmp_repos):
    rec = tmp_repos.feedback.append(
        target_type="diagnosis", target_id="x", feedback_type="confirmation", rating=None,
        correction=None, author_user_id="U-ENG-01", notes=None, created_at="2026-06-06T12:00:00",
    )
    assert rec["feedback_id"].startswith("FB-")
    assert len(tmp_repos.feedback.all()) == 1
