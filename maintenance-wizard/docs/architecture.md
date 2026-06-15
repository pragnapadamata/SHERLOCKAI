# Maintenance Wizard: Architecture

This document describes the layered architecture, data flow, and reasoning pipeline of Maintenance Wizard.

## Scope

Maintenance Wizard is a decision-support system for predictive and prescriptive maintenance on a steel Hot Strip Mill. It covers fault diagnosis, root-cause analysis, remaining-useful-life prediction, anomaly and early-warning detection, risk and priority scoring, maintenance recommendations, structured reports, and an autonomous monitoring loop, all behind a single operations console and an agentic assistant. Outputs are explainable: every conclusion can be traced to the records, documents, model outputs, or computations behind it.

## Layered architecture

| Layer | Responsibility |
| --- | --- |
| Data substrate | A synthetic but domain-grounded steel-plant dataset: equipment master, manuals, SOPs, maintenance history, failure reports, fault catalog, spare-parts master, and sensor time-series with embedded anomalies and degradation. |
| Retrieval | A per-equipment-scoped vector store with a reranker over the documents, local embeddings, and structured data in SQLite. |
| Tool layer | The well-defined tools the agents call: knowledge search, equipment logs, sensor data, anomaly detection, RUL prediction, spare parts, maintenance history, priority scoring, logbook writes, and feedback recording. This is what makes the system agentic. |
| ML predictive | Real models for anomaly detection, RUL and degradation, and early warning, exposed as tools rather than predictions invented by the model. |
| Agentic core | A tool-calling orchestrator that plans and invokes specialist roles (diagnostic, root cause, predictive, risk and priority, recommendation, reporting). Specialists share one framework and differ only by system prompt, allowed tools, and output schema. |
| Proactive engine | A simulated sensor stream that autonomously triggers diagnosis, risk, and recommendation on anomalies and pushes alerts. |
| Feedback loop | User corrections and confirmations stored and re-injected as retrieval context (feedback-conditioned retrieval, not model retraining). |
| Conversational | Multi-turn, context-aware session memory. |
| API | A backend exposing streaming chat, dashboard data, alerts, feedback, reports, logbook, and user roles. |
| Frontend | An operations console: dashboard, equipment register, assistant, alert center, report viewer with citations, digital logbook, tickets, and plant health, with role-based views. |

### Cross-cutting concerns

1. **Explainability and traceability.** Every output carries provenance: which tool, document, or score produced it. This is anchored by a `Provenance` record on every LLM call and a per-step tool-invocation trail in the agent result.
2. **Provider-agnostic, tiered LLM layer.** Provider, model, and API key all come from configuration. A small and fast tier handles routing and simple sub-tasks; a large tier handles heavy reasoning. See ADR 0001 and the LLM client design below.

## Key decisions

- **Agent orchestration is a hand-rolled bounded tool-calling loop.** See [adr/0001-agent-orchestration.md](adr/0001-agent-orchestration.md). The orchestrator exposes a deliberately narrow interface (`run(messages, ...) -> AgentResult`), so a graph framework remains a single-file swap if graph semantics are ever needed.
- **The backend commits to a standard REST and SSE contract**, which any modern frontend framework consumes identically.
- **The RUL model uses classical statistics rather than deep learning**, so there is no heavy model dependency and the prediction is transparent and deterministic.

## LLM client design

```
Settings (env/.env)
   |
   v
LLMRegistry.get("small" | "large")          tiers.py
   |
   v
build_client(provider, model, api_key)      providers/__init__.py
   |
   v
LLMClient (ABC)  <--  provider adapter       base.py / providers/
   |
   v
ChatResult(content, tool_calls, provenance) messages.py
```

Each provider is an OpenAI-compatible adapter. To add one, implement `LLMClient` in `backend/app/llm/providers/<name>.py`, register a line in `PROVIDERS`, and set the three `LLM_*` environment variables for that tier.

## Agentic loop

