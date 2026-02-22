"""Custom logging.Handler that pushes log records to Redis for streaming."""

import json
import logging
import re
from datetime import datetime, timezone

import redis

# Matches [50/573] (export/process scripts) or "Progress: 50/573" (build_index)
PROGRESS_RE = re.compile(r"(?:\[(\d+)/(\d+)\]|Progress:\s*(\d+)/(\d+))")
LOG_LIST_TTL = 86400


class JobLogHandler(logging.Handler):
    """Captures log records and pushes them to a Redis list for real-time streaming.

    Uses a synchronous redis client because this handler runs inside
    run_in_executor on a thread, not the async event loop.
    """

    def __init__(self, redis_url: str, job_id: str):
        super().__init__()
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.job_id = job_id
        self.log_key = f"granola:job:{job_id}:logs"
        self.items_processed = 0
        self.items_total = 0
        self.error_count = 0
        self.errors: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "message": self.format(record) if self.formatter else record.getMessage(),
                "logger": record.name,
            }
            self.redis_client.rpush(self.log_key, json.dumps(entry))
            self.redis_client.expire(self.log_key, LOG_LIST_TTL)

            self._parse_progress(entry["message"])
            if record.levelno >= logging.ERROR:
                self._track_error(entry["message"])
        except Exception:
            self.handleError(record)

    def _parse_progress(self, message: str) -> None:
        match = PROGRESS_RE.search(message)
        if match:
            # Groups 1,2 for [N/M] format; groups 3,4 for "Progress: N/M" format
            current = match.group(1) or match.group(3)
            total = match.group(2) or match.group(4)
            if current and total:
                self.items_processed = int(current)
                self.items_total = int(total)

    def _track_error(self, message: str) -> None:
        self.error_count += 1
        if len(self.errors) < 50:
            self.errors.append(message)

    def get_wide_event(self) -> dict:
        return {
            "items_processed": self.items_processed,
            "items_total": self.items_total,
            "error_count": self.error_count,
            "errors": self.errors,
        }

    def close(self) -> None:
        try:
            self.redis_client.close()
        except Exception:
            pass
        super().close()
