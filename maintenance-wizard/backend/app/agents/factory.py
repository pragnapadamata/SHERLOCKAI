"""Wire the data tools, tiered LLMs, specialists, and memory into an orchestrator."""

from __future__ import annotations

from backend.app.agents.orchestrator import MaintenanceOrchestrator
from backend.app.agents.specialists import build_reporting, build_specialists
from backend.app.conversation.memory import ConversationMemory
from backend.app.core.config import Settings, get_settings
from backend.app.llm.tiers import LLMRegistry
from backend.app.tools.base import ToolRegistry
from backend.app.tools.factory import build_default_registry

# Direct data tools the orchestrator may call for trivial lookups.
ORCHESTRATOR_DATA_TOOLS = ("get_equipment", "get_spare_parts", "get_fault_info", "search_knowledge")


def build_roster_text(data_registry: ToolRegistry) -> str:
    """A compact equipment roster for the orchestrator prompt (name -> id resolution)."""

    result = data_registry.get("get_equipment").run()
    rows = result.get("data") or []
    return "\n".join(f"- {r['equipment_id']}: {r['name']} ({r['area']})" for r in rows)


def _data_range_text() -> str:
    """Anchor the agent to the real (2026) data range so it stops guessing a wrong year."""

    try:
        from backend.app.core.config import RAW_SENSORS
        from backend.app.data_access import sensors

        ids = sorted(p.name.replace("_sensors.parquet", "") for p in RAW_SENSORS.glob("*_sensors.parquet"))
        if not ids:
            return "All sensor and coil data is recent 2026 data; prefer omitting date arguments."
        df = sensors.read_window(ids[0])
        start, end = str(df["timestamp_utc"].min())[:10], str(df["timestamp_utc"].max())[:10]
        return (f"All sensor and coil data is recent 2026 data spanning {start} to {end}. Prefer "
                "omitting date arguments (start/end) to analyze the latest window; if you pass "
                "them, use dates in this range. Never assume the year is earlier than 2026.")
    except Exception:  # noqa: BLE001 -- a missing dataset must not break construction
        return "All sensor and coil data is recent 2026 data; prefer omitting date arguments."


def build_orchestrator(settings: Settings | None = None,
                       memory: ConversationMemory | None = None,
                       *,
                       data_registry=None,
                       feedback_provider=None,
                       ticket_service=None,
                       extra_read_tools=None) -> MaintenanceOrchestrator:
    settings = settings or get_settings()
    memory = memory or ConversationMemory()

    data_registry = data_registry or build_default_registry(settings)
    llms = LLMRegistry(settings)
    specialists = build_specialists(
        data_registry, llms.get(settings.specialist_tier), settings.specialist_max_iters,
        feedback_provider=feedback_provider,
    )
    reporting = build_reporting(
        data_registry, llms.get(settings.reporting_tier), settings.reporting_max_iters
    )

    orchestrator_registry = ToolRegistry()
    for tool in specialists.values():
        orchestrator_registry.register(tool)
    for name in ORCHESTRATOR_DATA_TOOLS:
        orchestrator_registry.register(data_registry.get(name))
    for tool in extra_read_tools or []:
        orchestrator_registry.register(tool)

    return MaintenanceOrchestrator(
        orchestrator_llm=llms.get(settings.orchestrator_tier),
        orchestrator_registry=orchestrator_registry,
        reporting=reporting,
        memory=memory,
        analysis_specialist_names=set(specialists),
        roster_text=build_roster_text(data_registry),
        data_range_text=_data_range_text(),
        data_registry=data_registry,
        ticket_service=ticket_service,
        settings=settings,
    )