```
messages ---> LLMClient.chat(tools) ---> tool_calls? --yes--> execute via ToolRegistry
   ^                                          |                        |
   |                                          no                  append tool results
   |                                          v                        |
   +------------------------------------ final answer <---------------+
                                         (+ provenance trail, bounded by max_iters)
```

## Data and knowledge substrate

The substrate is the synthetic, domain-grounded Hot Strip Mill dataset that the rest of the system reasons over. Its top quality bar is coherence across sources: a fault code in a manual matches the maintenance log, which matches an anomaly in the sensor stream, which matches a spare part with a lead time.

Coherence is enforced structurally, not by hand. Everything derives from one source of truth, `backend/scripts/data_substrate/spec.py`, in three provenance classes:

- **Programmatic** (deterministic and byte-reproducible): equipment master, spares, fault catalog, histories, delay logs, incident records, process conditions, coil log, users, and the logbook seed (CSV); sensor series (Parquet); the Round 1 profile (JSON); and the data dictionary and fault-catalog document (Markdown).
- **Drafted once, then frozen**: equipment manuals, SOPs, and failure reports. These are written from spec slices using a strict `[[TYPE:id]]` reference grammar with an allowed-token whitelist, validated, and committed. They are not byte-reproducible by design; the validator is their gate.
- **Real**: the Round 1 hot-rolling CSVs (`data/round1_hotrolling/`), read-only, profiled and narratively bound to the down-coiler but never modified.

```
spec.py (single source of truth)
   |-- generate_structured.py -> data/raw/structured/*.csv
   |-- generate_sensors.py    -> data/raw/sensors/*.parquet   (ISO 10816-3 regimes)
   |-- profile_round1.py      -> data/processed/round1_profile.json
   |-- generate_data_dictionary.py -> data/data_dictionary/*.md
   |-- generate_documents.py  -> data/raw/documents/**   (drafted, frozen) + fault catalog (programmatic)
   `-- validate_coherence.py  -> schema, foreign-key, document, sensor, story checks (exit 0/1)
