"""The agentic core: a bounded tool-calling loop and shared agent contracts.

Every specialist in later phases (Diagnostic, Root-Cause, Predictive, Risk &
Priority, Recommendation, Reporting) is this same loop with a different system
prompt, a different tool allowlist, and a different output schema.
"""
