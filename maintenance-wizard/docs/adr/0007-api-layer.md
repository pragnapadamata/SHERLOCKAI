# ADR 0007: API layer

- **Status:** Accepted
- **Date:** 2026-06-06
- **Phase:** 6 (API Layer)

## Context

Phases 0-5 built the full system behind `build_system`. Phase 6 exposes it over HTTP
for the Phase 7 UI: every surface the problem statement implies (chat, dashboard,
alerts, tickets, feedback, reports, logbook, users, proactive control), with the
agentic process made visible, safe under concurrency, and still inside the the LLM provider
free-tier token budget. It must be fully testable offline (zero tokens).

## Decisions

1. **App factory over a module-level app.** `create_app(system=None)` builds the app,
   mounts CORS and `/health`, and includes the routers. Production calls it with no
   argument and the real `System` is built **lazily** on the first request that needs
   it (`deps.get_system`, cached on `app.state`); tests pass a scripted `System` in
   directly. This keeps `/health` and the import path cheap and makes injection trivial.
   `main.py` collapses to `app = create_app()`.

2. **One router per surface** (`api/routers/`): `chat`, `dashboard`, `alerts`,
   `tickets`, `feedback`, `reports`, `logbook`, `users`, `proactive`. Reads go straight
   to the tools/services already built in Phase 2-5; the orchestrator -- the only token
   cost -- is reachable only through `chat`, `reports`, and the `proactive/poll`
   trigger. Write endpoints (ticket status/timeline, feedback, acknowledge) are
   deterministic service calls, never LLM-driven (consistent with ADR 0006 Q4).

3. **Stream the agent's work via a per-request `ContextVar` event sink.** The deep tool
   loop should not have a callback threaded through every signature just to report
   progress. `agents/events.py` holds a `ContextVar` sink; the loop and orchestrator
   `emit` `status`/`tool_start`/`tool_end` events into whatever sink is set for the
   current context. `orchestrator.run_streaming(query, session_id, emit_fn)` sets the
   sink for the call, tags every event with the `session_id`, and appends the cited
   `final`. This makes the routing -> specialist -> tool -> synthesis process visible in
   the UI as it happens.

4. **Bridge the blocking run to async with a queue, not a new event loop.** The
   orchestrator is synchronous (and CPU/IO-blocking on LLM calls), so the SSE endpoint
   runs it in `asyncio.to_thread`; the worker's `emit` hands each event to the event
   loop via `loop.call_soon_threadsafe(queue.put_nowait, event)`, and the async
   generator drains the `asyncio.Queue`, formats SSE frames, and yields them. A
   sentinel `None` closes the stream. Errors in the worker become a terminal `error`
   event rather than a dropped connection.

5. **Per-request isolation is structural, not by convention.** `asyncio.to_thread`
   copies the current context, so each request's worker thread sees its **own** sink;
   plus each request builds its own `emit` closure over its own queue, and
   `run_streaming` stamps every event with that request's `session_id`. Two concurrent
   `/api/chat` streams therefore cannot cross-contaminate. A test runs two streams
   under `asyncio.gather` (via `httpx.ASGITransport`) and asserts every event in each
   stream carries only its own `session_id`.

6. **SQLite thread-safety: shared connection + global lock.** One connection is shared
   across the async server and the (background-capable) engine. It opens with
   `check_same_thread=False`, WAL journal, and a `busy_timeout`; every `query`/
   `query_one`/`execute` is wrapped in a process-global `RLock`. The lock is held only
   for the microsecond DB call -- **never** across an LLM call -- so contention is
   negligible. This is the simplest correct choice at demo scale; a connection
   pool or Postgres is deferred to Phase 8. (Single concurrent writer is acceptable;
   `test_concurrent_reads_are_thread_safe` covers the read path under load.)

7. **Token-safe proactive integration: a controllable trigger, no background loop.**
   There is deliberately **no** always-on poller firing the orchestrator. `GET
   /api/proactive/state` reports the replay cursor and monitored assets; `POST
   /api/proactive/poll` is the only trigger -- synchronous, returning the outcomes +
   alerts, accepting `advance_to`/`steps` and an `equipment_id` filter so the demo
   advances to the planted F2 spike and fires exactly one asset (one orchestrator run).
   Alert delivery stays poll-based (`GET /api/alerts`); the fire-once banner/sound is
   Phase 7.

8. **Auth/roles as a stub the UI will build on.** `X-User-Id` is resolved against the
   `UserRepo` into a `UserContext` (default `U-ENG-01`); the role is available to every
   handler and surfaced by `/api/me`. Server-side gating is intentionally light -- the
   role drives what the Phase 7 UI shows, not hard 403s -- which matches a single-plant
   decision-support tool. CORS origins are configurable (`settings.cors_origins`).

9. **Reports reuse the grounded synthesis.** `POST /api/reports` runs the orchestrator
   on a report-style query for an asset and assembles a structured `Report` (body +
   per-specialist sections + provenance + specialists used + token counts) from the
   `OrchestratorResult`. No separate report generator and no facts beyond the findings.

## Consequences

- The system is fully driveable over HTTP and ready for the Phase 7 UI; the live SSE
  trace gives the UI an agent-activity view for free.
- The offline suite (134 passing, zero tokens) covers every router, the SSE stream, the
  proactive trigger + debounce, the two-stream isolation guarantee, and concurrent
  reads via a scripted `System`. One `@slow` test streams a **real** chat SSE end to end
  (quota-permitting); under the the LLM provider 100k/day cap the loop's retry+degrade still streams
  `status` + a degraded `final`, and proactive tickets still open deterministically.
- The global DB lock serialises writes. At demo scale this is invisible; the Phase 8
  resilience/scale work (pool, provider failover, spend caps) will revisit it.

## Verification

- `pytest` (offline): 134 passed, 5 deselected, zero tokens.
- `ruff check`: clean (FastAPI's `Depends`/`Query` defaults whitelisted for B008).
- `pytest -m slow`: real chat SSE through the API passes standalone; the the LLM provider-heavy
  slow tests are quota-gated (429 at the 100k/day cap) by design.
- Manual smokes: `GET /health` ok; `GET /api/dashboard/priority` ranks the F3 gearbox
  first (98.5); `POST /api/proactive/poll` fires the F2 acute alarm (critical alert +
  ticket with the autonomous analysis, then debounced); `curl -N /api/chat` streams the
  live `tool_start`/`tool_end` trace then the cited `final`.
