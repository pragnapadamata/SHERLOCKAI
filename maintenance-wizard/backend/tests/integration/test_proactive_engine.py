"""Proactive engine offline: both tiers, debounce, tickets, alerts, auto-log.

The orchestrator is scripted (FakeLLM) so the full detect -> debounce -> alert ->
ticket -> analysis -> auto-log flow runs with zero tokens.
"""

from __future__ import annotations

from backend.app.conversation.memory import ConversationMemory
from backend.app.data_access.db import query
from backend.tests.fakes import (
    build_proactive_engine,
    build_scripted_orchestrator,
    text_result,
    tool_call_result,
)


def _scripted(ml_registry, specialist, tool_name, tool_args, conclusion, report):
    mem = ConversationMemory(clock=lambda: "t")
    return build_scripted_orchestrator(
        ml_registry, mem,
        orchestrator_script=[
            tool_call_result("o1", specialist, {"equipment_id": "HSM", "focus": "f"}),
            text_result("gathered"),
        ],
        specialist_scripts={specialist: [tool_call_result("c1", tool_name, tool_args),
                                         text_result(conclusion)]},
        reporting_script=[text_result(report)],
    )


def test_acute_alarm_on_f2_spike(tmp_repos, ml_models_dir, ml_registry):
    orch = _scripted(ml_registry, "diagnostic", "get_fault_info", {"fault_code": "F2-WRB-001"},
                     "F2-WRB-001 lubrication starvation",
                     "Acute: fault F2-WRB-001; immediate lubrication + bearing replacement.")
    engine, tickets, alerts = build_proactive_engine(
        monitored=["HSM-F2-WRB"], orchestrator=orch, repos=tmp_repos, models_dir=ml_models_dir)

    engine.stream.advance_to("2026-06-02T12:00:00")
    outcomes = engine.poll()

    assert len(outcomes) == 1
    out = outcomes[0]
    assert out.kind == "acute_alarm" and out.equipment_id == "HSM-F2-WRB"

    ticket = tickets.get(out.ticket_id)
    assert ticket.kind == "acute_alarm" and ticket.status == "open"
    assert ticket.severity in ("high", "critical")
    assert ticket.answer and ticket.provenance  # autonomous analysis attached

    alert = alerts.list()[0]
    assert alert.ticket_id == out.ticket_id and alert.contributing_channels
    assert "plant_manager" in alert.audience_roles or "supervisor" in alert.audience_roles

    logs = query(tmp_repos.conn, "SELECT * FROM logbook WHERE author_user_id = 'U-SYS-AMDC'")
    assert logs and out.ticket_id in logs[0]["text"]  # auto-logged by the system user

    assert engine.poll() == []  # debounce: one episode = one alert


def test_predictive_advisory_on_f3(tmp_repos, ml_models_dir, ml_registry):
    orch = _scripted(ml_registry, "predictive", "predict_rul", {"equipment_id": "HSM-F3-GBX"},
                     "RUL ~12 wk; procurement-at-risk.",
                     "Advisory: F3 RUL ~12 wk; order the gear set now.")
    engine, tickets, _ = build_proactive_engine(
        monitored=["HSM-F3-GBX"], orchestrator=orch, repos=tmp_repos, models_dir=ml_models_dir)

    outcomes = engine.poll()
    assert len(outcomes) == 1
    assert outcomes[0].kind == "predictive_advisory"
    ticket = tickets.get(outcomes[0].ticket_id)
    assert ticket.kind == "predictive_advisory" and ticket.severity == "medium"
    assert engine.poll() == []  # debounce


def test_calm_asset_does_not_fire(tmp_repos, ml_models_dir, ml_registry):
    orch = _scripted(ml_registry, "diagnostic", "get_equipment", {"equipment_id": "HSM-DC-MND"},
                     "nominal", "nominal")
    engine, _, _ = build_proactive_engine(
        monitored=["HSM-DC-MND"], orchestrator=orch, repos=tmp_repos, models_dir=ml_models_dir)
    assert engine.poll() == []  # no acute crossing, no early warning
