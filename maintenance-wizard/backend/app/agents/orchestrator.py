"""The planning orchestrator -- the agentic core.

A bounded loop (small model) plans and delegates to the analysis specialists (and
a few direct data tools for trivial queries), deciding depth so trivial questions
stay shallow. For analytical queries it then runs the Reporting specialist (large
model) once over the collected findings to assemble the final, grounded, cited
answer. Provenance from every tool the specialists used bubbles up, deduped.
"""

from __future__ import annotations

import json
from typing import Any

from backend.app.agents.contracts import OrchestratorResult
from backend.app.agents.events import emit, event_sink
from backend.app.agents.loop import ToolLoopError, run_tool_loop
from backend.app.agents.prompts import ORCHESTRATOR_SYSTEM
from backend.app.agents.provenance import dedup, harvest, sources_from_result
from backend.app.agents.specialists import SpecialistTool
from backend.app.conversation.memory import ConversationMemory
from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger
from backend.app.llm.base import LLMClient
from backend.app.llm.messages import Message
from backend.app.tools.base import ToolRegistry

log = get_logger(__name__)


class MaintenanceOrchestrator:
    def __init__(
        self,
        *,
        orchestrator_llm: LLMClient,
        orchestrator_registry: ToolRegistry,
        reporting: SpecialistTool,
        memory: ConversationMemory,
        analysis_specialist_names: set[str],
        roster_text: str,
        data_range_text: str = "",
        data_registry: ToolRegistry | None = None,
        ticket_service: Any | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._llm = orchestrator_llm
        self._registry = orchestrator_registry
        self._reporting = reporting
        self._memory = memory
        self._analysis = analysis_specialist_names
        self._roster = roster_text
        self._data_range = data_range_text
        self._data_registry = data_registry
        self._ticket_service = ticket_service
        self._settings = settings or get_settings()

    @staticmethod
    def _fallback_summary(findings: list[dict]) -> str:
        """Deterministic assembly if LLM synthesis fails -- always produces an answer."""

        parts = [f"[{f.get('role')}] {f.get('summary')}" for f in findings if f.get("summary")]
        return "\n\n".join(parts) or "No findings were produced."

    @staticmethod
    def _equipment_from_plan(plan: list[dict]) -> str | None:
        for step in plan:
            eq = (step.get("args") or {}).get("equipment_id")
            if eq:
                return eq
        return None

    def _maybe_log(self, query: str, summary: str, equipment_id: str | None) -> dict | None:
        """Write a logbook entry only when the user explicitly asks (Q4)."""

        if not equipment_id or self._data_registry is None:
            return None
        if not any(kw in query.lower() for kw in ("log", "record", "logbook")):
            return None
        try:
            return self._data_registry.get("log_maintenance_action").run(
                equipment_id=equipment_id, text=summary[:480], entry_type="observation",
            )
        except Exception as exc:  # noqa: BLE001 -- logging must never break the answer
            log.warning("logbook_write_failed", error=str(exc))
            return None

    @staticmethod
    def _severity_from_findings(findings: list[dict]):
        from backend.app.tickets.models import Severity

        rank = {"critical": Severity.CRITICAL, "high": Severity.HIGH}
        for f in findings:
            sev = (f.get("key_facts") or {}).get("severity")
            if sev in rank:
                return rank[sev]
        return Severity.MEDIUM

    def _maybe_create_ticket(self, query: str, *, equipment_id: str | None, answer: str,
                             findings: list[dict], provenance: list[dict]):
        """Open a ticket only when the user explicitly asks (deterministic, never LLM-driven)."""

        if self._ticket_service is None or not equipment_id:
            return None
        if not any(kw in query.lower() for kw in ("ticket",)):
            return None
        from backend.app.tickets.models import TicketKind

        try:
            return self._ticket_service.create(
                equipment_id=equipment_id, severity=self._severity_from_findings(findings),
                kind=TicketKind.USER_REQUEST, title=f"User-requested ticket for {equipment_id}",
                originating_event={"type": "user_request", "query": query[:200]},
                answer=answer, findings=findings, provenance=provenance,
                recommended_actions=answer, author="user",
            )
        except Exception as exc:  # noqa: BLE001 -- ticketing must never break the answer
            log.warning("ticket_create_failed", error=str(exc))
            return None

    def _report_task(self, query: str, findings: list[dict]) -> str:
        return (
            f"User question: {query}\n\n"
            "Specialist findings (synthesize ONLY from these; introduce no other facts, "
            "and every number or id you state must appear here):\n"
            f"{json.dumps(findings, indent=2, default=str)}\n\n"
            "Write the final cited summary now."
        )

    def run(self, query: str, session_id: str = "default") -> OrchestratorResult:
        history = self._memory.history_messages(session_id, self._settings.history_max_turns)
        messages = [
            Message(role="system", content=ORCHESTRATOR_SYSTEM.format(
                roster=self._roster, data_range=self._data_range or "Recent 2026 operational data.")),
            *history,
            Message(role="user", content=query),
        ]

        emit({"type": "status", "message": "Routing and planning"})
        try:
            ar = run_tool_loop(messages, llm=self._llm, tools=self._registry,
                               max_iters=self._settings.orchestrator_max_iters)
        except ToolLoopError as exc:
            ar = exc.result  # bounded but dependable

        plan = [{"step": i + 1, "tool": inv.tool, "args": inv.arguments, "ok": inv.ok}
                for i, inv in enumerate(ar.tool_invocations)]

        specialist_invs = [inv for inv in ar.tool_invocations
                           if inv.tool in self._analysis and inv.ok and isinstance(inv.result, dict)]
        used = [inv.tool for inv in specialist_invs]

        provenance = harvest(ar.tool_invocations)
        tokens_in = sum(p.tokens_in or 0 for p in ar.provenance)
        tokens_out = sum(p.tokens_out or 0 for p in ar.provenance)
        for inv in ar.tool_invocations:
            if isinstance(inv.result, dict):
                tokens_in += int(inv.result.get("tokens_in") or 0)
                tokens_out += int(inv.result.get("tokens_out") or 0)

        findings: list[dict] = []
        if used:
            findings = [inv.result for inv in specialist_invs]
            emit({"type": "status", "message": "Synthesizing report"})
            report = self._reporting.investigate(self._report_task(query, findings))
            answer = report.summary or self._fallback_summary(findings)
            provenance = provenance + report.provenance
            tokens_in += report.tokens_in
            tokens_out += report.tokens_out
            specialists_used = [*used, "reporting"]
            log_result = self._maybe_log(query, answer, self._equipment_from_plan(plan))
            if log_result:
                provenance = provenance + sources_from_result(log_result)
                specialists_used = [*specialists_used, "logbook"]
        else:
            if ar.content:
                answer = ar.content
            else:
                # The loop ended without a narrative answer (e.g. max_iters on the live
                # path). Synthesize from whatever tool output we did collect so the
                # engineer still gets something useful, and guide them to a focused query.
                partial = [
                    f"- {inv.tool}: {inv.result.get('summary')}"
                    for inv in ar.tool_invocations
                    if inv.ok and isinstance(inv.result, dict) and inv.result.get("summary")
                ]
                if partial:
                    answer = (
                        "Here are the partial findings gathered before the analysis-step "
                        "limit was reached:\n\n" + "\n".join(partial) +
                        "\n\nFor a complete diagnosis, please re-ask about a single asset."
                    )
                else:
                    answer = (
                        "I couldn't complete a full analysis for that query. Try naming a "
                        "specific asset — for example, the F3 main-drive gearbox or the F2 "
                        "work-roll bearing — so I can run a focused diagnosis."
                    )
            specialists_used = used

        ticket = self._maybe_create_ticket(
            query, equipment_id=self._equipment_from_plan(plan), answer=answer,
            findings=findings, provenance=provenance,
        )
        if ticket is not None:
            answer = f"{answer}\n\nOpened ticket {ticket.ticket_id}."
            provenance = provenance + [{"kind": "record", "table": "tickets", "id": ticket.ticket_id}]
            specialists_used = [*specialists_used, "ticket"]

        provenance = dedup(provenance)
        self._memory.append(session_id, "user", query)
        self._memory.append(session_id, "assistant", answer, provenance=provenance)

        log.info("orchestrator_run", session=session_id, specialists=specialists_used,
                 iterations=ar.iterations, tokens_in=tokens_in, tokens_out=tokens_out)
        return OrchestratorResult(
            answer=answer, provenance=provenance, specialists_used=specialists_used,
            findings=findings, plan=plan, session_id=session_id, iterations=ar.iterations,
            stop_reason=ar.stop_reason, tokens_in=tokens_in, tokens_out=tokens_out,
        )

    def run_streaming(self, query: str, session_id: str, emit_fn) -> OrchestratorResult:
        """Run with live progress events. ``emit_fn`` receives each event dict.

        Every event is tagged with this run's session_id and routed only to this
        run's sink (a ContextVar), so concurrent streams never cross-contaminate.
        """

        def tagged(event: dict) -> None:
            event.setdefault("session_id", session_id)
            emit_fn(event)

        token = event_sink.set(tagged)
        try:
            result = self.run(query, session_id)
            tagged({"type": "final", **result.to_dict()})
            return result
        finally:
            event_sink.reset(token)
