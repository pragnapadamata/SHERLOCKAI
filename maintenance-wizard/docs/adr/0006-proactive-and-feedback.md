# ADR 0006: Proactive engine, ticketing, and feedback loop

- **Status:** Accepted
- **Date:** 2026-06-06
- **Phase:** 5 (Proactive Engine + Feedback Loop + Ticketing)

## Context

Phase 5 adds the autonomy showcase and the operational loop: a simulated sensor
stream that responds to issues without a user, tickets that track each issue, and
a feedback loop that conditions future analysis -- all under the free-tier token
constraint.

## Decisions

1. **Simulated stream = a replay cursor over the committed parquet.** A `SensorStream`
   tracks a simulated "now" and exposes the live window ending at the cursor; no data
   is copied or mutated. The deterministic demo trigger is `advance_to` the real,
   planted F2 spike (2026-06-02) + `poll()`; a synthetic `inject_anomaly` exists as a
   secondary trigger only.

2. **Two proactive tiers, both debounced.**
   - **Acute alarm:** an anomaly crossing (`severity >= 0.7` or ISO `action` regime) ->
     high/critical ticket + full orchestrator analysis. (F2 spike.)
   - **Predictive advisory:** each sweep also runs `assess_early_warning` (local,
     zero-token); when it fires (e.g. F3 procurement-at-risk) -> a medium-severity
     advisory ticket + full analysis. (F3.)
   Rising-edge debounce per tier (one episode = one alert/ticket); acute supersedes
   advisory for an asset in the same poll.

3. **Token economy:** detection (`detect_anomaly`, `assess_early_warning`) is local
   every poll; the orchestrator -- the only token cost (~20-25k per run) -- is invoked
   only on a genuine, debounced trigger. The auto-response query requests a
   comprehensive analysis so the full specialist chain engages.

4. **Ticketing is lightweight and real:** `open -> acknowledged -> in_progress ->
   resolved -> closed` with validated transitions, a timeline, linked findings +
   provenance, and attached feedback. No SLA/assignment/escalation. **All ticket
   writes are deterministic** (engine + orchestrator service calls); the LLM gets
   `get_ticket`/`list_tickets` read-only (Q4). Tickets are created for genuine issues
   (alerts) or on explicit user request -- never per chat turn.

5. **Alerts carry what the UI will render** (severity, message, ticket id, anomaly
   score, channels, analysis summary) plus `audience_roles` derived from severity
   (lightweight role-based targeting; the UI filters in Phase 7). The fire-once sound
   and banner are Phase 7.

6. **Automatic logbook via a dedicated system user.** Every autonomous alert+ticket is
   logged to the digital logbook attributed to **U-SYS-AMDC ("Maintenance Wizard
   (autonomous)")**, a system user added to the seed -- machine entries are honestly
   distinguished from human ones (Q6), not attributed to a real analyst.

7. **Feedback-conditioned context (FR6), not retraining.** Prior engineer feedback
   targeting an asset or its fault codes is retrieved (`FeedbackRepo.by_targets`) and
   injected into each specialist's context, and cited in the result provenance. This
   shapes analysis of similar future cases without touching any model.

8. **Composition root.** `backend/app/container.py` `build_system()` wires the shared
   repos/connection, data registry, ticket/alert services, feedback provider,
   orchestrator (with ticket read tools + feedback), and the proactive engine. A
   single shared `repos` connection keeps autonomous logbook writes and tool reads
   consistent (thread-safety is a Phase 6 concern).

## Consequences

- `ProactiveEngine.poll()` runs both tiers; `run_until`/`run_ticks` drive replay. The
  API (Phase 6) will run it as a background task.
- Offline tests (scripted orchestrator + real tools/stream/detector) cover both tiers,
  debounce, tickets, alerts, auto-log, and feedback conditioning with **zero tokens**;
  a single `@slow` test covers a real F2 auto-response (quota-permitting, Q9).
- Autonomous responses inherit the Phase-4 loop's retry+degrade: under a the LLM provider
  `tool_use_failed`/429 the ticket still opens and the analysis degrades gracefully
  rather than crashing.

## Spec change

A system user (U-SYS-AMDC, role `system`) was added to `spec.py` and the regenerated
`users.csv`; the data dictionary note was updated. Deterministic regeneration and the
coherence validator still pass.
