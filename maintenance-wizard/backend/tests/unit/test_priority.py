"""compute_priority: transparent component math, ranking, and MTR flag."""

from __future__ import annotations

from backend.app.tools.maintenance.priority import ComputePriorityTool


def test_priority_ranks_and_breaks_down(tmp_repos):
    result = ComputePriorityTool(tmp_repos).run()
    assert result["ok"]
    data = result["data"]
    assert len(data) == 10

    scores = [d["priority_score"] for d in data]
    assert scores == sorted(scores, reverse=True)  # ranked descending

    f3 = next(d for d in data if d["equipment_id"] == "HSM-F3-GBX")
    assert f3["rank"] <= 2 and f3["vital_few"] is True

    components = f3["components"]
    assert len(components) == 4
    assert abs(sum(c["contribution"] for c in components) - f3["priority_score"]) < 0.5


def test_priority_single_asset_components(tmp_repos):
    result = ComputePriorityTool(tmp_repos).run(equipment_id="HSM-F3-GBX")
    assert result["ok"]
    assert result["components"] and len(result["components"]) == 4
    crit = next(c for c in result["components"] if c["dimension"] == "criticality")
    assert crit["normalized"] == 1.0  # 'critical' -> 1.0
    methods = [s for s in result["sources"] if s["kind"] == "computation"]
    assert methods and "weight" in methods[0]["method"]
    assert "criticality=" in methods[0]["detail"]


def test_priority_unknown_equipment(tmp_repos):
    result = ComputePriorityTool(tmp_repos).run(equipment_id="NOPE")
    assert result["ok"] is False
    assert "Unknown" in result["error"]
