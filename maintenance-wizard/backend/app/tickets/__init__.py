"""Lightweight ticketing + alerts: track each issue end to end with traceability.

Tickets and alerts are created for genuine issues (autonomous alerts, or explicit
user request) -- never one per chat turn. All ticket writes are deterministic
(service calls), never LLM-driven. Stores are in-process behind interfaces so the
API phase can persist them.
"""
