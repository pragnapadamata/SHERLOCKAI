# Demo cache

Pre-captured real agent outputs, replayed instantly when `DEMO_MODE=1` so the LLM-backed
features (assistant chat, reports, autonomous diagnosis) return in about two to three seconds
instead of waiting on a live model or risking a rate-limit error.

- These JSON files are genuine system captures produced by the real agent, not hand-written
  content. They are replayed (the reasoning trace is fast-forwarded, then the cited answer is
  shown) for demo speed only.
- Live mode (`DEMO_MODE` unset, the default) ignores this cache and calls the configured
  model. Cache misses in demo mode also fall through to live.

## Capturing

Capture runs the real agent once per canonical input and records the trace and the final
result. You can point capture at any OpenAI-compatible endpoint; a provider with a generous
free tier is convenient because capture makes many calls. The capture override is
capture-only and does not affect live mode.

```
CAPTURE_LLM_API_KEY=... uv run python -m backend.scripts.capture_demo_cache   # or: make capture
git add backend/demo_cache && git commit -m "chore: capture demo cache"
```

The capture provider, model, and base URL are set with `CAPTURE_LLM_PROVIDER`,
`CAPTURE_LLM_MODEL`, and `CAPTURE_LLM_BASE_URL`. Capture is safe and resumable: degraded
results are never written and already-good items are skipped, so you can re-run to fill only
the gaps.

## What is covered

Edit the constants at the top of the capture script to add more.

- Assistant chat (`CHAT_QUERIES`): the canonical full-chain queries.
- Reports (`REPORT_ASSETS`): `HSM-F3-GBX`, `HSM-F2-WRB`, `HSM-DC-MND`.
- Autonomous diagnosis (`PROACTIVE`): the F2 acute alarm on `HSM-F2-WRB`.

Layout: `chat/*.json`, `reports/<equipment_id>.json`, `proactive/<equipment_id>.json`, each
keyed for lookup by `backend/app/agents/demo_cache.py` (chat by normalized question; reports
and proactive by asset id).
