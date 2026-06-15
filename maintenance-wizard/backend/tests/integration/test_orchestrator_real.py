"""Real-LLM hero-story end-to-end (slow; deselected by default).

Run with a Groq key in .env:  uv run pytest -m slow

Asserts correctness/grounding. Routing depth (the Q2 small-vs-large decision) is
observed via the chat_demo smoke, not hard-asserted here.
"""

from __future__ import annotations

import pytest

from backend.app.agents.factory import build_orchestrator


@pytest.mark.slow
def test_hero_story_f3_status_is_grounded():
    orch = build_orchestrator()
    result = orch.run("What's the status of the F3 main drive gearbox?", "real-hero")

    assert result.specialists_used, "expected the orchestrator to consult specialists"
    assert "reporting" in result.specialists_used
    answer = result.answer.lower()
    assert any(token in answer for token in ("f3-gbx-002", "gbx-gear-set-01", "gear")), answer
    assert result.provenance  # traceable sources attached
    assert result.tokens_in > 0


@pytest.mark.slow
def test_trivial_query_answer_is_correct():
    orch = build_orchestrator()
    result = orch.run(
        "What is the procurement lead time for the F3 gear set, part GBX-GEAR-SET-01?",
        "real-trivial",
    )
    assert "8" in result.answer  # 8-week lead time
