"""Shared pytest fixtures and test isolation.

Keeps every test deterministic and offline: real LLM API keys from the shell are
removed, and the settings/registry caches are cleared around each test so one
test's configuration never leaks into another.
"""

from __future__ import annotations

import pytest

from backend.app.core.config import get_settings
from backend.app.llm.tiers import get_llm_registry
from backend.tests import fakes

FIXED_CLOCK = "2026-06-06T12:00:00"


@pytest.fixture
def tmp_repos(tmp_path):
    """Repositories over a fresh SQLite DB built from the committed CSVs."""

    return fakes.build_temp_repositories(tmp_path / "test.db")


@pytest.fixture(scope="session")
def fake_retriever():
    """Retriever over an ephemeral Chroma with deterministic fake models."""

    return fakes.build_fake_retriever()


@pytest.fixture
def registry(tmp_repos, fake_retriever):
    """A populated ToolRegistry with a temp DB, fake retriever, and fixed clock."""

    from backend.app.tools.factory import assemble_registry

    return assemble_registry(tmp_repos, fake_retriever, clock=lambda: FIXED_CLOCK)


@pytest.fixture
def memory():
    """A conversation memory with a fixed clock for deterministic timestamps."""

    from backend.app.conversation.memory import ConversationMemory

    return ConversationMemory(clock=lambda: FIXED_CLOCK)


@pytest.fixture
def api_system(tmp_repos, ml_registry, ml_models_dir):
    """A full System with a scripted orchestrator (zero tokens) for the API tests."""

    from backend.app.container import System
    from backend.app.conversation.memory import ConversationMemory
    from backend.app.feedback.context import FeedbackContextProvider
    from backend.app.tickets.service import AlertService, TicketService
    from backend.app.tickets.store import AlertStore, TicketStore
    from backend.tests import fakes

    clock = lambda: "2026-06-02T12:00:00"  # noqa: E731
    ticket_service = TicketService(TicketStore(), clock=clock)
    alert_service = AlertService(AlertStore(), clock=clock)
    mem = ConversationMemory(clock=lambda: FIXED_CLOCK)

    orchestrator = fakes.build_scripted_orchestrator(
        ml_registry, mem,
        orchestrator_script=[
            fakes.tool_call_result("o1", "diagnostic", {"equipment_id": "HSM-F2-WRB", "focus": "f"}),
            fakes.text_result("done"),
        ],
        specialist_scripts={"diagnostic": [
            fakes.tool_call_result("d1", "get_fault_info", {"fault_code": "F2-WRB-001"}),
            fakes.text_result("F2-WRB-001 lubrication starvation"),
        ]},
        reporting_script=[fakes.text_result(
            "Summary: fault F2-WRB-001; immediate lubrication + bearing replacement "
            "(spare BRG-F2-TRB-01, 2-week lead).")],
        ticket_service=ticket_service,
    )
    engine, _, _ = fakes.build_proactive_engine(
        monitored=["HSM-F2-WRB", "HSM-F3-GBX", "HSM-DC-MND"], orchestrator=orchestrator,
        repos=tmp_repos, models_dir=ml_models_dir,
        ticket_service=ticket_service, alert_service=alert_service,
    )
    return System(
        orchestrator=orchestrator, engine=engine, ticket_service=ticket_service,
        alert_service=alert_service, feedback_provider=FeedbackContextProvider(tmp_repos),
        memory=mem, data_registry=ml_registry, repos=tmp_repos,
    )


@pytest.fixture
def client(api_system):
    from fastapi.testclient import TestClient

    from backend.app.api.app import create_app

    return TestClient(create_app(system=api_system))


@pytest.fixture(scope="session")
def ml_models_dir(tmp_path_factory):
    """Train the Phase 3 ML artifacts once into a temp dir (offline, deterministic)."""

    from backend.app.ml.alpha_defect import train_alpha_model
    from backend.app.ml.anomaly import train_anomaly_models

    d = tmp_path_factory.mktemp("ml_models")
    train_anomaly_models(models_dir=d)
    train_alpha_model(models_dir=d)
    return str(d)


@pytest.fixture
def anomaly_detector(ml_models_dir):
    from backend.app.ml.anomaly import AnomalyDetector

    return AnomalyDetector(ml_models_dir)


@pytest.fixture
def rul_estimator():
    from backend.app.ml.rul import RULEstimator

    return RULEstimator()


@pytest.fixture
def alpha_model(ml_models_dir):
    from backend.app.ml.alpha_defect import AlphaDefectModel

    return AlphaDefectModel(ml_models_dir)


@pytest.fixture
def early_warning_service(anomaly_detector, rul_estimator, tmp_repos):
    from backend.app.ml.early_warning import EarlyWarningService

    return EarlyWarningService(anomaly_detector, rul_estimator, tmp_repos)


@pytest.fixture
def ml_registry(tmp_repos, fake_retriever, anomaly_detector, rul_estimator, alpha_model):
    """The full registry (16 tools) with ML services and the risk_modifier wired."""

    from backend.app.core.config import get_settings
    from backend.app.ml.early_warning import EarlyWarningService
    from backend.app.ml.risk import build_risk_modifier
    from backend.app.tools.factory import _weights, assemble_registry

    settings = get_settings()
    early = EarlyWarningService(anomaly_detector, rul_estimator, tmp_repos)
    risk_modifier = build_risk_modifier(anomaly_detector, rul_estimator)
    return assemble_registry(
        tmp_repos, fake_retriever, weights=_weights(settings), clock=lambda: FIXED_CLOCK,
        risk_modifier=risk_modifier, risk_weight=settings.risk_weight,
        anomaly=anomaly_detector, rul=rul_estimator, alpha=alpha_model, early_warning=early,
    )


@pytest.fixture(autouse=True)
def _isolate(monkeypatch: pytest.MonkeyPatch):
    """Remove real keys from the environment and clear cached singletons."""

    for var in (
        "LLM_SMALL_API_KEY",
        "LLM_LARGE_API_KEY",
        "LLM_SMALL_PROVIDER",
        "LLM_LARGE_PROVIDER",
    ):
        monkeypatch.delenv(var, raising=False)

    # The built SPA may exist at the default frontend/dist; keep tests deterministic by
    # pointing the guarded static mount at a path that does not exist (so it never mounts).
    monkeypatch.setenv("FRONTEND_DIST", "/nonexistent-mw-frontend-dist")

    # Force the OAuth path "unconfigured" in tests (env overrides .env) so the auth routes
    # degrade to the default engineer and never call Microsoft.
    monkeypatch.setenv("ENTRA_CLIENT_ID", "")
    monkeypatch.setenv("ENTRA_CLIENT_SECRET", "")

    get_settings.cache_clear()
    get_llm_registry.cache_clear()
    yield
    get_settings.cache_clear()
    get_llm_registry.cache_clear()
