"""Structured, colorized logging used across the framework.

Provides a single ``get_logger`` factory that writes to both the console and a
rotating log file under ``reports/logs``. Log level is controlled by the
``LOG_LEVEL`` environment variable (default: INFO).
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_LOG_DIR = _ROOT / "reports" / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class _ColorFormatter(logging.Formatter):
    """Adds ANSI colors when the stream is a TTY."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[41m",
    }
    RESET = "\033[0m"

    def __init__(self, use_color: bool) -> None:
        super().__init__(_FORMAT, _DATE_FORMAT)
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        if self.use_color:
            color = self.COLORS.get(record.levelname, "")
            return f"{color}{message}{self.RESET}"
        return message


def get_logger(name: str = "framework") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(_LEVEL)
    logger.propagate = False

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(_ColorFormatter(use_color=sys.stdout.isatty()))
    logger.addHandler(console)

    file_handler = RotatingFileHandler(
        _LOG_DIR / "test_run.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_FORMAT, _DATE_FORMAT))
    logger.addHandler(file_handler)

    return logger
