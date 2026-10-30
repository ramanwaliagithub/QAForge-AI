"""Structured (JSON-lines) logging for tests and framework code."""
import json
import logging
import sys
from datetime import datetime, timezone

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    """Format log records as one JSON object per line, including any `extra` fields."""

    def format(self, record: logging.LogRecord) -> str:
        """`ts`, `level`, `logger` and `msg`, then the record's extra fields, then `exc` when an exception is attached."""
        entry = {
            "ts": datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        entry.update({k: v for k, v in record.__dict__.items() if k not in _RESERVED})
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def get_logger(name: str = "qaforge", level: int = logging.INFO) -> logging.Logger:
    """Return a logger that writes JSON lines to stderr. Safe to call repeatedly."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(level)
    return logger
