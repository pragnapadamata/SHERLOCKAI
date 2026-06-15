"""Feedback context: retrieve prior feedback by asset + its fault codes."""

from __future__ import annotations

from backend.app.feedback.context import FeedbackContextProvider


def test_retrieves_feedback_for_asset_fault(tmp_repos):
    # Record a correction on a fault code of HSM-F3-GBX.
    tmp_repos.feedback.append(
        target_type="fault", target_id="F3-GBX-002", feedback_type="correction", rating=None,
        correction="Confirm with oil sample before ordering the gear set.",
        author_user_id="U-ENG-01", notes=None, created_at="2026-06-01T09:00:00",
    )
    provider = FeedbackContextProvider(tmp_repos)
    items = provider.for_equipment("HSM-F3-GBX")
    assert items and items[0]["target_id"] == "F3-GBX-002"

    note = provider.as_message(items)
    assert note and "oil sample" in note
    sources = provider.sources(items)
    assert sources[0]["kind"] == "record" and sources[0]["table"] == "feedback"


def test_no_feedback_returns_empty(tmp_repos):
    provider = FeedbackContextProvider(tmp_repos)
    assert provider.for_equipment("HSM-DC-MND") == []
    assert provider.as_message([]) is None
