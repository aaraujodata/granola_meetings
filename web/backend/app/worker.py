"""ARQ worker: async task definitions for pipeline operations.

Each task emits a canonical wide event (one structured log line per job)
at completion, following the wide events / canonical log line pattern.

Cancellation: tasks check `granola:cancel:{job_id}` (see src/cancel.py) at
safe checkpoints. A `JobCancelled` exception terminates the task and is
recorded as status="cancelled" rather than "failed".
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.dependencies import REDIS_URL, _parse_redis_settings
from app.log_handler import JobLogHandler
from src.cancel import JobCancelled, clear_cancel_async, is_cancelled_async

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

JOB_KEY_PREFIX = "granola:job:"


def _install_log_handler(job_id: str) -> JobLogHandler:
    """Create a JobLogHandler and attach it to the root logger only.

    All child loggers propagate to root by default, so attaching once
    here avoids duplicate entries.
    """
    handler = JobLogHandler(REDIS_URL, job_id)
    handler.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(handler)
    return handler


def _remove_log_handler(handler: JobLogHandler) -> None:
    """Remove handler from root logger and close it."""
    logging.getLogger().removeHandler(handler)
    handler.close()


async def _update_job(ctx, status: str, result: str | None = None, extra: dict | None = None):
    """Update the job status in Redis, merging optional wide-event fields."""
    redis = ctx["redis"]
    job_id = ctx["job_id"]
    raw = await redis.get(f"{JOB_KEY_PREFIX}{job_id}")
    if raw:
        data = json.loads(raw)
        data["status"] = status
        if result:
            data["result"] = result
        if extra:
            data.update(extra)
        await redis.set(f"{JOB_KEY_PREFIX}{job_id}", json.dumps(data), ex=86400)


def _emit_canonical_log(*, action: str, job_id: str, outcome: str, duration: float,
                        wide: dict, params: dict | None = None, error: str | None = None):
    """Emit one structured canonical log line per job — the wide event."""
    event = {
        "event": "job_completed",
        "action": action,
        "job_id": job_id,
        "outcome": outcome,
        "duration_seconds": round(duration, 2),
        "items_processed": wide.get("items_processed", 0),
        "items_total": wide.get("items_total", 0),
        "error_count": wide.get("error_count", 0),
        "warning_count": wide.get("warning_count", 0),
        "log_line_count": wide.get("log_line_count", 0),
        "commit_hash": wide.get("commit_hash", "unknown"),
        "python_version": wide.get("python_version", ""),
    }
    if params:
        event["params"] = params
    if error:
        event["error"] = error

    log.info(json.dumps(event))


def _set_job_env(job_id: str) -> dict[str, str | None]:
    """Expose GRANOLA_JOB_ID + REDIS_URL to the script process.

    Returns the previous values so the caller can restore them after the
    script finishes (worker is long-lived, so leaked env vars across jobs
    would let a stale flag from job A short-circuit job B).
    """
    prev = {
        "GRANOLA_JOB_ID": os.environ.get("GRANOLA_JOB_ID"),
        "REDIS_URL": os.environ.get("REDIS_URL"),
    }
    os.environ["GRANOLA_JOB_ID"] = job_id
    # The script's sync redis client reads REDIS_URL too; make sure it's set.
    os.environ["REDIS_URL"] = REDIS_URL
    return prev


def _restore_job_env(prev: dict[str, str | None]) -> None:
    for k, v in prev.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


async def _raise_if_cancelled(ctx) -> None:
    """Between-step cancel check for multi-step tasks (sync/refresh)."""
    if await is_cancelled_async(ctx["redis"], ctx["job_id"]):
        raise JobCancelled(f"Job {ctx['job_id']} cancelled between steps")


async def _finalize_cancelled(ctx, *, action: str, start: float, handler: JobLogHandler,
                              params: dict | None = None) -> None:
    """Common terminal-state writes for a cancelled job."""
    wide = handler.get_wide_event()
    duration = time.monotonic() - start
    await _update_job(ctx, "cancelled", "Cancelled by request", extra={
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(duration, 2),
        "current_step": None,
        **wide,
    })
    _emit_canonical_log(action=action, job_id=ctx["job_id"], outcome="cancelled",
                        duration=duration, wide=wide, params=params)
    await clear_cancel_async(ctx["redis"], ctx["job_id"])


async def _run_script_task(ctx, *, action: str, script_argv: list[str],
                           import_path: tuple[str, str], success_msg: str,
                           params: dict | None = None) -> None:
    """Generic single-script task wrapper used by export / index / process.

    `import_path` is ("scripts.export_all", "main") style. Centralizing this
    keeps the cancel + cleanup invariants in one place.
    """
    job_id = ctx["job_id"]
    start = time.monotonic()
    now = datetime.now(timezone.utc).isoformat()
    await _update_job(ctx, "running", extra={"started_at": now})

    handler = _install_log_handler(job_id)
    original_argv = sys.argv
    prev_env = _set_job_env(job_id)
    try:
        module_name, fn_name = import_path
        module = __import__(module_name, fromlist=[fn_name])
        script_main = getattr(module, fn_name)

        loop = asyncio.get_event_loop()
        sys.argv = script_argv
        await loop.run_in_executor(None, script_main)

        wide = handler.get_wide_event()
        duration = time.monotonic() - start
        await _update_job(ctx, "completed", success_msg, extra={
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration, 2),
            **wide,
        })
        _emit_canonical_log(action=action, job_id=job_id, outcome="success",
                            duration=duration, wide=wide, params=params)
    except JobCancelled:
        await _finalize_cancelled(ctx, action=action, start=start, handler=handler, params=params)
    except (Exception, SystemExit) as e:
        wide = handler.get_wide_event()
        duration = time.monotonic() - start
        error_msg = str(e) if not isinstance(e, SystemExit) else f"Script exited with code {e.code}"
        await _update_job(ctx, "failed", error_msg, extra={
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration, 2),
            **wide,
        })
        _emit_canonical_log(action=action, job_id=job_id, outcome="error",
                            duration=duration, wide=wide, params=params, error=error_msg)
        if isinstance(e, SystemExit):
            raise RuntimeError(error_msg) from e
        raise
    finally:
        sys.argv = original_argv
        _restore_job_env(prev_env)
        _remove_log_handler(handler)


async def task_export(ctx):
    """Run scripts/export_all.main() in a thread executor."""
    await _run_script_task(
        ctx, action="export",
        script_argv=["export_all"],
        import_path=("scripts.export_all", "main"),
        success_msg="Export finished successfully",
    )


async def task_index(ctx):
    """Run scripts/build_index.main() in a thread executor."""
    await _run_script_task(
        ctx, action="index",
        script_argv=["build_index"],
        import_path=("scripts.build_index", "main"),
        success_msg="Index rebuild finished successfully",
    )


async def task_process(ctx):
    """Run scripts/process_meetings.main() in a thread executor."""
    await _run_script_task(
        ctx, action="process",
        script_argv=["process_meetings"],
        import_path=("scripts.process_meetings", "main"),
        success_msg="Processing finished successfully",
    )


async def task_sync(ctx):
    """Run export -> index -> process sequentially with step tracking."""
    job_id = ctx["job_id"]
    start = time.monotonic()
    now = datetime.now(timezone.utc).isoformat()
    await _update_job(ctx, "running", extra={
        "started_at": now,
        "current_step": "export",
        "steps_completed": [],
    })

    handler = _install_log_handler(job_id)
    original_argv = sys.argv
    prev_env = _set_job_env(job_id)
    try:
        loop = asyncio.get_event_loop()

        # Step 1: Export
        await _raise_if_cancelled(ctx)
        await _update_job(ctx, "running", extra={"current_step": "export"})
        from scripts.export_all import main as export_main
        sys.argv = ["export_all"]
        await loop.run_in_executor(None, export_main)
        await _update_job(ctx, "running", extra={
            "current_step": "index",
            "steps_completed": ["export"],
        })

        # Step 2: Index
        await _raise_if_cancelled(ctx)
        from scripts.build_index import main as index_main
        sys.argv = ["build_index"]
        await loop.run_in_executor(None, index_main)
        await _update_job(ctx, "running", extra={
            "current_step": "process",
            "steps_completed": ["export", "index"],
        })

        # Step 3: Process
        await _raise_if_cancelled(ctx)
        from scripts.process_meetings import main as process_main
        sys.argv = ["process_meetings"]
        await loop.run_in_executor(None, process_main)

        wide = handler.get_wide_event()
        duration = time.monotonic() - start
        await _update_job(ctx, "completed", "Full sync finished successfully", extra={
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration, 2),
            "current_step": None,
            "steps_completed": ["export", "index", "process"],
            **wide,
        })
        _emit_canonical_log(action="sync", job_id=job_id, outcome="success", duration=duration, wide=wide)
    except JobCancelled:
        await _finalize_cancelled(ctx, action="sync", start=start, handler=handler)
    except (Exception, SystemExit) as e:
        wide = handler.get_wide_event()
        duration = time.monotonic() - start
        error_msg = str(e) if not isinstance(e, SystemExit) else f"Script exited with code {e.code}"
        await _update_job(ctx, "failed", error_msg, extra={
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration, 2),
            **wide,
        })
        _emit_canonical_log(action="sync", job_id=job_id, outcome="error", duration=duration, wide=wide, error=error_msg)
        if isinstance(e, SystemExit):
            raise RuntimeError(error_msg) from e
        raise
    finally:
        sys.argv = original_argv
        _restore_job_env(prev_env)
        _remove_log_handler(handler)


async def task_refresh(ctx, params: dict | None = None):
    """Run export (with --since/--limit) -> index sequentially with step tracking."""
    job_id = ctx["job_id"]
    start = time.monotonic()
    now = datetime.now(timezone.utc).isoformat()
    await _update_job(ctx, "running", extra={
        "started_at": now,
        "current_step": "export",
        "steps_completed": [],
    })

    handler = _install_log_handler(job_id)
    original_argv = sys.argv
    prev_env = _set_job_env(job_id)
    try:
        loop = asyncio.get_event_loop()

        # Step 1: Export with --since (and optional --limit)
        await _raise_if_cancelled(ctx)
        await _update_job(ctx, "running", extra={"current_step": "export"})
        from scripts.export_all import main as export_main
        argv = ["export_all"]
        if params and params.get("since"):
            argv += ["--since", params["since"]]
        if params and params.get("limit"):
            argv += ["--limit", str(params["limit"])]
        sys.argv = argv
        await loop.run_in_executor(None, export_main)
        await _update_job(ctx, "running", extra={
            "current_step": "index",
            "steps_completed": ["export"],
        })

        # Step 2: Rebuild index
        await _raise_if_cancelled(ctx)
        from scripts.build_index import main as index_main
        sys.argv = ["build_index", "--rebuild"]
        await loop.run_in_executor(None, index_main)

        wide = handler.get_wide_event()
        duration = time.monotonic() - start
        since_label = params.get("since", "") if params else ""
        await _update_job(ctx, "completed", f"Refresh finished successfully (since {since_label})", extra={
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration, 2),
            "current_step": None,
            "steps_completed": ["export", "index"],
            **wide,
        })
        _emit_canonical_log(action="refresh", job_id=job_id, outcome="success", duration=duration, wide=wide, params=params)
    except JobCancelled:
        await _finalize_cancelled(ctx, action="refresh", start=start, handler=handler, params=params)
    except (Exception, SystemExit) as e:
        wide = handler.get_wide_event()
        duration = time.monotonic() - start
        error_msg = str(e) if not isinstance(e, SystemExit) else f"Script exited with code {e.code}"
        await _update_job(ctx, "failed", error_msg, extra={
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration, 2),
            **wide,
        })
        _emit_canonical_log(action="refresh", job_id=job_id, outcome="error", duration=duration, wide=wide, params=params, error=error_msg)
        if isinstance(e, SystemExit):
            raise RuntimeError(error_msg) from e
        raise
    finally:
        sys.argv = original_argv
        _restore_job_env(prev_env)
        _remove_log_handler(handler)


async def on_startup(ctx):
    """Log registered functions on worker startup for traceability."""
    log.info("ARQ worker starting up")
    log.info("Registered task functions: %s", [f.__name__ for f in WorkerSettings.functions])

    # Reconcile stale jobs: if ARQ already failed a job but our tracking still says
    # queued/running, mark it as failed so the UI reflects the real state.
    redis = ctx["redis"]
    raw_ids = await redis.lrange("granola:recent_jobs", 0, 49)
    for raw_jid in raw_ids:
        jid = raw_jid.decode() if isinstance(raw_jid, bytes) else raw_jid
        raw = await redis.get(f"{JOB_KEY_PREFIX}{jid}")
        if not raw:
            continue
        raw_str = raw.decode() if isinstance(raw, bytes) else raw
        data = json.loads(raw_str)
        if data["status"] not in ("queued", "running"):
            continue
        arq_result = await redis.get(f"arq:result:{jid}")
        if arq_result:
            now_iso = datetime.now(timezone.utc).isoformat()
            reason = "Job failed before task execution (likely worker restarted or function not found)"
            log.warning("Reconciling stale job %s (was '%s', ARQ already has result) -> marking as failed", jid, data["status"])
            data["status"] = "failed"
            data["result"] = reason
            data["completed_at"] = now_iso
            await redis.set(f"{JOB_KEY_PREFIX}{jid}", json.dumps(data), ex=86400)
            log_key = f"{JOB_KEY_PREFIX}{jid}:logs"
            log_entries = [
                json.dumps({"timestamp": now_iso, "level": "ERROR", "message": reason, "logger": "arq.worker"}),
                json.dumps({"timestamp": now_iso, "level": "INFO", "message": f"Task '{data.get('action')}' was not registered in the worker when this job was enqueued. The worker has been restarted with the correct functions. Please re-trigger the job.", "logger": "arq.worker"}),
            ]
            for entry in log_entries:
                await redis.rpush(log_key, entry)
            await redis.expire(log_key, 86400)
    log.info("Startup reconciliation complete")


class WorkerSettings:
    redis_settings = _parse_redis_settings()
    functions = [task_export, task_index, task_process, task_sync, task_refresh]
    on_startup = on_startup
    max_jobs = 1
