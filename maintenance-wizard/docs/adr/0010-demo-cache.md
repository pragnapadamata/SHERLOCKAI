# ADR 0010: Demo cache (instant replay of real agent outputs)

- **Status:** Accepted
- **Date:** 2026-06-07
- **Phase:** 7 (Enterprise Frontend) -- demo prep

## Context

The LLM-backed features (assistant chat, reports, autonomous diagnosis) take ~20-30s live
and risk a the LLM provider free-tier 429 mid-recording. For a screen-recorded demo we want them to
return in ~2-3s and never fail on camera, without faking content.

## Decisions

1. **Replay REAL captured outputs, not fabrications.** `backend/scripts/capture_demo_cache.py`
   runs the **real** agent (fresh quota) for each canonical hero input and records the
   emitted trace + final result to `backend/demo_cache/{chat,reports,proactive}/*.json`.
   These are genuine system outputs; the demo only replays them faster. The framing is kept
   in code comments, the cache README, and the UI (the footer still says real Entra SSO,
   nothing claims the answers are live-generated on camera).

2. **One wrapper, all three features: `CachedOrchestrator`.** Because chat, reports, and the
   proactive engine all call `orchestrator.run` / `run_streaming`, wrapping the orchestrator
   in `build_system` (when `DEMO_MODE`) makes all three serve from cache with **no endpoint
   or engine changes**. The proactive engine still creates the ticket/alert deterministically
   and attaches the cached analysis; only the LLM step is replaced.

3. **Fast-replay the trace.** `run_streaming` (chat) and `run` under an active stream sink
   (proactive `poll/stream`) re-emit the captured `status` / `tool_start` / `tool_end`
   events with a single tunable gap (`DEMO_REPLAY_DELAY_MS`, default 250ms, ~2-3s total),
   then the cited `final`. A plain report request has no sink, so it returns instantly. So it
   still looks like live agent reasoning, just fast.

4. **Stable, tolerant keys.** `derive_key` keys reports and autonomous-alert queries by asset
   id (their templates carry a varying timestamp) and everything else by a normalized chat
   key (lowercased, whitespace-collapsed, trailing punctuation stripped), so a near-identical
   question on camera still hits.

5. **Off by default; misses go live.** `DEMO_MODE` is off (live) by default; `make demo` is
   live, `make demo-cached` serves the cache. A cache miss delegates to the real orchestrator,
   so uncached questions still work (just slow). The captured JSON is committed so demo mode
   is reproducible and shippable; `.env` stays gitignored.

## Consequences

- Hero features return in ~2-3s on camera with no 429 risk; everything else is unchanged.
- Offline tests cover key derivation, fast-replay, cache miss, and serving cached chat/report
  via the API with a scripted inner orchestrator -- zero tokens. The capture step is the only
  part needing real quota and is run out-of-band.
- The report endpoint was also hardened independently (see below): it now returns `503` when
  the live agent degrades to an empty result, the frontend has a 40s timeout, and it never
  renders a blank card -- so live `/reports` fails loudly instead of silently.
