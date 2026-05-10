"""Cooperative job cancellation via a Redis polled flag.

We cannot preempt the synchronous pipeline scripts that run inside ARQ's
thread executor — `asyncio.CancelledError` does not propagate into a thread.
So we use the canonical cooperative-cancel pattern: a Redis key set by the
API and polled at safe checkpoints by the worker / scripts.

Key shape:    granola:cancel:{job_id}    (value "1", TTL CANCEL_TTL_SECONDS)
Lifecycle:    request_cancel  ->  worker observes  ->  raise JobCancelled
              ->  worker marks status="cancelled"  ->  clear_cancel
"""

from __future__ import annotations

import logging
import os

from .config import CANCEL_KEY_PREFIX, CANCEL_TTL_SECONDS

log = logging.getLogger(__name__)


class JobCancelled(Exception):
    """Raised at a checkpoint when a cancel flag has been observed."""


def _cancel_key(job_id: str) -> str:
    return f"{CANCEL_KEY_PREFIX}{job_id}"


def _redis_url() -> str:
    return os.environ.get("REDIS_URL", "redis://localhost:6379")


# ── Sync API (used by pipeline scripts running in the worker thread) ──────

def _sync_client():
    """Lazy import to keep redis off the import path for non-Docker CLI use."""
    import redis  # type: ignore
    return redis.Redis.from_url(_redis_url(), decode_responses=True)


def is_cancelled(job_id: str) -> bool:
    """Return True if a cancel flag exists for this job in Redis."""
    try:
        return bool(_sync_client().exists(_cancel_key(job_id)))
    except Exception as e:
        # Never let a Redis hiccup turn into a fake cancel signal.
        log.debug("Cancel check failed (treating as not-cancelled): %s", e)
        return False


def check_cancelled(job_id: str | None = None) -> None:
    """Raise `JobCancelled` if the current job has been asked to stop.

    `job_id` defaults to the `GRANOLA_JOB_ID` env var so pipeline scripts
    can call this without knowing they are running under a worker. When
    no job id is in scope (plain CLI runs), this is a no-op.
    """
    jid = job_id or os.environ.get("GRANOLA_JOB_ID")
    if not jid:
        return
    if is_cancelled(jid):
        raise JobCancelled(f"Job {jid} cancelled by request")


def clear_cancel(job_id: str) -> None:
    """Drop the cancel flag once the worker has acknowledged it."""
    try:
        _sync_client().delete(_cancel_key(job_id))
    except Exception as e:
        log.debug("Cancel clear failed (TTL will reap it): %s", e)


# ── Async API (used by the FastAPI cancel endpoint) ───────────────────────

async def request_cancel_async(redis, job_id: str) -> None:
    """Set the cancel flag from the FastAPI side, using an async redis client."""
    await redis.set(_cancel_key(job_id), "1", ex=CANCEL_TTL_SECONDS)


async def is_cancelled_async(redis, job_id: str) -> bool:
    """Async variant for the worker's between-step checks."""
    return bool(await redis.exists(_cancel_key(job_id)))


async def clear_cancel_async(redis, job_id: str) -> None:
    await redis.delete(_cancel_key(job_id))
