"""ML predictive layer: anomaly detection, RUL, process-defect risk, early warning.

Deterministic and offline (no LLM, no network). Logic lives here as services;
the Phase 3 tools are thin wrappers, and the priority risk_modifier reuses these
same services. Every output reports why (contributing channels, trend basis, or
top-driver features). Artifacts persist under ``models/`` (gitignored, rebuilt by
``backend.scripts.train_models``).
"""
