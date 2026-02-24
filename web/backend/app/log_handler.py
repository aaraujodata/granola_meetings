"""Custom logging.Handler that pushes log records to Redis for streaming.

Implements the wide events (canonical log line) pattern:
- Each job emits ONE rich structured event at completion via get_wide_event()
- Individual log lines are streamed to Redis for the UI log viewer
- Progress and errors are aggregated into the wide event, not scattered
"""

import json
import logging
import os
import platform
import re
import subprocess
import time
from datetime import datetime, timezone

import redis

# Matches [50/573] (export/process scripts) or "Progress: 50/573" (build_index)
PROGRESS_RE = re.compile(r"(?:\[(\d+)/(\d+)\]|Progress:\s*(\d+)/(\d+))")
LOG_LIST_TTL = 86400

# Resolve environment context once at module load (immutable per process)
_ENV_CONTEXT: dict | None = None


def _get_env_context() -> dict:
    """Build environment context once, cache for process lifetime."""
    global _ENV_CONTEXT
    if _ENV_CONTEXT is not None:
        return _ENV_CONTEXT

    commit_hash = "unknown"
    try:
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        pass

    _ENV_CONTEXT = {
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "commit_hash": commit_hash,
        "pid": os.getpid(),
    }
    return _ENV_CONTEXT


class JobLogHandler(logging.Handler):
    """Captures log records and pushes them to a Redis list for real-time streaming.

    Uses a synchronous redis client because this handler runs inside
    run_in_executor on a thread, not the async event loop.

    Wide event pattern: call get_wide_event() once at job completion to get
    a single context-rich structured event with progress, errors, timing,
    and environment info.
    """

    def __init__(self, redis_url: str, job_id: str):
        super().__init__()
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.job_id = job_id
        self.log_key = f"granola:job:{job_id}:logs"
        self.start_time = time.monotonic()
        self.items_processed = 0
        self.items_total = 0
        self.error_count = 0
        self.warning_count = 0
        self.log_line_count = 0
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

            self.log_line_count += 1
            self._parse_progress(entry["message"])
            if record.levelno >= logging.ERROR:
                self._track_error(entry["message"])
            elif record.levelno >= logging.WARNING:
                self.warning_count += 1
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
        """Build the canonical wide event for this job.

        Called once at job completion. Returns a single structured dict
        with all aggregated context: progress, errors, timing, and env.
        """
        elapsed = time.monotonic() - self.start_time
        return {
            # Progress
            "items_processed": self.items_processed,
            "items_total": self.items_total,
            # Error tracking
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "errors": self.errors,
            # Observability
            "log_line_count": self.log_line_count,
            "handler_elapsed_s": round(elapsed, 2),
            # Environment (immutable per process)
            **_get_env_context(),
        }

    def close(self) -> None:
        try:
            self.redis_client.close()
        except Exception:
            pass
        super().close()
