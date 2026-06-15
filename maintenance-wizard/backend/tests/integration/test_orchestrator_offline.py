"""Orchestrator offline: depth control, delegation, provenance, bounds, memory.

Everything runs with scripted FakeLLMs (zero tokens, no key) but real tools, so
planning, delegation, and provenance bubbling are exercised end to end.
"""

from __future__ import annotations

from backend.app.conversation.memory import ConversationMemory
from backend.tests.fakes import build_scripted_orchestrator, text_result, tool_call_result


def test_trivial_query_stays_shallow(ml_registry):
    mem = ConversationMemory(clock=lambda: "t")
    orch = build_scripted_orchestrator(
        ml_registry, mem,
        orchestrator_script=[
            tool_call_result("c1", "get_spare_parts", {"part_id": "GBX-GEAR-SET-01"}),
            text_result("The F3 gear set (GBX-GEAR-SET-01) lead time is 8 weeks, on order."),
        ],
        specialist_scripts={},
        reporting_script=[text_result("should not be called")],
    )
    result = orch.run("What's the lead time on the F3 gear set?", "s")

    assert result.specialists_used == []  # no specialists, no reporting step
    assert "8" in result.answer
    assert any(p.get("table") == "spare_parts_master" for p in result.provenance)
    assert [p["tool"] for p in result.plan] == ["get_spare_parts"]


def test_analytical_query_delegates_and_reporting_assembles(ml_registry):
    mem = ConversationMemory(clock=lambda: "t")
    orch = build_scripted_orchestrator(
        ml_registry, mem,
        orchestrator_script=[
            tool_call_result("o1", "diagnostic", {"equipment_id": "HSM-F3-GBX", "focus": "fault"}),
            tool_call_result("o2", "predictive", {"equipment_id": "HSM-F3-GBX", "focus": "rul"}),
            tool_call_result("o3", "recommendation", {"equipment_id": "HSM-F3-GBX", "focus": "actions"}),
            text_result("gathered: diagnostic, predictive, recommendation"),
        ],
        specialist_scripts={
            "diagnostic": [
                tool_call_result("d1", "get_fault_info", {"fault_code": "F3-GBX-002"}),
                text_result("F3-GBX-002 Stage-2 pitting."),
            ],
            "predictive": [
                tool_call_result("p1", "predict_rul", {"equipment_id": "HSM-F3-GBX"}),
                tool_call_result("p2", "assess_early_warning", {"equipment_id": "HSM-F3-GBX"}),
                text_result("RUL ~12 wk; procurement-at-risk."),
            ],
            "recommendation": [
                tool_call_result("r1", "get_spare_parts", {"part_id": "GBX-GEAR-SET-01"}),
                text_result("Order GBX-GEAR-SET-01 now."),
            ],
        },
        reporting_script=[
            text_result("Status of F3 (HSM-F3-GBX): fault F3-GBX-002 (Stage-2 pitting); "
                        "RUL ~12 wk; order spare GBX-GEAR-SET-01 (8-wk lead)."),
        ],
    )
    result = orch.run("What's the status of the F3 main drive gearbox?", "s")

    assert result.specialists_used == ["diagnostic", "predictive", "recommendation", "reporting"]
    assert [p["tool"] for p in result.plan] == ["diagnostic", "predictive", "recommendation"]
    assert "F3-GBX-002" in result.answer and "GBX-GEAR-SET-01" in result.answer
    # provenance bubbled up from the specialists' real tool calls
    record_tables = {p.get("table") for p in result.provenance if p.get("kind") == "record"}
    assert "spare_parts_master" in record_tables
    assert any(p.get("kind") == "computation" for p in result.provenance)  # from predict_rul


def test_bounds_do_not_crash(ml_registry):
    mem = ConversationMemory(clock=lambda: "t")
    # Orchestrator keeps calling a data tool, never finishing -> max_iters -> caught.
    orch = build_scripted_orchestrator(
        ml_registry, mem,
        orchestrator_script=[
            tool_call_result(f"o{i}", "get_equipment", {"equipment_id": "HSM-F3-GBX"})
            for i in range(20)
        ],
        specialist_scripts={},
        reporting_script=[text_result("unused")],
    )
    result = orch.run("status?", "s")
    assert result.stop_reason == "max_iters"
    assert result.answer  # graceful fallback, no exception


def test_turn_is_recorded_in_memory(ml_registry):
    mem = ConversationMemory(clock=lambda: "t")
    orch = build_scripted_orchestrator(
        ml_registry, mem,
        orchestrator_script=[
            tool_call_result("c1", "get_equipment", {"equipment_id": "HSM-F3-GBX"}),
            text_result("F3 is the main drive gearbox."),
        ],
        specialist_scripts={},
        reporting_script=[text_result("unused")],
    )
    orch.run("Tell me about F3", "s")
    turns = mem.get("s").turns
    assert [t.role for t in turns] == ["user", "assistant"]
    assert turns[1].provenance  # assistant turn carries provenance