make_all.py orchestrates the above; --with-docs also redrafts prose documents.
```

Three failure stories are planted so each is traceable end to end across sensors, history, manuals, fault catalog, and spares: an F3 gearbox Stage-2 pitting case (a lead-time versus RUL decision), an F2 bearing lubrication-starvation case (an autonomous alert, with the root-cause lubrication cycle deliberately omitted from history), and a down-coiler process-defect case backed by the real Round 1 data. See ADR 0002 and `data/data_dictionary/`.

## Retrieval layer and tool suite

The retrieval layer and the non-ML tool suite are the surface the agents call. Both are fully local and offline-testable, with no LLM API needed at query time.

**Retrieval (local, ONNX via fastembed, torch-free).** The documents are chunked by Markdown section with provenance metadata (`doc_id`, `doc_type`, `equipment_id`, `source`, `section`, and `[[TYPE:id]]` references), embedded with `BAAI/bge-small-en-v1.5`, and stored in one Chroma collection. Per-equipment scoping is a metadata filter (`equipment_id $in [asset, "shared"]`, with SOPs marked `"shared"`), which gives a dynamic knowledge base per asset. The query flow is retrieve then rerank: vector search (top_k), then a cross-encoder rerank (`Xenova/ms-marco-MiniLM-L-6-v2`), then top_n. The embedder and reranker sit behind protocols, so tests inject deterministic fakes.

**Structured access.** The committed CSVs load into a runtime SQLite database via a deterministic build; a `sqlite3` repository layer reads them (logbook and feedback are appendable). Sensor Parquet is read through a summarizer that returns compact per-channel statistics and the ISO regime rather than raw multi-thousand-row dumps.

**Tool suite.** `search_knowledge`, `get_equipment`, `get_sensor_data`, `get_maintenance_history`, `get_spare_parts`, `get_fault_info`, `get_equipment_logs`, `get_process_conditions`, `compute_priority`, `log_maintenance_action`, `record_feedback`, and `get_logbook`. `build_index` builds the SQLite database and the Chroma index; `build_default_registry()` wires the real dependencies into the registry, and specialists restrict tools via the registry allowlist.

**Provenance envelope.** Every tool returns a `ToolResult` with `sources` (document citations, record ids, sensor windows, and computation notes) and, for scored tools, a `components` breakdown. For example, `compute_priority` returns each of its four weighted dimensions' raw value, normalized value, weight, and contribution. This is the traceability the agents and the UI cite from. See ADR 0003.

## ML predictive layer

Real, deterministic, offline prediction models exposed as agent tools, each reporting why through contributing channels, a trend basis, or top-driver features.

- **detect_anomaly**: multivariate per asset, using a robust residual z-score from a per-asset baseline as the decision and an IsolationForest for corroboration, with channel attribution. Severity is mapped from the ISO zone and reconciled with the `regime` column.
- **predict_rul**: a classical Theil-Sen degradation-trend extrapolation to the ISO 10816-3 damage threshold (4.5 mm/s, the fracture-equivalent end of life), with a planning interval, the trend basis, and an earlier time-to-action horizon.
- **assess_alpha_defect_risk**: a HistGradientBoostingClassifier on the real Round 1 data, with `class_weight="balanced"`, StratifiedKFold cross-validation, and a threshold tuned for a target recall. It reports the actual cross-validation metrics and permutation-importance drivers. The features stay unlabeled and the held-out set is unlabeled, so it is used for prediction only.
- **assess_early_warning**: a combined verdict of acute anomaly, imminent RUL, or procurement-at-risk (the RUL interval lower bound at or below the spare lead time).

Dynamic risk is folded into `compute_priority` as a transparent additive `dynamic_risk` component (`risk = max(rul_risk, anomaly_severity)`), which raises a degrading asset in the ranking. Models persist under `models/` (gitignored, rebuilt by `train_models`); RUL needs no stored artifact. The layer uses scikit-learn only, with no deep learning dependency. See ADR 0004.

## Agentic core

A planning orchestrator that genuinely plans, delegates, and reasons over multiple steps rather than answering from a single retrieval pass.

- **Orchestrator** (large tier): a bounded loop whose tools are the five analysis specialists plus four direct data tools for trivial lookups. It decides depth, so a single factual lookup is answered with one data tool and no specialists, while an analytical or status question delegates to the relevant specialists. See ADR 0005.
- **Six specialists** share one framework (a loop, a role prompt, a tool allowlist, and a key-fact extractor): diagnostic, root cause, predictive, risk and priority, recommendation, and reporting. Each returns a `SpecialistResult` whose prose is the conclusion and whose key facts and provenance are harvested from the real tool results it called.
- **Reporting** is a deterministic, tool-less synthesis step (large tier) run after gathering. It assembles the final answer only from the collected findings (strict grounding), with inline citations. Logbook writes happen deterministically and only on an explicit request.
- **Provenance** from every tool the specialists used bubbles up, is deduplicated, and is attached to the answer. This is the explainability payoff.
- **Multi-turn memory**: an in-process session store feeds recent turns back to the orchestrator for context-aware follow-ups.
- **Bounded and dependable**: iteration is capped everywhere, and `llm.chat` is retried once and then degrades to a partial result, so provider tool-call errors and rate limits never crash a query.

```
query -> orchestrator (plan/route) --calls--> specialists (each a bounded loop over its tools)
                                                   |  findings + harvested provenance
                                                   v
                                 reporting (grounded synthesis) -> cited answer + provenance
