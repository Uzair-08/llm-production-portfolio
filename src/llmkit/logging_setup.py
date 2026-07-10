"""Structured logging: one line of JSON per event.

Why JSON logs: in production your logs get shipped to a log store (Datadog,
CloudWatch, Loki...). Structured fields (cost, tokens, latency_ms) become
queryable — 'show me all requests over $0.05' — which print() can never do.
"""

import json
import logging
import sys
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Anything passed via logger.info("...", extra={"extra_fields": {...}})
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def log_event(logger: logging.Logger, msg: str, **fields) -> None:
    """Convenience: log_event(log, 'llm_call', model=m, cost_usd=c, latency_ms=t)."""
    logger.info(msg, extra={"extra_fields": fields})
