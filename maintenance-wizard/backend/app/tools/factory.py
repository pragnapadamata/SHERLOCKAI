"""Compose dependencies into a populated ToolRegistry.

``assemble_registry`` wires already-built dependencies (repositories, retriever)
into the tool suite -- tests call it with a temp DB and a fake retriever.
``build_default_registry`` builds the real dependencies from settings for runtime
and Phase 4.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from backend.app.core.config import Settings, get_settings
from backend.app.data_access.db import connect
from backend.app.data_access.repositories import Repositories, build_repositories
from backend.app.ml.alpha_defect import AlphaDefectModel
from backend.app.ml.anomaly import AnomalyDetector
from backend.app.ml.early_warning import EarlyWarningService
from backend.app.ml.risk import build_risk_modifier
from backend.app.ml.rul import RULEstimator
from backend.app.retrieval.embeddings import build_embedder
from backend.app.retrieval.reranker import build_reranker
from backend.app.retrieval.retriever import KnowledgeRetriever
from backend.app.retrieval.vector_store import VectorStore
from backend.app.tools.base import ToolRegistry
from backend.app.tools.maintenance.defect import AssessAlphaDefectRiskTool
from backend.app.tools.maintenance.equipment import (
    GetEquipmentLogsTool,
    GetEquipmentTool,
    GetProcessConditionsTool,
)
from backend.app.tools.maintenance.faults import GetFaultInfoTool
from backend.app.tools.maintenance.feedback import RecordFeedbackTool
from backend.app.tools.maintenance.knowledge import SearchKnowledgeTool
from backend.app.tools.maintenance.maintenance import (
    GetLogbookTool,
    GetMaintenanceHistoryTool,
    LogMaintenanceActionTool,
)
from backend.app.tools.maintenance.predictive import (
    AssessEarlyWarningTool,
    DetectAnomalyTool,
    PredictRulTool,
)
from backend.app.tools.maintenance.priority import ComputePriorityTool, RiskModifier
from backend.app.tools.maintenance.sensors import GetSensorDataTool
from backend.app.tools.maintenance.spares import GetSparePartsTool


def _weights(settings: Settings) -> dict[str, float]:
    return {
        "criticality": settings.priority_weight_criticality,
        "delay": settings.priority_weight_delay,
        "spares": settings.priority_weight_spares,
        "leadtime": settings.priority_weight_leadtime,
    }


def build_retriever(settings: Settings | None = None) -> KnowledgeRetriever:
    settings = settings or get_settings()
    store = VectorStore.persistent(settings.vector_store_path, settings.kb_collection)
    return KnowledgeRetriever(
        store, build_embedder(settings), build_reranker(settings),
        top_k=settings.retrieval_top_k, top_n=settings.retrieval_top_n,
    )


def assemble_registry(
    repos: Repositories,
    retriever: KnowledgeRetriever,
    *,
    weights: dict[str, float] | None = None,
    clock: Callable[[], str] | None = None,
    sensors_dir: Path | None = None,
    risk_modifier: RiskModifier | None = None,
    risk_weight: float | None = None,
    anomaly: AnomalyDetector | None = None,
    rul: RULEstimator | None = None,
    alpha: AlphaDefectModel | None = None,
    early_warning: EarlyWarningService | None = None,
) -> ToolRegistry:
    registry = ToolRegistry()
    for tool in (
        SearchKnowledgeTool(retriever),
        GetEquipmentTool(repos),
        GetProcessConditionsTool(repos),
        GetEquipmentLogsTool(repos),
        GetSensorDataTool(sensors_dir),
        GetMaintenanceHistoryTool(repos),
        GetLogbookTool(repos),
        LogMaintenanceActionTool(repos, clock),
        GetSparePartsTool(repos),
        GetFaultInfoTool(repos),
        ComputePriorityTool(repos, weights, risk_modifier=risk_modifier, risk_weight=risk_weight),
        RecordFeedbackTool(repos, clock),
    ):
        registry.register(tool)

    # Phase 3 ML tools, registered when their services are provided.
    if anomaly is not None:
        registry.register(DetectAnomalyTool(anomaly))
    if rul is not None:
        registry.register(PredictRulTool(rul))
    if early_warning is not None:
        registry.register(AssessEarlyWarningTool(early_warning))
    if alpha is not None:
        registry.register(AssessAlphaDefectRiskTool(alpha))
    return registry


def build_default_registry(settings: Settings | None = None,
                           repos: Repositories | None = None) -> ToolRegistry:
    settings = settings or get_settings()
    repos = repos or build_repositories(connect(settings=settings))
    retriever = build_retriever(settings)

    anomaly = AnomalyDetector(settings.models_dir)
    rul = RULEstimator()
    alpha = AlphaDefectModel(settings.models_dir)
    early_warning = EarlyWarningService(anomaly, rul, repos)
    risk_modifier = build_risk_modifier(anomaly, rul)

    return assemble_registry(
        repos, retriever, weights=_weights(settings),
        risk_modifier=risk_modifier, risk_weight=settings.risk_weight,
        anomaly=anomaly, rul=rul, alpha=alpha, early_warning=early_warning,
    )
