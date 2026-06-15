"""Tool abstraction and registry.

Tools are the agentic surface: well-defined, schema-described functions the
agents call. Later phases add knowledge search, sensor data, anomaly detection,
RUL prediction, spare parts, priority scoring, logbook write, and feedback tools
-- all built on the same ``Tool`` base and ``ToolRegistry``.
"""
