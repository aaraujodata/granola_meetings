# Date-Filtered Refresh + ARQ Job Reconciliation

## Problem

Two distinct problems solved in one session:

1. **No way to refresh recent meetings from the UI.** The CLI supports `python granola_pipeline.py export --since 2026-02-19`, but the web dashboard only had 4 buttons (Export All, Rebuild Index, Process, Full Sync) with no parameters. Exporting 586 meetings to get the 3 new ones from today is wasteful.

2. **Silent job failures when ARQ functions are missing.** After deploying the new `task_refresh` function, the first job was enqueued but the worker (started before the deploy) didn't have it registered. ARQ failed internally with `function 'task_refresh' not found`, but our custom job tracking in Redis stayed at `queued` forever — no status update, no logs, no error message. The UI showed a permanently-stuck job with "No logs available."

## Decision 1: New `refresh` Action With Parameter Passing

### What
Added a `refresh` pipeline action that runs **export (with `--since`/`--limit` flags) then rebuild index**. Extended the existing `POST /api/pipeline/{action}` endpoint to accept an optional JSON body.

### Why This Over Alternatives

| Alternative | Rejected Because |
|---|---|
| Add `--since`/`--limit` to the existing `export` action | Would change the semantics of "Export All" — existing behavior must stay untouched |
| Create a separate `/api/pipeline/refresh` endpoint | Violates the existing `/{action}` pattern; duplicates routing and job-tracking logic |
| Add query params `?since=...&limit=...` | POST body is the right place for action parameters; query params on POST is an anti-pattern |
| Run export and index as two separate jobs | User would need to manually trigger index after export; the point of refresh is "one click, updated data" |

### Parameter Flow

```
Frontend (date picker + presets)
  -> triggerPipeline("refresh", { since: "2026-02-19", limit: 10 })
    -> POST /api/pipeline/refresh  body: {"since":"2026-02-19","limit":10}
      -> Router validates since is required, stores params in Redis job_data
      -> arq.enqueue_job("task_refresh", params_dict, _job_id=job_id)
        -> task_refresh(ctx, params) builds sys.argv and calls export_main() then index_main()
```

### Backward Compatibility

- `PipelineParams` body defaults to `None` — existing actions (no body) work identically
- `params` field on `JobResponse` defaults to `None` — old jobs deserialize fine
- ARQ enqueue: only passes `params_dict` as positional arg when it's non-None

## Decision 2: Startup Reconciliation for Stale Jobs

### The Traceability Gap

When ARQ can't execute a job (function not found, deserialization error, worker crash), our custom job tracking is never updated because the task function never runs — `_update_job()` is never called. This creates a class of "ghost jobs" that are permanently stuck at `queued` or `running`.

```
Normal flow:     enqueue -> task_fn starts -> _update_job("running") -> work -> _update_job("completed")
Failure flow:    enqueue -> ARQ fails internally -> (nothing updates our tracking) -> UI shows "queued" forever
```

ARQ stores its own result in `arq:result:{job_id}` (msgpack), but our UI reads from `granola:job:{job_id}` (JSON). Two separate state stores, no synchronization.

### Why Startup Reconciliation Over Alternatives

| Alternative | Rejected Because |
|---|---|
| Periodic background reconciliation (cron/interval) | Adds complexity; startup is the natural point where function mismatches get resolved |
| Middleware on GET `/jobs/{id}` that cross-checks ARQ | Adds latency to every status poll; mixes read path with state mutation |
| ARQ `after_job_end` callback | Doesn't fire when the function isn't found — ARQ handles that internally without calling any user callbacks |
| Just document "restart the worker" | Doesn't fix the UI showing permanently-stuck jobs; violates observability principles |

### Implementation

On every worker startup (`on_startup` hook):

1. Log all registered function names (observability: confirms deploy was picked up)
2. Scan `granola:recent_jobs` list (last 50 job IDs)
3. For each job still in `queued` or `running`:
   - Check if `arq:result:{id}` exists (ARQ already processed/failed it)
   - If yes: mark our tracking as `failed`, set `completed_at`, write log entries explaining why
