"""Real-LLM proactive auto-response (slow; deselected; token-aware -- F2 only).

Run with a Groq key:  uv run pytest -m slow
"""

from __future__ import annotations

import pytest


@pytest.mark.slow
def test_f2_acute_autonomous_response_real():
    from backend.app.agents.factory import build_orchestrator
    from backend.app.core.config import get_settings
    from backend.app.data_access.db import connect
    from backend.app.data_access.repositories import build_repositories
    from backend.tests.fakes import build_proactive_engine

    settings = get_settings()
    repos = build_repositories(connect(settings=settings))
    orchestrator = build_orchestrator(settings)  # one real run, F2 only (token-aware)
    engine, tickets, alerts = build_proactive_engine(
        monitored=["HSM-F2-WRB"], orchestrator=orchestrator, repos=repos,
        models_dir=settings.models_dir,
    )

    engine.stream.advance_to("2026-06-02T12:00:00")
    outcomes = engine.poll()

    acute = [o for o in outcomes if o.kind == "acute_alarm"]
    assert acute, "expected an acute alarm on the F2 spike"
    ticket = tickets.get(acute[0].ticket_id)
    assert ticket.answer and ticket.provenance
