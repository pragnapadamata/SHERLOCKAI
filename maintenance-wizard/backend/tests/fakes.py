"""Offline test doubles.

``FakeLLMClient`` returns a queue of scripted ``ChatResult`` objects in order,
so the agent loop and anything built on the LLM client can be tested with no
network and no API key. ``tool_call_result`` and ``text_result`` build the two
shapes of response the loop cares about.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from pathlib import Path

from backend.app.data_access.db import connect
from backend.app.data_access.loader import build_database
from backend.app.data_access.repositories import Repositories, build_repositories
from backend.app.llm.base import LLMClient
from backend.app.llm.messages import (
    ChatResult,
    Message,
    Provenance,
    ToolCall,
    ToolSpec,
)
from backend.app.retrieval.ingest import ingest_documents
from backend.app.retrieval.retriever import KnowledgeRetriever
from backend.app.retrieval.vector_store import VectorStore


def _provenance(tier: str = "test", model: str = "fake-model") -> Provenance:
    return Provenance(
        provider="fake",
        model=model,
        tier=tier,
        latency_ms=1.0,
        tokens_in=1,
        tokens_out=1,
    )


class FakeLLMClient(LLMClient):
    """An LLM client that replays scripted responses and records its calls."""

    def __init__(
        self,
        scripted: Sequence[ChatResult],
        *,
        model: str = "fake-model",
        tier: str = "test",
    ) -> None:
        super().__init__(model=model, api_key=None, tier=tier)
        self._scripted: list[ChatResult] = list(scripted)
        self.calls: list[list[Message]] = []

    @property
    def provider(self) -> str:
        return "fake"

    def chat(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec] | None = None,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatResult:
        self.calls.append(list(messages))
        if not self._scripted:
            raise AssertionError("FakeLLMClient ran out of scripted responses.")
        return self._scripted.pop(0)


def tool_call_result(call_id: str, name: str, arguments: dict) -> ChatResult:
    """A scripted response that asks to call one tool."""

    return ChatResult(
        content=None,
        tool_calls=[ToolCall(id=call_id, name=name, arguments=arguments)],
        provenance=_provenance(),
    )


def text_result(text: str) -> ChatResult:
    """A scripted response that is a final text answer (no tool calls)."""

    return ChatResult(content=text, tool_calls=[], provenance=_provenance())


# --------------------------------------------------------------------------- #
# Retrieval fakes (deterministic, no model downloads)
# --------------------------------------------------------------------------- #

_DIM = 64


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class FakeEmbedder:
    """Deterministic bag-of-words hashing embedder (shared words -> similar)."""

    dim = _DIM

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * _DIM
        for tok in _tokens(text):
            idx = int.from_bytes(hashlib.blake2b(tok.encode(), digest_size=4).digest(), "big") % _DIM
            v[idx] += 1.0
        norm = sum(x * x for x in v) ** 0.5 or 1.0
        return [x / norm for x in v]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)


class FakeReranker:
    """Lexical-overlap reranker (count of shared tokens)."""

    def rerank(self, query: str, documents: list[str]) -> list[float]:
        q = set(_tokens(query))
        return [float(len(q & set(_tokens(d)))) for d in documents]


def build_temp_repositories(db_path: Path) -> Repositories:
    """Build a SQLite DB from the committed CSVs at db_path and return repos."""

    build_database(db_path=str(db_path))
    return build_repositories(connect(path=str(db_path)))


def build_fake_retriever() -> KnowledgeRetriever:
    """An ephemeral Chroma + fake embedder/reranker over the committed documents."""

    from backend.scripts.build_index import build_doc_inputs

    store = VectorStore.ephemeral()
    embedder = FakeEmbedder()
    ingest_documents(store, embedder, build_doc_inputs())
    return KnowledgeRetriever(store, embedder, FakeReranker(), top_k=20, top_n=5)


def build_scripted_orchestrator(data_registry, memory, *, orchestrator_script,
                                specialist_scripts, reporting_script, settings=None,
                                ticket_service=None):
    """Wire a MaintenanceOrchestrator whose every LLM is a scripted FakeLLMClient.

    The real data/ML tools execute (against the temp DB + fake retriever), so the
    whole plan -> delegate -> tools -> provenance chain runs offline with no tokens.
    """

    from backend.app.agents.orchestrator import MaintenanceOrchestrator
    from backend.app.agents.specialists import ANALYSIS_SPECS, REPORTING_SPEC, SpecialistTool
    from backend.app.core.config import get_settings
    from backend.app.tools.base import ToolRegistry

    settings = settings or get_settings()
    specialists = {
        spec.name: SpecialistTool(
            spec, data_registry,
            FakeLLMClient(specialist_scripts.get(spec.name, [text_result("no findings")])),
            max_iters=settings.specialist_max_iters,
        )
        for spec in ANALYSIS_SPECS
    }
    reporting = SpecialistTool(
        REPORTING_SPEC, data_registry, FakeLLMClient(reporting_script),
        max_iters=settings.reporting_max_iters,
    )

    orchestrator_registry = ToolRegistry()
    for tool in specialists.values():
        orchestrator_registry.register(tool)
    for name in ("get_equipment", "get_spare_parts", "get_fault_info", "search_knowledge"):
        orchestrator_registry.register(data_registry.get(name))

    return MaintenanceOrchestrator(
        orchestrator_llm=FakeLLMClient(orchestrator_script),
        orchestrator_registry=orchestrator_registry,
        reporting=reporting,
        memory=memory,
        analysis_specialist_names=set(specialists),
        roster_text="- HSM-F3-GBX: F3 main drive gearbox (Finishing)",
        data_registry=data_registry,
        ticket_service=ticket_service,
        settings=settings,
    )


class ConstantLLM(LLMClient):
    """A stateless, thread-safe LLM that always returns the same text (no tools)."""

    def __init__(self, content: str = "Constant answer.") -> None:
        super().__init__(model="constant", api_key=None, tier="test")
        self._content = content
        self.calls: list = []

    @property
    def provider(self) -> str:
        return "constant"

    def chat(self, messages, tools=None, *, temperature=None, max_tokens=None) -> ChatResult:
        self.calls.append(list(messages))
        return ChatResult(content=self._content, tool_calls=[], provenance=_provenance())


def build_constant_orchestrator(data_registry, memory, content="Constant answer.", settings=None):
    """An orchestrator whose every LLM is a ConstantLLM -> each run is one immediate
    final, no tool calls. Used to test concurrent-stream isolation deterministically."""

    from backend.app.agents.orchestrator import MaintenanceOrchestrator
    from backend.app.agents.specialists import REPORTING_SPEC, SpecialistTool
    from backend.app.core.config import get_settings
    from backend.app.tools.base import ToolRegistry

    settings = settings or get_settings()
    registry = ToolRegistry()
    for name in ("get_equipment", "get_spare_parts", "get_fault_info", "search_knowledge"):
        registry.register(data_registry.get(name))
    reporting = SpecialistTool(REPORTING_SPEC, data_registry, ConstantLLM(content))
    return MaintenanceOrchestrator(
        orchestrator_llm=ConstantLLM(content), orchestrator_registry=registry, reporting=reporting,
        memory=memory, analysis_specialist_names=set(), roster_text="(roster)",
        data_registry=data_registry, settings=settings,
    )


def build_proactive_engine(*, monitored, orchestrator, repos, models_dir,
                           ticket_service=None, alert_service=None):
    """A ProactiveEngine wired with a real stream/detector but the given (scripted)
    orchestrator -- so the proactive loop is exercised offline with zero tokens."""

    from backend.app.core.config import get_settings
    from backend.app.ml.anomaly import AnomalyDetector
    from backend.app.ml.early_warning import EarlyWarningService
    from backend.app.ml.rul import RULEstimator
    from backend.app.proactive.engine import ProactiveEngine
    from backend.app.proactive.stream import SensorStream
    from backend.app.tickets.service import AlertService, TicketService
    from backend.app.tickets.store import AlertStore, TicketStore

    stream = SensorStream(monitored)

    def clock() -> str:
        return stream.now.isoformat()

    ticket_service = ticket_service or TicketService(TicketStore(), clock=clock)
    alert_service = alert_service or AlertService(AlertStore(), clock=clock)
    detector = AnomalyDetector(str(models_dir))
    early_warning = EarlyWarningService(detector, RULEstimator(), repos)
    engine = ProactiveEngine(
        stream=stream, detector=detector, early_warning=early_warning, orchestrator=orchestrator,
        ticket_service=ticket_service, alert_service=alert_service, repos=repos,
        settings=get_settings(), monitored_assets=monitored, system_user_id="U-SYS-AMDC",
    )
    return engine, ticket_service, alert_service
