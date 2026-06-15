"""Structured logging via structlog.

Console-rendered and human-friendly in dev; JSON in production. Context bound
with ``structlog.contextvars`` (request id, session id, step id, tool name,
provider, model) is merged into every line, which is how later phases attach
traceability to logs.
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(level: str = "INFO", *, dev: bool = True) -> None:
    """Configure stdlib logging and structlog. Safe to call more than once."""

    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    renderer = (
        structlog.dev.ConsoleRenderer()
        if dev
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""

    return structlog.get_logger(name)
