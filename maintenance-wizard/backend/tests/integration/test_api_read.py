"""Read endpoints: health, me, dashboard, logbook (offline, zero tokens)."""

from __future__ import annotations


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_me_default_and_header(client):
    default = client.get("/api/me").json()
    assert default["user_id"] == "U-ENG-01"
    pm = client.get("/api/me", headers={"X-User-Id": "U-PM-01"}).json()
    assert pm["role"] == "plant_manager"


def test_dashboard_equipment_lists_with_monitored_flag(client):
    rows = client.get("/api/dashboard/equipment").json()
    assert len(rows) == 10
    by_id = {r["equipment_id"]: r for r in rows}
    assert by_id["HSM-F2-WRB"]["monitored"] is True
    assert by_id["HSM-DSC-PMP"]["monitored"] is False


def test_dashboard_priority_ranks_f3_high(client):
    data = client.get("/api/dashboard/priority").json()
    assert data and "priority_score" in data[0]
    top_two = {d["equipment_id"] for d in data[:2]}
    assert "HSM-F3-GBX" in top_two


def test_dashboard_sensors_summary_and_404(client):
    ok = client.get("/api/dashboard/sensors/HSM-F3-GBX")
    assert ok.status_code == 200 and "channels" in ok.json()
    missing = client.get("/api/dashboard/sensors/HSM-DSC-PMP")  # unmonitored, no parquet
    assert missing.status_code == 404


def test_dashboard_equipment_detail(client):
    detail = client.get("/api/dashboard/equipment/HSM-F3-GBX").json()
    assert detail["equipment"]["equipment_id"] == "HSM-F3-GBX"
    assert "sensors" in detail and "open_tickets" in detail and "logbook" in detail


def test_logbook_lists(client):
    rows = client.get("/api/logbook").json()
    assert isinstance(rows, list) and len(rows) >= 15  # seed entries
