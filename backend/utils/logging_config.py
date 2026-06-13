"""
Centralised logging configuration.

Call setup_logging() once on app startup. After that, every module can use
get_logger(__name__) to obtain a properly configured logger.
"""
from __future__ import annotations

import logging
import logging.handlers
import os
from typing import Optional


_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
_CONFIGURED = False


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
) -> None:
    """Configure root logger with console + rotating-file handlers."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    fmt = "[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%dT%H:%M:%S")

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(numeric_level)
    console.setFormatter(formatter)
    root.addHandler(console)

    # Rotating file handler
    resolved_file = log_file or os.path.join(_LOG_DIR, "app.log")
    os.makedirs(os.path.dirname(resolved_file), exist_ok=True)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        resolved_file,
        when="midnight",
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger (setup_logging must have been called first)."""
    return logging.getLogger(name)
