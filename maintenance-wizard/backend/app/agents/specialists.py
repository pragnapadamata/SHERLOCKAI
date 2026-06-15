"""One shared specialist framework instantiated in six roles.

A ``SpecialistTool`` is a Tool the orchestrator can call. Internally it runs the
Phase 0 bounded loop over its tool allowlist with its role prompt, then returns a
``SpecialistResult`` whose prose is the loop's conclusion and whose key_facts and
provenance are harvested programmatically from the tool results it actually called
(robust and traceable -- not trusted from LLM-formatted JSON).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar

from backend.app.agents import prompts
from backend.app.agents.contracts import SpecialistResult
from backend.app.agents.loop import ToolLoopError, run_tool_loop
from backend.app.agents.provenance import dedup, harvest, sources_from_result
from backend.app.agents.schemas import ToolInvocation
from backend.app.llm.base import LLMClient
from backend.app.llm.messages import Message
from backend.app.tools.base import Tool, ToolRegistry

KeyFactExtractor = Callable[[list[ToolInvocation]], dict]


def _result_of(invocations: list[ToolInvocation], tool_name: str) -> dict | None:
    for inv in invocations:
        if inv.tool == tool_name and inv.ok and isinstance(inv.result, dict):
            return inv.result
    return None


def _first_item(data: Any) -> dict | None:
    if isinstance(data, dict):
        return data
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0]
    return None


def _diagnostic_facts(invs: list[ToolInvocation]) -> dict:
    facts: dict = {}
    fi = _result_of(invs, "get_fault_info")
    item = _first_item(fi.get("data")) if fi else None
    if item:
        facts["probable_fault_code"] = item.get("fault_code")
        facts["fault_title"] = item.get("title")
    anomaly = _result_of(invs, "detect_anomaly")
    if anomaly and isinstance(anomaly.get("data"), dict):
        facts["anomaly"] = anomaly["data"].get("is_anomaly")
    return facts


def _root_cause_facts(invs: list[ToolInvocation]) -> dict:
    precedents = set()
    for inv in invs:
        for ref in sources_from_result(inv.result or {}):
            if ref.get("kind") == "document" and ref.get("doc_type") == "failure_report":
                precedents.add(ref.get("doc_id"))
    return {"precedent_reports": sorted(p for p in precedents if p)} if precedents else {}


def _predictive_facts(invs: list[ToolInvocation]) -> dict:
    facts: dict = {}
    rul = _result_of(invs, "predict_rul")
    if rul and isinstance(rul.get("data"), dict):
        d = rul["data"]
        facts.update(rul_weeks=d.get("rul_weeks"), rul_interval_weeks=d.get("rul_interval_weeks"),
                     status=d.get("status"), time_to_action_weeks=d.get("time_to_action_weeks"))
    ew = _result_of(invs, "assess_early_warning")
    if ew and isinstance(ew.get("data"), dict):
        facts.update(early_warning=ew["data"].get("early_warning"), severity=ew["data"].get("severity"))
    return facts


def _risk_facts(invs: list[ToolInvocation]) -> dict:
    facts: dict = {}
    cp = _result_of(invs, "compute_priority")
    item = _first_item(cp.get("data")) if cp else None
    if item:
        facts.update(priority_score=item.get("priority_score"), vital_few=item.get("vital_few"))
    ew = _result_of(invs, "assess_early_warning")
    if ew and isinstance(ew.get("data"), dict):
        facts["severity"] = ew["data"].get("severity")
    return facts


def _recommendation_facts(invs: list[ToolInvocation]) -> dict:
    sp = _result_of(invs, "get_spare_parts")
    item = _first_item(sp.get("data")) if sp else None
    if item:
        return {"spare": {"part_id": item.get("part_id"),
                          "lead_weeks": item.get("procurement_lead_time_weeks"),
                          "availability": item.get("spare_availability")}}
    return {}


def _reporting_facts(invs: list[ToolInvocation]) -> dict:
    lg = _result_of(invs, "log_maintenance_action")
    if lg and isinstance(lg.get("data"), dict):
        return {"logged_entry_id": lg["data"].get("entry_id")}
    return {}


@dataclass
class SpecialistSpec:
    name: str
    description: str
    system_prompt: str
    allow: list[str]
    key_facts: KeyFactExtractor = field(default=lambda _invs: {})


ANALYSIS_SPECS: list[SpecialistSpec] = [
    SpecialistSpec(
        name="diagnostic",
        description="Diagnose the probable fault(s) for an asset from symptoms and sensors. "
                    "Args: equipment_id, focus.",
        system_prompt=prompts.DIAGNOSTIC_SYSTEM,
        allow=["search_knowledge", "get_fault_info", "get_sensor_data", "get_equipment", "detect_anomaly"],
        key_facts=_diagnostic_facts,
    ),
    SpecialistSpec(
        name="root_cause",
        description="Find the root cause using history, logs, and precedents. Args: equipment_id, focus.",
        system_prompt=prompts.ROOT_CAUSE_SYSTEM,
        allow=["search_knowledge", "get_maintenance_history", "get_equipment_logs", "get_fault_info",
               "get_sensor_data"],
        key_facts=_root_cause_facts,
    ),
    SpecialistSpec(
        name="predictive",
        description="Estimate RUL / degradation and early warning. Args: equipment_id, focus.",
        system_prompt=prompts.PREDICTIVE_SYSTEM,
        allow=["predict_rul", "detect_anomaly", "assess_early_warning", "get_sensor_data"],
        key_facts=_predictive_facts,
    ),
    SpecialistSpec(
        name="risk_priority",
        description="Classify risk and place the asset in plant priority. Args: equipment_id, focus.",
        system_prompt=prompts.RISK_SYSTEM,
        allow=["compute_priority", "assess_early_warning", "get_equipment", "get_spare_parts"],
        key_facts=_risk_facts,
    ),
    SpecialistSpec(
        name="recommendation",
        description="Immediate + long-term actions and spare-procurement strategy. "
                    "Args: equipment_id, focus.",
        system_prompt=prompts.RECOMMENDATION_SYSTEM,
        allow=["search_knowledge", "get_spare_parts", "get_fault_info", "get_maintenance_history"],
        key_facts=_recommendation_facts,
    ),
]

REPORTING_SPEC = SpecialistSpec(
    name="reporting",
    description="Assemble the final cited summary from specialist findings.",
    system_prompt=prompts.REPORTING_SYSTEM,
    # Tool-less: synthesis is pure prose. Free-tier llama tool-calling is flaky and
    # synthesis needs no tools; logging is handled deterministically by the
    # orchestrator only when the user explicitly asks.
    allow=[],
    key_facts=_reporting_facts,
)


class SpecialistTool(Tool):
    """A bounded specialist loop, callable as a Tool."""

    name: ClassVar[str]
    description: ClassVar[str]
    parameters: ClassVar[dict]

    def __init__(self, spec: SpecialistSpec, registry: ToolRegistry, llm: LLMClient,
                 max_iters: int = 5, feedback_provider: Any | None = None) -> None:
        self._spec = spec
        self._registry = registry
        self._llm = llm
        self._max_iters = max_iters
        self._feedback = feedback_provider
        self.name = spec.name
        self.description = spec.description
        self.parameters = {
            "type": "object",
            "properties": {
                "equipment_id": {"type": "string", "description": "Asset id, if the task is asset-specific."},
                "focus": {"type": "string", "description": "What to investigate (the sub-question)."},
            },
            "required": ["focus"],
            "additionalProperties": False,
        }

    def investigate(self, focus: str, equipment_id: str | None = None) -> SpecialistResult:
        task = focus if not equipment_id else f"Equipment: {equipment_id}\n\nTask: {focus}"
        messages = [
            Message(role="system", content=self._spec.system_prompt),
            Message(role="user", content=task),
        ]

        # Feedback-conditioned context (FR6): inject prior feedback for this asset.
        feedback_sources: list[dict] = []
        if self._feedback is not None and equipment_id:
            items = self._feedback.for_equipment(equipment_id)
            note = self._feedback.as_message(items)
            if note:
                messages.insert(1, Message(role="system", content=note))
                feedback_sources = self._feedback.sources(items)

        try:
            ar = run_tool_loop(messages, llm=self._llm, tools=self._registry,
                               allow=self._spec.allow, max_iters=self._max_iters)
        except ToolLoopError as exc:
            ar = exc.result  # bounded but dependable: use the partial findings

        tokens_in = sum(p.tokens_in or 0 for p in ar.provenance)
        tokens_out = sum(p.tokens_out or 0 for p in ar.provenance)
        return SpecialistResult(
            role=self._spec.name,
            summary=ar.content or "",
            key_facts=self._spec.key_facts(ar.tool_invocations),
            provenance=dedup(harvest(ar.tool_invocations) + feedback_sources),
            tools_used=[inv.tool for inv in ar.tool_invocations],
            iterations=ar.iterations,
            stop_reason=ar.stop_reason,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )

    def run(self, focus: str, equipment_id: str | None = None) -> dict:
        return self.investigate(focus, equipment_id).to_compact()


def build_specialists(registry: ToolRegistry, llm: LLMClient, max_iters: int,
                      feedback_provider: Any | None = None) -> dict[str, SpecialistTool]:
    """The five analysis specialists as orchestrator-callable tools."""

    return {
        spec.name: SpecialistTool(spec, registry, llm, max_iters, feedback_provider=feedback_provider)
        for spec in ANALYSIS_SPECS
    }


def build_reporting(registry: ToolRegistry, llm: LLMClient, max_iters: int) -> SpecialistTool:
    return SpecialistTool(REPORTING_SPEC, registry, llm, max_iters)
