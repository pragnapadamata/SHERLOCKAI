"""Retrieve prior engineer feedback relevant to an asset and render it as context.

Relevance = feedback targeting the asset id OR any of the asset's fault codes. The
provider returns the items, a context message for the specialist prompt, and the
SourceRefs so the conditioned answer cites which feedback shaped it.
"""

from __future__ import annotations

from backend.app.data_access.repositories import Repositories

_MAX_ITEMS = 5


class FeedbackContextProvider:
    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    def for_equipment(self, equipment_id: str) -> list[dict]:
        if not equipment_id:
            return []
        fault_codes = [f["fault_code"] for f in self._repos.faults.by_equipment(equipment_id)]
        items = self._repos.feedback.by_targets([equipment_id, *fault_codes])
        return items[:_MAX_ITEMS]

    @staticmethod
    def as_message(items: list[dict]) -> str | None:
        if not items:
            return None
        lines = []
        for it in items:
            detail = it.get("correction") or it.get("notes") or ""
            rating = f" rating={it['rating']}" if it.get("rating") is not None else ""
            lines.append(
                f"- [{it['feedback_type']} on {it['target_type']} {it['target_id']}{rating}] {detail}"
            )
        return (
            "Relevant prior engineer feedback for this equipment -- take it into account "
            "(this is conditioning context, not ground truth):\n" + "\n".join(lines)
        )

    @staticmethod
    def sources(items: list[dict]) -> list[dict]:
        return [{"kind": "record", "table": "feedback", "id": it["feedback_id"]} for it in items]
