"""Phase 1 data & knowledge substrate generators.

Everything the system reasons over is derived from a single source of truth,
``spec.py``. Programmatic generators (structured CSVs, sensor parquet, the Round 1
profile, and the data dictionary) are deterministic and byte-reproducible. The
prose documents are drafted once by the LLM from the same spec, validated for
cross-reference coherence, and then frozen as committed source artifacts.
"""
