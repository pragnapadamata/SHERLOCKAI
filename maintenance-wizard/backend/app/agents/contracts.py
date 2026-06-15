"""Phase 4 higher-level result contracts: specialist findings and the final answer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SpecialistResult:
    """A specialist's findings: prose conclusion + harvested key facts and provenance."""

    role: str
    summary: str
    key_facts: dict = field(default_factory=dict)
    provenance: list[dict] = field(default_factory=list)  # deduped SourceRef dicts
    tools_used: list[str] = field(default_factory=list)
    iterations: int = 0
    stop_reason: str = "completed"
    tokens_in: int = 0
    tokens_out: int = 0

    def to_compact(self) -> dict:
        """The compact view handed back to the orchestrator loop (no raw evidence)."""

        return {
            "role": self.role,
            "summary": self.summary,
            "key_facts": self.key_facts,
            "provenance": self.provenance,
            "tools_used": self.tools_used,
            "stop_reason": self.stop_reason,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
        }


@dataclass
class OrchestratorResult:
    """The orchestrator's final, cited answer plus the trace behind it."""

    answer: str
    provenance: list[dict] = field(default_factory=list)
    specialists_used: list[str] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)  # per-specialist compact results
    plan: list[dict] = field(default_factory=list)
    session_id: str = "default"
    iterations: int = 0
    stop_reason: str = "completed"
    tokens_in: int = 0
    tokens_out: int = 0

    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "provenance": self.provenance,
            "specialists_used": self.specialists_used,
            "findings": self.findings,
            "plan": self.plan,
            "session_id": self.session_id,
            "iterations": self.iterations,
            "stop_reason": self.stop_reason,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
        }
