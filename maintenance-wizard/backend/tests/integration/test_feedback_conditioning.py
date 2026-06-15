"""Feedback-conditioned context: prior feedback is injected and cited (FR6)."""

from __future__ import annotations

from backend.app.agents.specialists import ANALYSIS_SPECS, SpecialistTool
from backend.app.feedback.context import FeedbackContextProvider
from backend.tests.fakes import FakeLLMClient, text_result, tool_call_result


def test_prior_feedback_is_injected_and_cited(tmp_repos, ml_registry):
    tmp_repos.feedback.append(
        target_type="fault", target_id="F3-GBX-002", feedback_type="correction", rating=None,
        correction="Verify the oil sample before ordering the gear set.",
        author_user_id="U-ENG-01", notes=None, created_at="2026-06-01T09:00:00",
    )
    provider = FeedbackContextProvider(tmp_repos)
    spec = next(s for s in ANALYSIS_SPECS if s.name == "diagnostic")
    fake = FakeLLMClient([
        tool_call_result("c1", "get_fault_info", {"fault_code": "F3-GBX-002"}),
        text_result("F3-GBX-002 pitting; per prior feedback, verifying oil sample first."),
    ])
    tool = SpecialistTool(spec, ml_registry, fake, max_iters=5, feedback_provider=provider)

    result = tool.investigate("diagnose current condition", "HSM-F3-GBX")

    # the prior feedback was injected into the specialist's context
    first_call = fake.calls[0]
    assert any("prior engineer feedback" in (m.content or "").lower() for m in first_call)
    # and is cited in the result provenance
    assert any(p.get("kind") == "record" and p.get("table") == "feedback" for p in result.provenance)


def test_no_feedback_no_injection(tmp_repos, ml_registry):
    provider = FeedbackContextProvider(tmp_repos)
    spec = next(s for s in ANALYSIS_SPECS if s.name == "diagnostic")
    fake = FakeLLMClient([text_result("nominal")])
    tool = SpecialistTool(spec, ml_registry, fake, max_iters=5, feedback_provider=provider)

    tool.investigate("diagnose", "HSM-DC-MND")
    first_call = fake.calls[0]
    assert not any("prior engineer feedback" in (m.content or "").lower() for m in first_call)
