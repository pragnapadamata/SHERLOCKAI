# ADR 0003: Retrieval layer and tool suite

- **Status:** Accepted
- **Date:** 2026-06-06
- **Phase:** 2 (Retrieval Layer + Tool Suite)

## Context

Phase 2 builds the knowledge-retrieval pipeline and the non-ML tools the agents
will call. Two requirements carry over: every tool result must be explainable and
traceable, and tools must be uniform (Phase 0 `Tool` ABC + registry). The phase
must be fully offline-testable.

## Decisions

1. **Local embeddings + reranker via fastembed (ONNX), not sentence-transformers.**
   Torch-free, lighter install, faster cold start, M2-friendly; consistent with
   deferring PyTorch to Phase 3. Embeddings: `BAAI/bge-small-en-v1.5`. Reranker:
   `Xenova/ms-marco-MiniLM-L-6-v2` (small, ample for a ~90-chunk corpus), with
   `BAAI/bge-reranker-base` a config-only swap. The configured names are verified
   against fastembed's supported list at build time and fall back if absent.

2. **Embedder and reranker behind protocols.** Tests inject deterministic fakes
   (hashing embedder, lexical reranker), so the default suite needs no model
   download and no network. One `@pytest.mark.slow` test exercises the real
   models and is deselected by default (`-m "not slow"`).

3. **One Chroma collection with per-equipment metadata scoping.** Each chunk
   carries `equipment_id` (its asset, or `"shared"` for SOPs); scoped retrieval
   filters `equipment_id $in [asset, "shared"]`. Simpler than a collection per
   asset and Chroma-idiomatic. We pass precomputed embeddings in/out so Chroma's
   own embedding function is unused and the embedder stays swappable.

4. **Retrieve-then-rerank.** Vector search pulls `top_k` candidates; the
   cross-encoder reranks; `top_n` are returned with provenance metadata.

5. **Structured access: stdlib sqlite3 + pandas load, no ORM.** CSVs load into a
   runtime SQLite DB (deterministic rebuild); a thin repository layer reads them.
   `logbook` (seeded from `logbook_seed.csv`) and `feedback` (new) are appendable.

6. **Sensors return summaries, not raw dumps.** `get_sensor_data` returns
   per-channel stats, trend, current ISO regime, and anomaly count over a window,
   with an optional downsampled series -- never the full 16k-row series.

7. **Uniform provenance envelope.** Every tool returns a `ToolResult`
   (`data`, `sources`, optional `components`, `ok`/`error`) via a `DataTool` base.
   `SourceRef` is tagged by `kind` (document / record / sensor / computation).
   Expected failures become `ok=False`; unexpected exceptions propagate to the
   agent loop's catch.

8. **compute_priority uses strictly the four MTR dimensions** (criticality, delay
   severity, spares availability, lead time) with transparent normalization and
   configurable weights, returning the full component breakdown and flagging the
   top ~20% as the "vital few". A `risk_modifier` hook lets Phase 3 RUL/anomaly
   risk extend the score without changing the four-dimension base. Recent delay
   frequency is deliberately excluded (it double-counts delay severity).

9. **get_fault_info symptom matching is lexical and transparent** (returns the
   matched terms). Semantic symptom->fault discovery is left to `search_knowledge`
   over the fault-catalog chunks, not duplicated here.

10. **One added tool, `get_logbook`** (read counterpart to
    `log_maintenance_action`), for Phase 4 and the logbook UI.

## Consequences

- `build_index` builds `data/sqlite/` and `data/vector_store/` (both gitignored,
  rebuilt from the committed substrate). Models cache in `~/.cache` after first
  download.
- Tools slot into the Phase 0 registry; Phase 4 restricts them per specialist via
  the registry allowlist.
- Default `pytest` runs offline with fakes; `pytest -m slow` validates the real
  pipeline.
- Phase 3 adds the ML tools (`detect_anomaly`, `predict_rul`,
  `assess_alpha_defect_risk`) and can wire RUL/anomaly risk into
  `compute_priority` via the existing hook.
