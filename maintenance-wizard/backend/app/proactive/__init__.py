"""Proactive engine: a simulated sensor stream + an autonomous monitoring loop.

Two tiers run each poll: an ACUTE ALARM on an anomaly crossing (debounced) and a
PREDICTIVE ADVISORY from the early-warning sweep. Detection is local (zero tokens);
the orchestrator is invoked only on a genuine, debounced trigger.
"""
