"""Centralized structlog configuration.

Usage:
    from shared.logging import configure_logging
    configure_logging(mode="dev")  # or "json" or "cli"
"""

import logging
import sys
from typing import Literal

import structlog


def configure_logging(mode: Literal["dev", "json", "cli"] = "dev") -> None:
    """Configure structlog with the specified rendering mode.

    Args:
        mode: "dev" for colored console output, "json" for structured JSON,
              "cli" for Rich-compatible plain text.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if mode == "json":
        renderer: structlog.typing.Processor = structlog.processors.JSONRenderer()
    elif mode == "cli":
        # For CLI output, use a simple string renderer
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )
