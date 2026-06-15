# ADR 0008: Frontend portal

- **Status:** Accepted
- **Date:** 2026-06-07
- **Phase:** 7 (Enterprise Frontend)

## Context

Phases 0-6 built the system and exposed it over REST + SSE. Phase 7 adds the operator
console: a fast, multi-page enterprise web portal in the spirit of an industrial CMMS /
SCADA console, with consistent branding, screen-recorded locally. It consumes the existing
API -- no SSR, no backend rewrite (only small, additive, tested backend touches).

## Decisions

1. **Vite + React + TypeScript + React Router + Tailwind, client-side routed.** Instant
   page transitions for a smooth recording; a persistent shell (brand-blue topbar +
   grouped sidebar) wraps every route via a `ProtectedRoute` layout. The app lives in
   `frontend/`, a self-contained sibling of `backend/`.

2. **One design system as the single source of truth** (`tailwind.config.ts`): brand
   blue `#3D79BB` (extracted from the official logo SVG) with derived shades, slate
   neutrals, and a semantic severity scale (critical=red, high=amber, medium=blue,
   healthy=green). Severity/status render through one `severity.ts` map of literal token
   classes plus a small UI-primitive set, so every badge, table, and chart is consistent.
   Self-hosted Inter (no CDN); restrained, flat-first, modest radius.

3. **Typed data layer.** `types.ts` mirrors every backend response exactly; `api.ts` is a
   typed fetch wrapper that attaches `X-User-Id` from the stored session and normalises
   errors to `ApiError` (reads FastAPI `{detail}`); React Query hooks add caching,
   polling, and precise invalidation. Loading uses skeletons (no layout shift); 429 and
   degraded results are surfaced cleanly and never block.

4. **The live agent trace is the differentiator.** `/api/chat` is POST-SSE, so the client
   uses `fetch-event-source` (POST + `X-User-Id`). `useChatStream` folds events into a
   trace with a LIFO stack so the orchestrator -> specialist -> tool nesting renders live
   (status, spinners, ok/fail, summaries), then the cited answer with provenance. A
   shared trace model (`trace.ts` + `TraceList`) backs both chat and the alert center.

5. **Fire-once alerts.** `useAlertWatcher` polls alerts, seeds a seen-set on the first
   load (so existing alerts never fire), and raises a banner + plays a tone exactly once
   for a new, unacknowledged alert whose `audience_roles` includes the current role.
   Audio is primed on the login/trigger gesture to satisfy autoplay policy; a mute toggle
   gives demo control.

6. **Sign-in: real Entra OAuth plus a credential-less persona quick-select.** A
   split-screen `/login` (a brand hero on the left, sign-in panel on the right).
   "Sign in with Microsoft" runs a **real** Microsoft Entra ID authorization-code flow
   (Authlib; see ADR 0009); the persona cards are a no-password quick-select for fast role
   switching. Both converge on the same `AuthContext` login -- the OAuth callback hands the
   SPA a `user_id` via `/login?uid=...`, the same plumbing as picking a persona.
   `roles.ts` adapts the offered actions (engineer/supervisor write; analyst/plant_manager
   read-broad); the backend does not hard-gate, so role gating is UI-level UX, not a
   security boundary, and the persona path performs no credential check. The one-time intro
   splash now plays as the post-login transition into the dashboard, not on app open.

7. **Reports show honest progress.** `POST /api/reports` is synchronous, so the UI shows
   an indeterminate "runs the full specialist chain, ~20-30s" state -- no fabricated
   staged animation -- then renders the body, per-specialist sections, and citations.

8. **Four additive backend touches**, each guarded and tested, none disturbing Phase 6
   code: `GET /api/users` (persona picker, single source of truth); `POST
   /api/proactive/reset` (rewind cursor + debounce to re-arm the demo); `POST
   /api/proactive/poll/stream` (stream the autonomous self-diagnosis live -- the same
   single `engine.poll` run as `/poll`, wired through the **same** `events.py` ContextVar
   sink + `asyncio.Queue` + `to_thread` bridge as `/api/chat`, with `run_streaming` and
   `stream_orchestrator` left untouched); and a guarded `StaticFiles` SPA mount.

9. **Single-origin demo, proxy for dev.** `make dev` runs the backend (:8000) and the
   Vite dev server (:5173, proxying `/api` + `/health`). For the recording, `make demo`
   builds the SPA and FastAPI serves it from one origin (the guarded mount) -- no CORS,
   no proxy. The mount is a no-op when the build is absent (dev, tests, CI), so the API
   is unchanged there.

10. **The System is built at startup, not lazily per request.** A FastAPI lifespan
    constructs `build_system()` once (off the event loop via `run_in_threadpool`) before
    the server accepts traffic and stores it on `app.state`; `get_system` returns it (with
    a double-checked-lock lazy fallback). Building lazily inside request handlers was
    unsafe in production: the SPA fires several data requests at once, each sync dependency
    ran the heavy build in its own threadpool thread, and ChromaDB's `PersistentClient` is
    not concurrency-safe to initialise -- concurrent first requests 500'd
    (`'RustBindingsAPI' object has no attribute 'bindings'`) or hung. The in-process
    TestClient (injected System) and the `/health`+static smoke never exercised that path;
    a `@slow` real-server smoke (uvicorn subprocess + concurrent first requests) now guards
    it.

## Consequences

- The whole system is operable from a branded console, and the live trace gives an
  agent-activity view that is the strongest demo beat.
- Frontend gates: `tsc --noEmit` and ESLint (`--max-warnings 0`) clean; `vite build`
  succeeds. Backend stays green: 139 offline tests including the new endpoints' tests.
- The live AI beats (chat stream, proactive self-diagnosis) are quota-gated by the the LLM provider
  free-tier daily cap (~100k tokens). Both were verified with fresh quota; under the cap
  the chat degrades to a partial answer and the proactive path still fires the
  deterministic ticket + alert (the stream delivers `status` then the outcome) -- the
  resilience the system is meant to show.
- Single-writer SQLite and bundle size (Recharts) are acceptable at demo scale; the split
  deploy (Vercel + a backend container) is a follow-on, not the target.

## Optional deploy

`Dockerfile` builds a self-contained backend image (dependencies + data + indexes +
trained models at build time); `frontend/vercel.json` configures the SPA (Vite preset +
catch-all rewrite). Local single-origin is the demo target; these make a live deploy a
quick follow-on.
