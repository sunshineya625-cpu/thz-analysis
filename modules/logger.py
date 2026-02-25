"""
logger.py — Streamlit-compatible logging for THz Analysis Studio.

Provides a shared logger that writes to both console and an in-memory
buffer so that log entries can be displayed inside the Streamlit sidebar.
"""

import logging
import io
from datetime import datetime


class _MemoryHandler(logging.Handler):
    """Handler that appends formatted records to a list (newest last)."""

    def __init__(self, max_records=200):
        super().__init__()
        self._records: list[str] = []
        self._max = max_records

    def emit(self, record):
        msg = self.format(record)
        self._records.append(msg)
        if len(self._records) > self._max:
            self._records = self._records[-self._max:]

    @property
    def entries(self) -> list[str]:
        return list(self._records)

    def clear(self):
        self._records.clear()


# ── Module-level singleton ────────────────────────────────────────────────────

_memory_handler: _MemoryHandler | None = None


def get_logger(name: str = "thz") -> logging.Logger:
    """Return (or create) the application logger."""
    global _memory_handler

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)-7s  %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(ch)

    # In-memory handler (for Streamlit display)
    _memory_handler = _MemoryHandler(max_records=200)
    _memory_handler.setLevel(logging.DEBUG)
    _memory_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)-7s  %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_memory_handler)

    return logger


def get_log_entries() -> list[str]:
    """Return all buffered log entries (oldest first)."""
    if _memory_handler is None:
        return []
    return _memory_handler.entries


def clear_logs():
    """Clear the in-memory log buffer."""
    if _memory_handler is not None:
        _memory_handler.clear()
