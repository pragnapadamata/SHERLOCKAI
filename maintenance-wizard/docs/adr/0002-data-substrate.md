# ADR 0002: Data & knowledge substrate

- **Status:** Accepted
- **Date:** 2026-06-06
- **Phase:** 1 (Data & Knowledge Substrate)

## Context

Every later phase reasons over a synthetic Hot Strip Mill dataset. The dataset's
credibility depends on coherence across sources more than on volume: a user
following one failure story must find every source in agreement. We needed a way
to generate documents, structured records, and sensor series that cannot drift
apart, while incorporating Tata's real Round 1 hot-rolling data honestly.

## Decisions

1. **Single source of truth.** All entities (assets, spares, fault codes, SOPs,
   manuals, failure reports, sensor plans, anchor history/delay/incident events,
   table schemas) live in `spec.py`, which self-validates its internal
   cross-references at import. Editing the substrate means editing `spec.py`.

2. **Three provenance classes.** Programmatic artifacts are generated
   deterministically from the spec and are byte-reproducible. Prose documents are
   LLM-drafted once and frozen. The Round 1 CSVs are real and read-only.

3. **Reproducibility gate scoped to programmatic outputs only.** CSVs, Parquet,
   the Round 1 profile JSON, and the generated Markdown are byte-identical across
   runs. LLM documents are excluded from byte-equality (inference is not reliably
   deterministic); their gate is `validate_coherence.py`.

4. **Machine-checkable reference grammar.** Documents cross-reference entities
   with `[[TYPE:id]]` tokens. The document generator gives the model a whitelist
   of fully-wrapped allowed tokens and the required subset, and forbids any other
   token. The validator resolves every token against the spec and fails the build
   on any unresolved or missing required reference.

5. **Fault catalog rendered programmatically.** The fault catalog is tabular, so
   it is rendered from the spec rather than LLM-drafted, guaranteeing all fault
   references resolve.

6. **Sensor design.** 10-minute aggregated features (what an AMDC dashboard
   persists), 16-week window anchored at a single `SIMULATION_NOW` constant,
   per-asset Parquet. Degradation is baseline + piecewise-linear trend + diurnal +
   noise with scripted anomalies; the `regime` column is derived from ISO 10816-3
   velocity RMS zones so downstream code reads the zone instead of recomputing it.

7. **Generators live in `backend/scripts/data_substrate/`,** not under `data/`, so
   `data/` is pure output and the generators are importable, testable Python.

8. **RUL modelling left open.** No deep-learning dependency is introduced; the
   classical-ML-versus-small-NN choice for RUL and the Alpha-defect classifier is
   a Phase 3 decision.

## Consequences

- A fresh `make_all` run reproduces all programmatic artifacts byte-for-byte and
  passes `validate_coherence` (exit 0).
- Adding or changing data is localized to `spec.py`; the data dictionary and CSV
  schemas regenerate together and the validator catches drift.
- The committed substrate is complete and self-validating; the test suite runs
  the validator over it offline.
