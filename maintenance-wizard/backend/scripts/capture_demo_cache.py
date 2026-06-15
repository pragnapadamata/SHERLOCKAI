"""Capture REAL hero agent outputs into the demo cache.

Runs the real agent for each canonical hero input and records the emitted trace + final
result to demo_cache_dir. Outputs are genuine system captures; the demo cache replays them
for speed (see backend/app/agents/demo_cache.py).

PROVIDER (capture-only): defaults to Google Gemini's free OpenAI-compatible endpoint, whose
daily budget dwarfs Groq's. Live mode is unchanged (Groq). Configure via env:
    GEMINI_API_KEY          required (or CAPTURE_LLM_API_KEY)
    CAPTURE_LLM_BASE_URL    default https://generativelanguage.googleapis.com/v1beta/openai/
    CAPTURE_LLM_MODEL       default gemini-2.0-flash (gemini-2.0-flash-lite gives 10 RPM)
    CAPTURE_LLM_PROVIDER    default openai (the OpenAI-compatible adapter)

PACING (survives free-tier RPM caps; 3 reports + proactive then take ~15-20 min):
    CAPTURE_MIN_CALL_INTERVAL_S  default 7  (space LLM calls under ~10 req/min)
    CAPTURE_MAX_RETRIES          default 10 (wait out 429s across multiple per-minute windows)
    CAPTURE_MAX_WAIT_S           default 60 (cap on a single honored retry delay)
Calls are paced and 429s are waited out patiently (RetryInfo honored), so a run degrades only
on a genuine error, never on rate-limit backoff.

SAFE + RESUMABLE: a degraded result (stop_reason llm_error, or empty findings AND empty
provenance, or a "could not complete / step budget" answer) is NEVER written; items that
already have a good cached entry are skipped. Re-run after a partial/degraded run to fill
only the gaps. Exit code is non-zero if anything degraded.

    GEMINI_API_KEY=... uv run python -m backend.scripts.capture_demo_cache   # or: make capture

TO ADD MORE ITEMS (cache every function shown in the video): add the chat question to
CHAT_QUERIES, the asset id to REPORT_ASSETS, or extend PROACTIVE. Any query routed through
the orchestrator is cacheable; keys are derived the same way at capture and serve time.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from backend.app.agents.demo_cache import derive_key
from backend.app.agents.events import event_sink
from backend.app.api.routers.reports import _REPORT_QUERY
from backend.app.container import build_system
from backend.app.core.config import Settings, get_settings
from backend.app.proactive.engine import COMPREHENSIVE

# --- Editable hero inputs (finalize wording before capturing; use the chat strings verbatim
#     on camera -- matching is tolerant of case/whitespace/trailing punctuation) -----------
CHAT_QUERIES = [
    "What's the status of the F3 main drive gearbox, and what should we do?",
    "What's driving the surface defects on the hot rolling line?",
    "What is the status of the F2 work-roll bearing?",
    "Diagnose the F3 main drive gearbox and recommend actions.",
    "Which assets should I prioritise this week and why?",
]
REPORT_ASSETS = ["HSM-F3-GBX", "HSM-F2-WRB", "HSM-DC-MND"]
PROACTIVE = {
    "equipment_id": "HSM-F2-WRB",
    "kind": "acute_alarm",
    "name": "F2 finishing stand work-roll bearing",
}
# -----------------------------------------------------------------------------------------

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def _capture_settings() -> Settings:
    """Default settings with the capture provider (Gemini OpenAI-compatible) and rate-limit
    pacing/patience overridden. Live mode is untouched."""

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("CAPTURE_LLM_API_KEY")
    provider = os.environ.get("CAPTURE_LLM_PROVIDER", "openai")
    model = os.environ.get("CAPTURE_LLM_MODEL", "gemini-2.0-flash")
    base_url = os.environ.get("CAPTURE_LLM_BASE_URL", _GEMINI_BASE_URL)
    interval = float(os.environ.get("CAPTURE_MIN_CALL_INTERVAL_S", "7"))
    max_retries = int(os.environ.get("CAPTURE_MAX_RETRIES", "10"))
    max_wait = float(os.environ.get("CAPTURE_MAX_WAIT_S", "60"))
    return get_settings().model_copy(update={
        "llm_large_provider": provider, "llm_large_model": model,
        "llm_large_api_key": key, "llm_large_base_url": base_url,
        "llm_small_provider": provider, "llm_small_model": model,
        "llm_small_api_key": key, "llm_small_base_url": base_url,
        "llm_min_call_interval_s": interval,
        "llm_rate_limit_max_retries": max_retries,
        "llm_rate_limit_max_wait_s": max_wait,
    })


def _is_degraded(final: dict) -> bool:
    if final.get("stop_reason") == "llm_error":
        return True
    if not final.get("findings") and not final.get("provenance"):
        return True
    answer = (final.get("answer") or "").lower()
    return "could not complete" in answer or "step budget" in answer


def _already_good(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        entry = json.loads(path.read_text())
    except Exception:  # noqa: BLE001 -- a corrupt file is treated as missing
        return False
    return bool(entry.get("final")) and not _is_degraded(entry["final"])


def _capture(orchestrator: Any, query: str, session_id: str) -> dict:
    """Run the real agent once, recording the trace events and the final result."""

    events: list[dict] = []
    token = event_sink.set(lambda e: events.append(dict(e)))
    try:
        result = orchestrator.run(query, session_id=session_id)
    finally:
        event_sink.reset(token)
    return {
        "key": derive_key(query),
        "query": query,
        "events": [e for e in events if e.get("type") != "final"],
        "final": result.to_dict(),
    }


def _write(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entry, indent=2, default=str))


def _proactive_query() -> str:
    return COMPREHENSIVE.format(
        kind=PROACTIVE["kind"], name=PROACTIVE["name"], equipment_id=PROACTIVE["equipment_id"],
        timestamp="(captured for demo)", message="Acute anomaly captured for the demo cache.",
    )


def main() -> None:
    settings = _capture_settings()
    if not settings.llm_large_api_key:
        print("No capture key. Set GEMINI_API_KEY (or CAPTURE_LLM_API_KEY). Aborting.")
        raise SystemExit(1)
    print(f"Capturing via {settings.llm_large_provider}:{settings.llm_large_model} "
          f"@ {settings.llm_large_base_url}")
    print(f"Pacing: >={settings.llm_min_call_interval_s}s between calls, up to "
          f"{settings.llm_rate_limit_max_retries} patient 429 retries "
          f"(<={settings.llm_rate_limit_max_wait_s}s each). This is slow but reliable.")

    system = build_system(settings)
    orch = system.orchestrator
    base = Path(settings.demo_cache_dir)

    items: list[tuple[Path, str, str]] = []
    for i, query in enumerate(CHAT_QUERIES, start=1):
        items.append((base / "chat" / f"{i}.json", query, f"capture-chat-{i}"))
    for asset in REPORT_ASSETS:
        items.append((base / "reports" / f"{asset}.json",
                      _REPORT_QUERY.format(equipment_id=asset), f"report-{asset}"))
    items.append((base / "proactive" / f"{PROACTIVE['equipment_id']}.json",
                  _proactive_query(), "capture-proactive"))

    captured, skipped, degraded = [], [], []
    for path, query, session_id in items:
        key = derive_key(query)
        if _already_good(path):
            print(f"skip (already cached): {key}")
            skipped.append(key)
            continue
        entry = _capture(orch, query, session_id)
        if _is_degraded(entry["final"]):
            print(f"DEGRADED, not written: {key}")
            degraded.append(key)
            continue
        _write(path, entry)
        print(f"captured: {key} -> {path}")
        captured.append(key)

    print("\n=== capture summary ===")
    print(f"captured ({len(captured)}): {captured}")
    print(f"skipped, already good ({len(skipped)}): {skipped}")
    print(f"degraded, NOT written ({len(degraded)}): {degraded}")
    if degraded:
        print("Re-run (resumable) to fill the degraded items.")
        raise SystemExit(2)
    print(f"done. commit the JSON under {base} to ship demo mode.")


if __name__ == "__main__":
    main()
