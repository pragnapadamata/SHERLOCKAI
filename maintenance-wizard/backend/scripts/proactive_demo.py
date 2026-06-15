"""Demonstrate the proactive engine end to end (needs a Groq key; token-heavy).

    uv run python -m backend.scripts.proactive_demo

Fast-forwards the stream to the real planted F2 bearing spike, polls once (an acute
alarm fires + a ticket opens + the auto-logbook entry is written), polls again
(debounced, no re-fire), and shows the F3 predictive advisory from the same sweep.
"""

from __future__ import annotations

from backend.app.container import build_system
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.data_access.db import query

F2_SPIKE = "2026-06-02T12:00:00"


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, dev=settings.app_env != "prod")
    system = build_system(settings)
    engine = system.engine

    print(f"monitored: {engine.monitored_assets} | cursor start: {engine.stream.now}")
    engine.stream.advance_to(F2_SPIKE)
    print(f"advanced cursor to the F2 spike: {engine.stream.now}\n")

    print("=== first poll (autonomous) ===")
    outcomes = engine.poll()
    for o in outcomes:
        print(f"  {o.kind:20s} {o.equipment_id:12s} -> alert {o.alert_id}, "
              f"ticket {o.ticket_id} ({o.severity}); tokens in={o.tokens_in}")

    print("\n=== second poll (debounce) ===")
    print(f"  new outcomes: {len(engine.poll())} (expected 0 -- one episode = one alert)")

    acute = next((o for o in outcomes if o.kind == "acute_alarm"), None)
    if acute:
        t = system.ticket_service.get(acute.ticket_id)
        print(f"\n=== ticket {t.ticket_id} ===")
        print(f"  status={t.status} severity={t.severity} kind={t.kind} equipment={t.equipment_id}")
        print(f"  answer: {(t.answer[:320] + '...') if t.answer else '(none)'}")
        print(f"  provenance: {len(t.provenance)} sources | timeline: {len(t.timeline)} entries")

    print("\n=== auto-logbook (attributed to the system user) ===")
    rows = query(
        system.repos.conn,
        "SELECT entry_id, author_user_id, entry_type, text FROM logbook "
        "WHERE author_user_id = ? ORDER BY entry_id DESC LIMIT 3",
        (settings.system_user_id,),
    )
    for r in rows:
        print(f"  {r['entry_id']} [{r['author_user_id']}/{r['entry_type']}] {r['text'][:120]}")


if __name__ == "__main__":
    main()