4. Log reconciliation summary

### The Bytes Bug

ARQ's Redis connection (`ctx["redis"]` = `ArqRedis`) does NOT use `decode_responses=True`. The FastAPI app's Redis does. So `redis.lrange()` returns `[b'abc123', ...]` in the worker, not `['abc123', ...]`.

First attempt at reconciliation silently failed because `f"granola:job:{jid}"` produced `"granola:job:b'abc123'"` — a key that doesn't exist.

**Fix**: Explicit `.decode()` on all values read from ARQ's Redis:
```python
jid = raw_jid.decode() if isinstance(raw_jid, bytes) else raw_jid
```

**Lesson**: Never assume Redis returns strings in ARQ worker context. The two Redis clients (FastAPI's `redis.asyncio.Redis(decode_responses=True)` vs ARQ's `ArqRedis`) have different defaults.

## Decision 3: Log Entries for Reconciled Jobs

### Why

A failed status without logs is nearly as bad as a stuck status. The user sees "failed" but has no idea why. The whole point of the observability layer (see `ctx-02-22-26-pipeline-observability.md`) is that every state transition is explainable.

### What

When reconciliation marks a job as failed, it also writes log entries to `granola:job:{id}:logs`:

```
[ERROR] Job failed before task execution (likely worker restarted or function not found)
[INFO]  Task 'refresh' was not registered in the worker when this job was enqueued.
        The worker has been restarted with the correct functions. Please re-trigger the job.
```

These appear in the LogViewer when the user expands the failed job — actionable, not just "failed."

## Files Modified

| File | Changes |
|---|---|
| `web/backend/app/schemas.py` | Added `refresh` to `PipelineAction`; new `PipelineParams` model; `params` field on `JobResponse` |
| `web/backend/app/routers/pipeline.py` | Accept optional `PipelineParams` body; validate refresh requires `since`; store params in Redis; pass to ARQ |
| `web/backend/app/worker.py` | New `task_refresh`; `on_startup` reconciliation with bytes handling; log entries for reconciled jobs |
| `web/frontend/src/types/index.ts` | `"refresh"` in `PipelineAction`; `PipelineParams` interface; `params` on `JobResponse` |
| `web/frontend/src/lib/api.ts` | `triggerPipeline` accepts optional params, sends JSON body |
| `web/frontend/src/components/PipelineControls.tsx` | Refresh section with date picker, limit input, preset buttons (Today/3d/7d/14d) |
| `web/frontend/src/app/pipeline/page.tsx` | Forward params through `handleTrigger`; show `(since YYYY-MM-DD)` on refresh jobs |
| `web/frontend/src/components/JobProgressBar.tsx` | `REFRESH_STEPS = ["export", "index"]`; generalized step tracker for sync + refresh |

## Redis Key Schema (Updated)

| Key | Type | TTL | Purpose |
|---|---|-----|---------|
| `granola:job:{id}` | string (JSON) | 86400s | Job metadata + wide event + **params** |
| `granola:job:{id}:logs` | list (JSON entries) | 86400s | Ordered log entries (**including reconciliation logs**) |
| `granola:recent_jobs` | list (job IDs) | none | Last 50 job IDs for listing |
| `arq:result:{id}` | string (msgpack) | varies | ARQ's internal result store (used for reconciliation cross-check) |

## Operational Runbook

### "Job stuck at queued/running"

1. Check if the ARQ worker is running: `ps aux | grep arq`
2. If not running: start it. `on_startup` will reconcile stale jobs automatically.
3. If running: the function might not be registered. Check worker logs for `Registered task functions: [...]`
4. Restart the worker: `kill <pid>` then `cd web/backend && arq app.worker.WorkerSettings`
5. Reconciliation runs on startup — stale jobs get marked as failed with explanatory logs.

### "Function not found" after deploy

This happens when code is deployed but the ARQ worker process is still running old code. ARQ imports functions once at startup. **Always restart the worker after modifying `worker.py` or any script it imports.**
