"""Composition root: wire the full system (data, tools, ML, orchestrator,
tickets/alerts, feedback, proactive engine) for the runtime, demo, and API phase.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.agents.factory import build_orchestrator
from backend.app.conversation.memory import ConversationMemory
from backend.app.core.config import Settings, get_settings
from backend.app.data_access.db import connect
from backend.app.data_access.repositories import Repositories, build_repositories
from backend.app.feedback.context import FeedbackContextProvider
from backend.app.ml.anomaly import AnomalyDetector
from backend.app.ml.early_warning import EarlyWarningService
from backend.app.ml.rul import RULEstimator
from backend.app.proactive.engine import ProactiveEngine
from backend.app.proactive.stream import SensorStream
from backend.app.tickets.service import AlertService, TicketService
from backend.app.tickets.store import AlertStore, TicketStore
from backend.app.tickets.tools import build_ticket_tools
from backend.app.tools.factory import build_default_registry


@dataclass
class System:
    orchestrator: Any
    engine: ProactiveEngine
    ticket_service: TicketService
    alert_service: AlertService
    feedback_provider: FeedbackContextProvider
    memory: ConversationMemory
    data_registry: Any
    repos: Repositories


def monitored_assets(settings: Settings) -> list[str]:
    """Assets with a trained anomaly model are the ones the engine monitors."""

    anomaly_dir = Path(settings.models_dir) / "anomaly"
    if not anomaly_dir.exists():
        return []
    return sorted(p.stem for p in anomaly_dir.glob("*.joblib"))


def build_system(settings: Settings | None = None,
                 memory: ConversationMemory | None = None) -> System:
    settings = settings or get_settings()
    memory = memory or ConversationMemory()

    repos = build_repositories(connect(settings=settings))
    data_registry = build_default_registry(settings, repos=repos)
    feedback_provider = FeedbackContextProvider(repos)

    # Autonomous events carry simulated timestamps -> services share the stream clock.
    monitored = monitored_assets(settings) or ["HSM-F2-WRB"]
    stream = SensorStream(monitored, start_days_back=settings.monitor_start_days_back)

    def clock() -> str:
        return stream.now.isoformat()

    ticket_service = TicketService(TicketStore(), clock=clock, prefix=settings.ticket_prefix)
    alert_service = AlertService(AlertStore(), clock=clock)
    ticket_tools = build_ticket_tools(ticket_service)

    orchestrator = build_orchestrator(
        settings, memory, data_registry=data_registry, feedback_provider=feedback_provider,
        ticket_service=ticket_service,
        extra_read_tools=[ticket_tools["get_ticket"], ticket_tools["list_tickets"]],
    )

    # Demo mode: wrap the orchestrator so chat, reports, and the autonomous diagnosis serve
    # REAL captured outputs instantly (the engine below gets the wrapped one too).
    if settings.demo_mode:
        from backend.app.agents.demo_cache import CachedOrchestrator, load_demo_cache

        orchestrator = CachedOrchestrator(
            inner=orchestrator, cache=load_demo_cache(settings.demo_cache_dir),
            delay_ms=settings.demo_replay_delay_ms,
        )

    detector = AnomalyDetector(settings.models_dir)
    early_warning = EarlyWarningService(detector, RULEstimator(), repos)
    engine = ProactiveEngine(
        stream=stream, detector=detector, early_warning=early_warning, orchestrator=orchestrator,
        ticket_service=ticket_service, alert_service=alert_service, repos=repos, settings=settings,
        monitored_assets=monitored, system_user_id=settings.system_user_id,
    )

    return System(orchestrator=orchestrator, engine=engine, ticket_service=ticket_service,
                  alert_service=alert_service, feedback_provider=feedback_provider, memory=memory,
                  data_registry=data_registry, repos=repos)
