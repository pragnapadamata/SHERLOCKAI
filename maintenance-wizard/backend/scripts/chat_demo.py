"""Drive the orchestrator end to end with a real key (needs a Groq key in .env).

    uv run python -m backend.scripts.chat_demo
    uv run python -m backend.scripts.chat_demo "What's the lead time on the F3 gear set?"

With no arguments it runs the F3 status hero-story query.
"""

from __future__ import annotations

import sys

from backend.app.agents.factory import build_orchestrator
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging

DEFAULT_QUERIES = ["What's the status of the F3 main drive gearbox?"]


def _format_source(ref: dict) -> str:
    kind = ref.get("kind")
    if kind == "document":
        return f"doc {ref.get('doc_id')} #{ref.get('section')}"
    if kind == "record":
        return f"{ref.get('table')}:{ref.get('id')}"
    if kind == "sensor":
        return f"sensor {ref.get('source')}"
    if kind == "computation":
        return f"{ref.get('model') or 'computation'} ({ref.get('method')})"
    return str(ref)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, dev=settings.app_env != "prod")
    orchestrator = build_orchestrator(settings)

    queries = sys.argv[1:] or DEFAULT_QUERIES
    for query in queries:
        result = orchestrator.run(query, session_id="demo")
        print("\n" + "=" * 80)
        print(f"Q: {query}")
        print("=" * 80)
        print(result.answer)
        print("\n--- specialists:", result.specialists_used or "(none -- answered directly)")
        print("--- plan:", [p["tool"] for p in result.plan])
        print(f"--- tokens: in={result.tokens_in} out={result.tokens_out} "
              f"iterations={result.iterations} stop={result.stop_reason}")
        print("--- provenance:")
        for ref in result.provenance:
            print(f"      - {_format_source(ref)}")


if __name__ == "__main__":
    main()
