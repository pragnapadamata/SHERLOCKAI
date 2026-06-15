"""Specialists offline: scripted LLM, real tools, harvested facts + provenance."""

from __future__ import annotations

from backend.app.agents.specialists import ANALYSIS_SPECS, SpecialistTool
from backend.tests.fakes import FakeLLMClient, text_result, tool_call_result


def _spec(name: str):
    return next(s for s in ANALYSIS_SPECS if s.name == name)


def test_diagnostic_harvests_fault_and_provenance(ml_registry):
    script = [
        tool_call_result("c1", "get_fault_info", {"fault_code": "F3-GBX-002"}),
        text_result("Probable fault F3-GBX-002: Stage-2 gear-tooth pitting."),
    ]
    tool = SpecialistTool(_spec("diagnostic"), ml_registry, FakeLLMClient(script), max_iters=5)
    result = tool.investigate("diagnose current condition", "HSM-F3-GBX")

    assert result.role == "diagnostic"
    assert result.key_facts.get("probable_fault_code") == "F3-GBX-002"
    assert "get_fault_info" in result.tools_used
    assert any(p.get("kind") == "record" and p.get("table") == "fault_catalog"
               for p in result.provenance)


def test_predictive_harvests_rul_and_early_warning(ml_registry):
    script = [
        tool_call_result("c1", "predict_rul", {"equipment_id": "HSM-F3-GBX"}),
        tool_call_result("c2", "assess_early_warning", {"equipment_id": "HSM-F3-GBX"}),
        text_result("RUL ~12 weeks; procurement-at-risk early warning."),
    ]
    tool = SpecialistTool(_spec("predictive"), ml_registry, FakeLLMClient(script), max_iters=5)
    result = tool.investigate("estimate RUL and early warning", "HSM-F3-GBX")

    assert 8.0 <= result.key_facts["rul_weeks"] <= 14.0
    assert result.key_facts["early_warning"] is True
    assert any(p.get("kind") == "computation" for p in result.provenance)


def test_recommendation_harvests_spare(ml_registry):
    script = [
        tool_call_result("c1", "get_spare_parts", {"part_id": "GBX-GEAR-SET-01"}),
        text_result("Order GBX-GEAR-SET-01 now given the 8-week lead time."),
    ]
    tool = SpecialistTool(_spec("recommendation"), ml_registry, FakeLLMClient(script), max_iters=5)
    result = tool.investigate("recommend actions", "HSM-F3-GBX")
    assert result.key_facts["spare"]["part_id"] == "GBX-GEAR-SET-01"
    assert result.key_facts["spare"]["lead_weeks"] == 8


def test_specialist_uses_partial_result_on_max_iters(ml_registry):
    # Script always calls a tool -> never concludes -> ToolLoopError caught -> partial.
    script = [tool_call_result(f"c{i}", "get_sensor_data", {"equipment_id": "HSM-F3-GBX"})
              for i in range(10)]
    tool = SpecialistTool(_spec("diagnostic"), ml_registry, FakeLLMClient(script), max_iters=2)
    result = tool.investigate("x", "HSM-F3-GBX")
    assert result.stop_reason == "max_iters"  # bounded, no crash
