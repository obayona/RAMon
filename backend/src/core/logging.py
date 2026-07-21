"""Structured logging configuration for RAMon.

Provides a single ``configure_logging()`` entry-point that sets up both
``structlog`` and stdlib ``logging``.  Libraries (chatbot) use
``structlog.get_logger()`` but never call ``configure`` themselves — only
the host application does.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import structlog


def configure_logging(
    *,
    level: str = "INFO",
    fmt: str = "text",
    log_dir: str | None = None,
) -> None:
    """Configure structlog + stdlib logging for the application.

    Call this **once** at startup (in ``lifespan()``).

    Args:
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR).
        fmt: ``"text"`` for human-readable, ``"json"`` for structured.
        log_dir: Directory for log files.  ``None`` = stdout only.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # ── structlog processors ──────────────────────────────────────────
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if fmt == "json":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # ── stdlib logging handlers ───────────────────────────────────────
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Remove pre-existing handlers (e.g. uvicorn defaults)
    root.handlers.clear()

    if log_dir is not None:
        log_path = Path(log_dir)

        api_handler = _file_handler(
            log_path / "api.log", formatter, numeric_level
        )
        worker_handler = _file_handler(
            log_path / "worker.log", formatter, numeric_level
        )
        root.addHandler(api_handler)

        # Route worker logs to the worker file via a filter
        worker_handler.addFilter(_LoggerNameFilter("ramon.sync.worker"))
        root.addHandler(worker_handler)

        # Everything else goes to the api handler (default stream handler
        # already catches all, but we make it explicit).
    else:
        stream = logging.StreamHandler(sys.stdout)
        stream.setLevel(numeric_level)
        stream.setFormatter(formatter)
        root.addHandler(stream)

    # Quiet down noisy third-party loggers
    for name in ("httpcore", "httpx", "openai", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)


# ── helpers ───────────────────────────────────────────────────────────


def _file_handler(
    path: Path,
    formatter: logging.Formatter,
    level: int,
) -> logging.FileHandler:
    """Create a plain file handler."""
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


class _LoggerNameFilter(logging.Filter):
    """Pass only records whose logger name starts with a given prefix."""

    def __init__(self, prefix: str) -> None:
        super().__init__()
        self._prefix = prefix

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name == self._prefix or record.name.startswith(
            self._prefix + "."
        )
