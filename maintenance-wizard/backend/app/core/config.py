"""Application settings, sourced from environment variables and a local .env.

Nothing is hardcoded: the LLM provider, model, and API key for each tier come
from here. Every field has a safe default so the package imports and the test
suite runs with no .env and no environment variables set.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Stable, CWD-independent paths derived from this file's location.
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
RAW_STRUCTURED = DATA_DIR / "raw" / "structured"
RAW_SENSORS = DATA_DIR / "raw" / "sensors"
RAW_DOCS = DATA_DIR / "raw" / "documents"
ROUND1_DIR = DATA_DIR / "round1_hotrolling"
SQLITE_DIR = DATA_DIR / "sqlite"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
MODELS_DIR = REPO_ROOT / "models"


class Settings(BaseSettings):
    """Typed application configuration.

    Environment variables are matched case-insensitively, so ``LLM_LARGE_MODEL``
    populates :attr:`llm_large_model`. Unknown keys in the environment or .env
    are ignored rather than raising.
    """

    # env_file is an ABSOLUTE path to the repo-root .env so DEMO_MODE and the API
    # keys load no matter which directory uvicorn is launched from. (A relative
    # ".env" only resolves against the current working directory, so launching from
    # backend/ silently dropped the config and forced the broken live path.)
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---
    app_env: Literal["dev", "prod", "test"] = "dev"
    log_level: str = "INFO"

    # --- LLM small/fast tier (routing, classification, simple sub-tasks) ---
    llm_small_provider: str = "groq"
    llm_small_model: str = "llama-3.1-8b-instant"
    llm_small_api_key: str | None = None
    llm_small_base_url: str | None = None  # OpenAI-compatible endpoint override (e.g. capture)

    # --- LLM large/reasoning tier (diagnosis, root-cause, planning, reports) ---
    llm_large_provider: str = "groq"
    llm_large_model: str = "llama-3.3-70b-versatile"
    llm_large_api_key: str | None = None
    llm_large_base_url: str | None = None  # OpenAI-compatible endpoint override (e.g. capture)

    # --- LLM rate-limit handling (capture sets these to survive free-tier RPM caps) ---
    llm_min_call_interval_s: float = 0.0     # client-side pacing between LLM calls (0 = off)
    llm_rate_limit_max_retries: int = 1      # patient 429 retries (live = 1; capture ~10)
    llm_rate_limit_max_wait_s: float = 60.0  # cap on a single honored retry delay

    # --- LLM per-call request timeout (LIVE provider client) ---
    # A full multi-specialist run makes many large-context calls (70k+ input tokens), and a
    # single large-tier completion can take well over a minute. The provider SDK default
    # (Groq 60s) cut long calls off, so default to 180s. Env override: LLM_REQUEST_TIMEOUT.
    # Applies to the live network client only; it never touches the cached/replay demo path.
    llm_request_timeout: float = 180.0

    # --- Runtime data stores (rebuilt by build_index; gitignored) ---
    sqlite_path: str = str(SQLITE_DIR / "maintenance.db")
    vector_store_path: str = str(VECTOR_STORE_DIR)

    # --- Retrieval (local, ONNX via fastembed) ---
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    # Verified present in fastembed's reranker list at build time; bge-reranker-base
    # is a one-line swap. build_reranker() falls back to a supported model if this
    # name is ever unavailable.
    reranker_model: str = "Xenova/ms-marco-MiniLM-L-6-v2"
    retrieval_top_k: int = 20
    retrieval_top_n: int = 5
    kb_collection: str = "maintenance_kb"

    # --- Priority weights (compute_priority; four MTR dimensions, sum to 1.0) ---
    priority_weight_criticality: float = 0.40
    priority_weight_delay: float = 0.25
    priority_weight_spares: float = 0.15
    priority_weight_leadtime: float = 0.20

    # --- ML predictive layer (Phase 3) ---
    models_dir: str = str(MODELS_DIR)
    # Anomaly detection (z well above baseline max-of-many-samples noise ~4)
    anomaly_z_threshold: float = 6.0
    anomaly_window_days: int = 14
    # RUL (extrapolate to ISO damage threshold; report time-to-action separately)
    rul_horizon_weeks: float = 26.0     # RUL beyond this contributes no risk
    rul_critical_weeks: float = 2.0     # RUL at/under this is an imminent early-warning
    rul_interval_frac: float = 0.40     # +/- degradation-rate planning allowance on RUL
    # Dynamic risk folded into priority
    risk_weight: float = 0.30           # additive: priority += risk_weight * risk * 100 (capped 100)
    # Process-defect classifier
    alpha_target_recall: float = 0.90
    random_seed: int = 42

    # --- Agentic core (Phase 4) ---
    # Verified during Phase 4 @slow testing: the small (8b) model hallucinated plans
    # as text instead of emitting tool calls, so the orchestrator runs on the large tier.
    orchestrator_tier: Literal["small", "large"] = "large"
    specialist_tier: Literal["small", "large"] = "large"
    reporting_tier: Literal["small", "large"] = "large"
    orchestrator_max_iters: int = 8
    specialist_max_iters: int = 5
    reporting_max_iters: int = 3
    max_specialist_calls: int = 6
    history_max_turns: int = 6           # recent conversation messages passed to the orchestrator
    enable_tier_fallback: bool = False   # large->small fallback; disabled, deferred to Phase 8

    # --- Proactive engine (Phase 5) ---
    monitor_lookback_days: int = 3       # live window the engine scores at each tick
    monitor_step_days: int = 1           # cursor stride per tick
    monitor_start_days_back: int = 21    # where the replay cursor starts before the parquet end
    proactive_min_severity: float = 0.7  # acute-alarm gate (also fires on ISO action regime)
    recovery_polls: int = 2              # consecutive normal polls before debounce resets
    ticket_prefix: str = "MW"
    system_user_id: str = "U-SYS-AMDC"   # autonomous logbook/ticket attribution

    # --- API (Phase 6) ---
    cors_origins: str = "http://localhost:3000,http://localhost:5173"  # comma-separated

    # --- Frontend (Phase 7): single-origin demo serving; guarded (mounts only if built) ---
    frontend_dist: str = str(REPO_ROOT / "frontend" / "dist")

    # --- Microsoft Entra ID SSO (Phase 7): real OAuth auth-code flow ---
    entra_client_id: str = ""
    entra_client_secret: str = ""
    entra_tenant_id: str = "common"
    entra_redirect_uri: str = "http://localhost:8000/api/auth/callback"
    session_secret: str = "mw-dev-session-secret-change-in-prod"

    # --- Demo cache (Phase 7+): replay REAL captured agent outputs instantly on camera ---
    demo_mode: bool = False
    demo_cache_dir: str = str(REPO_ROOT / "backend" / "demo_cache")
    demo_replay_delay_ms: int = 250  # per-event fast-replay gap; tune pacing for rehearsal


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached Settings instance.

    Cached so configuration is read once. Tests that need a clean read call
    ``get_settings.cache_clear()`` or construct ``Settings`` directly.
    """

    return Settings()
