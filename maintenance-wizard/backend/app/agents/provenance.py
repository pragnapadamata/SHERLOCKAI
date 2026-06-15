"""Harvest and dedup provenance so every answer traces to real artifacts.

Specialist results expose their harvested sources under ``provenance``; raw data
tools expose them under ``sources``. This module flattens both from a run's tool
invocations and dedups by a kind-specific key.
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.schemas import ToolInvocation


def sources_from_result(result: Any) -> list[dict]:
    """Pull SourceRef dicts from a tool result (specialist 'provenance' or tool 'sources')."""

    if isinstance(result, dict):
        refs = result.get("provenance")
        if refs is None:
            refs = result.get("sources")
        if isinstance(refs, list):
            return [r for r in refs if isinstance(r, dict)]
    return []


def harvest(invocations: list[ToolInvocation]) -> list[dict]:
    refs: list[dict] = []
    for inv in invocations:
        if inv.ok and inv.result is not None:
            refs.extend(sources_from_result(inv.result))
    return refs


def _key(ref: dict) -> tuple:
    kind = ref.get("kind")
    if kind == "document":
        return ("document", ref.get("doc_id"), ref.get("section"))
    if kind == "record":
        return ("record", ref.get("table"), ref.get("id"))
    if kind == "sensor":
        return ("sensor", ref.get("source"), ref.get("equipment_id"))
    if kind == "computation":
        return ("computation", ref.get("method"), ref.get("model"))
    return (kind, repr(sorted(ref.items())))


def dedup(refs: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    out: list[dict] = []
    for ref in refs:
        k = _key(ref)
        if k not in seen:
            seen.add(k)
            out.append(ref)
    return out
