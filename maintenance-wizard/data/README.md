# Data substrate

> **Prototype - Tata Steel AI Hackathon 2026 - synthetic data, do not use operationally.**

The synthetic, domain-grounded Hot Strip Mill dataset the Maintenance Wizard
reasons over, plus Tata's real Round 1 hot-rolling data. The top quality bar is
**coherence across sources**: a fault code in a manual matches the maintenance
log, which matches an anomaly in the sensor stream, which matches a spare part
with a lead time.

## Layout

```
data/
  raw/
    documents/        equipment manuals, SOPs, failure reports, fault catalog (Markdown)
    structured/       equipment master, spares, fault catalog, histories, coil log, etc. (CSV)
    sensors/          per-hero-asset sensor time-series (Parquet)
  round1_hotrolling/  real Tata Round 1 data (read-only) + profile README
  data_dictionary/    field-level documentation + cross-reference map (generated)
  processed/          round1_profile.json (other caches are gitignored)
  sqlite/             runtime structured DB (built in Phase 2; gitignored)
  vector_store/       runtime vector index (built in Phase 2; gitignored)
```

## How it is generated

Everything derives from a single source of truth,
`backend/scripts/data_substrate/spec.py`. Rebuild with:

```bash
# Programmatic artifacts only (deterministic, byte-reproducible) + validation
uv run python -m backend.scripts.data_substrate.make_all

# Also (re)draft the LLM prose documents (manuals, SOPs, failure reports)
uv run python -m backend.scripts.data_substrate.make_all --with-docs

# Validate coherence on its own (exit 0 == coherent)
uv run python -m backend.scripts.data_substrate.validate_coherence
```

Provenance classes:

- **Programmatic** - CSVs, Parquet, the Round 1 profile, the data dictionary, and
  the fault-catalog document. Deterministic; regenerated on every run.
- **LLM-drafted, then frozen** - equipment manuals, SOPs, failure reports. Drafted
  once from spec slices with a strict `[[TYPE:id]]` reference grammar, validated,
  and committed. Regenerated only with `--with-docs` (and overwritten only with
  `--force-docs`).
- **Real** - the Round 1 CSVs, never modified.

## Coherence model

Documents cross-reference entities with machine-checkable `[[TYPE:id]]` tokens
(`ASSET`, `FAULT`, `SOP`, `PART`, `FR`, `MANUAL`). `validate_coherence.py` checks
column schemas, foreign keys, document references, sensor shapes, Round 1
integrity, and the three hero-story guarantees, and exits non-zero on any
mismatch.

## Hero failure stories

- **Story A - F3 gearbox (HSM-F3-GBX):** Stage-2 gear-tooth pitting; rising
  vibration sidebands and oil Fe (18 -> 34 ppm); replacement gear set lead time 8
  weeks. Supports the lead-time-vs-RUL "order now" decision.
- **Story B - F2 work-roll bearing (HSM-F2-WRB):** lubrication starvation to
  inner-race defect; a sharp anomaly the proactive engine detects unprompted. The
  root-cause lubrication cycle (week of 2026-04-20) is deliberately absent from
  maintenance history.
- **Story C - down-coiler (HSM-DC-MND):** Alpha surface-defect risk, backed by the
  real Round 1 data; every Coil ID maps here. The classifier is a Phase 3 tool.

See `data_dictionary/` for field-level documentation and the cross-reference map.