```

Token economy is managed with tiered models, depth control, iteration bounds, a compact specialist hand-back, and limited history. Development uses a zero-token offline suite (a scripted fake LLM driving real tools) plus a small set of slow tests that exercise a real chat stream end to end. See ADR 0005.

## Proactive engine, ticketing, and feedback

The autonomy showcase and the operational loop, wired by the composition root `backend/app/container.py` (`build_system`).

- **Simulated stream** (`proactive/stream.py`): a replay cursor over the committed Parquet; the live window ending at the cursor is what the engine scores. The demo trigger advances the cursor to the planted spike and polls.
- **Two-tier monitoring loop** (`proactive/engine.py`), both debounced so one episode produces one alert and ticket: an acute alarm on an anomaly crossing (a critical ticket plus full analysis) and a predictive advisory from the early-warning sweep (a medium ticket plus full analysis). Detection is local and zero-token; the orchestrator runs only on a genuine, debounced trigger.
- **Ticketing** (`tickets/`): a lightweight lifecycle (open through to closed) with a timeline, linked findings and provenance, and attached feedback. All writes are deterministic; the LLM gets read-only `get_ticket` and `list_tickets`.
- **Alerts** (`tickets/`): the records the API and UI consume for the banner and fire-once sound, with severity-derived `audience_roles`.
- **Automatic logbook**: every autonomous alert is logged as the system user, clearly distinguishing machine entries from human ones.
- **Feedback-conditioned context** (`feedback/context.py`): prior engineer feedback for an asset and its faults is retrieved, injected into each specialist, and cited in provenance. This is conditioning, not retraining.

**Persistence boundary.** The operational write-side state (tickets, alerts, and conversation memory) is held in-memory (`tickets/store.py`, `conversation/memory.py`), guarded by a per-store lock so concurrent writes are safe, but it is not persisted across a process restart: restarting the server clears tickets, alerts, and chat history. The read-side substrate is durable, with assets, sensors, maintenance history, and the fault catalog in SQLite and the document corpus indexed in Chroma. The production path is to move the operational stores onto the same SQLite layer behind the existing repository interfaces, giving durability, restart-safety, and multi-process consistency.

## API layer

The system is exposed over HTTP with FastAPI on top of `build_system`, with the agentic process made visible and the LLM token budget respected.

- **App factory** (`api/app.py`): `create_app(system=None)` builds the app, mounts CORS, a light `/health`, and the routers. A real `System` is built once at startup by a lifespan, off the event loop, before the server accepts traffic, which avoids a first-request build race. Tests inject a scripted `System` directly.
- **Surfaces** (`api/routers/`): `chat` (streaming), `dashboard` (equipment, priority, sensors, per-asset composite), `alerts` (list and acknowledge), `tickets` (list, get, status transition, timeline), `feedback`, `reports`, `logbook`, `users`, and `proactive` (state and poll). Reads call tools and services directly; the orchestrator, the only token cost, runs only on `chat`, `reports`, and a `proactive/poll` trigger.
- **Streaming the agent's work** (`api/sse.py`, `agents/events.py`): a per-request `ContextVar` event sink lets the deep tool loop emit `status`, `tool_start`, and `tool_end` events without threading a callback through every call. The blocking run executes in a worker thread, and events cross back to the event loop via a queue that the SSE generator drains. Because each request copies the context, two concurrent chat streams get independent sinks and never cross-contaminate (covered by a concurrency test).
- **Concurrency and thread-safety** (`data_access/db.py`): SQLite opens with `check_same_thread=False`, WAL, and a busy timeout, and every read and write is wrapped in a process-global lock held only for the microsecond database call, never across an LLM call. A connection pool or a server database is a natural next step at larger scale.
- **Token-safe proactive integration**: there is no background poll loop firing the orchestrator. `POST /api/proactive/poll` is the only trigger, synchronous, returning the outcomes and alerts, and it accepts an `equipment_id` filter so the demo fires exactly one asset. Alert delivery is poll-based (`GET /api/alerts`); the UI fires the banner and sound once.
- **Auth and roles**: a user id resolves to a `UserContext` and a role that is available to every handler and returned by the users endpoint. Server-side gating is intentionally light; the UI adapts the offered actions.
- **Testing**: the offline suite drives all routers, the SSE stream, the proactive trigger, and a two-stream isolation check with zero tokens; one slow test streams a real chat end to end when quota allows.

## Frontend

A fast, multi-page operations console (Vite, React, TypeScript, React Router, and Tailwind CSS) in `frontend/`, consuming the API over REST and SSE. Routing is client-side for instant transitions, with no server-side rendering.

- **Shell and routing**: a persistent topbar (logo, alert bell, mentions bell, mute, user menu) and a grouped sidebar wrap every route via a protected-route layout. Pages include the dashboard, equipment register and detail, assistant, alerts, plant health, tickets and detail, reports, and logbook.
- **Design system** (`tailwind.config.ts`): a single source of truth for the brand scale, neutrals, and one semantic severity scale, rendered through a `severity.ts` map and a small set of UI primitives so every badge and table stays consistent.
- **Data layer**: a typed `api.ts` with `types.ts` mirroring every backend response, behind TanStack Query hooks with precise cache invalidation. Skeleton, error, and empty states are handled throughout, and degraded paths are surfaced cleanly rather than blocking.
- **Live agent trace** (`useChatStream` and `TraceList`): the assistant streams the chat SSE and renders the routing-to-specialist-to-tool nesting live, then shows the cited answer with its provenance. On completion, the reasoning and sources collapse into disclosures and the view anchors at the top of the answer. The same trace model backs the alert center.
- **Alert center**: a watcher polls alerts and fires a banner and tone exactly once for a new, unacknowledged, role-targeted alert. The demo trigger streams the autonomous self-diagnosis live, and a reset control re-arms the scenario.
- **Plant health**: per-area health percentages rolled up from live asset priority, color-graded on the severity scale, with an expandable detail view of the assets and alerts driving each area.
- **Tickets and mentions**: a ticket detail view with the lifecycle, analysis, and a timeline. Notes support inline personnel mentions (for example `@[A. Bose]`) that render as chips and are collected in a per-user mentions view in the header.
- **Sign-in**: a split-screen login. A Microsoft Entra ID authorization-code flow runs on the backend when configured (Authlib, with the authority taken from the tenant id); without it, a credential-less persona quick-select is used. Both paths log in through the same client auth context.
- **Visualizations**: trend charts on equipment detail (including a paired vibration and temperature view), an anomaly-score-versus-threshold gauge on alerts, and health sparklines on the dashboard, all drawn from real data with Recharts.
- **Run**: `make dev` runs the backend and the Vite dev server together; `make demo` builds the SPA and serves it single-origin from the backend. A `make demo-cached` mode fast-replays recorded agent outputs for the LLM-backed features. Optional deployment artifacts are a backend `Dockerfile` and a `frontend/vercel.json` for the SPA.

## Directory map

```
maintenance-wizard/
  backend/app/core/        configuration, logging, channel labels
  backend/app/llm/         provider-agnostic tiered LLM client and adapters
  backend/app/agents/      bounded loop, orchestrator, specialists, prompts, provenance, contracts
  backend/app/conversation/ in-process multi-turn session memory
  backend/app/retrieval/   chunking, embeddings, reranker, Chroma store, retriever
  backend/app/data_access/ SQLite loader, repositories, sensor reader
  backend/app/ml/          anomaly, RUL, defect, risk, early warning
  backend/app/tools/       tool abstraction and the maintenance tool suite
  backend/app/proactive/   autonomous monitoring engine and sensor stream
  backend/app/tickets/     ticket and alert services, stores, presentation
  backend/app/feedback/    feedback-conditioned context provider
  backend/app/api/         FastAPI routers and the server-sent-events bridge
  backend/scripts/         data substrate, model training, index build, demo capture
  backend/demo_cache/      recorded payloads for the cached demo
  backend/tests/           unit and integration tests
  data/raw/                committed synthetic source data (CSVs, sensor parquet, documents)
  docs/                    this overview and the decision records under adr/
  frontend/src/            React SPA: pages, components, hooks, lib, auth
```
