"""
Virtual Fence — Structured Logging Configuration
Provides JSON-formatted logging for production and colored console output for development.
"""

import logging
import sys
from datetime import datetime, timezone

from backend.config import get_settings


class _JSONFormatter(logging.Formatter):
    """Produces JSON log lines for machine-parseable output."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


class _ConsoleFormatter(logging.Formatter):
    """Colored console output for development."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%H:%M:%S")
        level = f"{color}{record.levelname:<8}{self.RESET}"
        name = f"\033[90m{record.name}\033[0m"
        return f"{self.BOLD}{timestamp}{self.RESET} {level} {name} — {record.getMessage()}"


def setup_logging() -> None:
    """Configure application-wide logging."""
    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Root logger
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers
    root.handlers.clear()

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if settings.DEBUG:
        handler.setFormatter(_ConsoleFormatter())
    else:
        handler.setFormatter(_ConsoleFormatter())  # Use console in both; switch to _JSONFormatter for prod

    root.addHandler(handler)

    # Silence noisy third-party loggers
    logging.getLogger("ultralytics").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance."""
    return logging.getLogger(f"virtual_fence.{name}")
