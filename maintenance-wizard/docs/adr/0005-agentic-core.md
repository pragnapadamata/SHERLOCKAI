# ADR 0005: Agentic core (orchestrator + specialists)

- **Status:** Accepted
- **Date:** 2026-06-06
- **Phase:** 4 (Agentic Core)

## Context

Phase 4 makes the system genuinely agentic: an orchestrator that plans, delegates,
and reasons over multiple steps, six specialist roles, multi-turn memory, and
cited answer assembly -- under a hard free-tier token constraint.

## Decisions

1. **Specialists-as-tools planning orchestrator.** The orchestrator is the Phase 0
   bounded loop; its callable tools are the five analysis specialists plus four
   direct data tools (`get_equipment`, `get_spare_parts`, `get_fault_info`,
   `search_knowledge`) for trivial lookups. Each specialist is the same loop with a
   role prompt, a tool allowlist, and a key-fact extractor.

2. **Reporting is a deterministic, tool-less post-loop assembler.** After the
   planning loop gathers findings, the orchestrator runs Reporting (large model,
   single synthesis, no tools) to write the final answer. Reason: routing is a good
   LLM job; final assembly should be deterministic, use the strong model once, and
   bound tokens. Reporting is tool-less because free-tier llama tool-calling is
   flaky and synthesis needs no tools.

3. **Strict Reporting grounding.** The synthesis prompt may use ONLY the collected
   specialist findings and their provenance; every number/id it states must appear
   in the findings. The harvested provenance list is already real; this closes the
   prose-overclaim hole.

4. **Orchestrator runs on the LARGE tier (verified, not assumed).** The plan
   defaulted the orchestrator to the small (8b) model for token economy, treated as
   provisional. Real testing showed the 8b model **hallucinated plans as prose**
   ("gathered: [...]") instead of emitting tool calls, so per the Phase 4 decision
   we flipped the orchestrator to the large tier, where it routes and resolves
   correctly. Specialists and Reporting were always large.

5. **Bounded *and* dependable loops.** Iteration caps on the orchestrator (8),
   specialists (5), and Reporting (3); `ToolLoopError` is caught and the partial
   result used. The loop also **retries a failed `llm.chat` once and then degrades
   to a partial result** rather than propagating provider errors (e.g. the LLM provider's
   intermittent `tool_use_failed` 400s, or 429 rate limits) -- the agentic core
   never crashes a user query.

6. **Provenance bubbles up, deduped.** Specialists harvest `sources` from their
   tool results into `provenance`; the orchestrator unions specialist `provenance`
   and direct-tool `sources`, dedups by a kind-specific key, and attaches the list
   to the final answer with inline id references in the prose.

7. **In-process multi-turn memory.** A session store holds user queries and
   assistant final answers (with provenance); only the last N turns flow back to the
   orchestrator. Behind an interface for the API phase.

8. **Single-key convenience (not model failover).** The tiered registry falls back
   to the other tier's key when a tier's key is blank and the provider matches, so a
   single the LLM provider key in `.env` drives both tiers. This is key sharing, distinct from
   the large->small model failover deferred to Phase 8 (disabled).

9. **Deterministic logbook write only on explicit request (Q4).** When the query
   asks to log/record, the orchestrator calls `log_maintenance_action` directly with
   the summary -- not via an LLM tool call (avoids the flaky-tool-calling failure).

## Consequences

- `build_orchestrator()` wires the data registry, tiered LLMs, specialists, and
  memory; `MaintenanceOrchestrator.run(query, session_id) -> OrchestratorResult`.
- Offline tests (FakeLLM scripted plans, real tools) cover planning, delegation,
  provenance, bounds, and memory with **zero tokens**; `@slow` tests exercise the
  real hero story.
- **Free-tier token reality:** a full hero query costs ~20-25k tokens across the
  orchestrator, several specialists, and Reporting; the a hosted free tier caps ~100k
  tokens/day, so repeated real runs exhaust the daily budget. Development relies on
  the zero-token offline suite; sustained real-run capacity is the provider/spend
  decision at Phase 8.

## Latent bug fixed

`sensors.read_window` compared microsecond-resolution parquet timestamps against an
ns `Timestamp` (pandas 3.0 rejects cross-unit / tz-aware comparison). Exposed once
the LLM passed `start`/`end`; fixed by normalizing to naive-ns and parsing bounds
tz-safely.
