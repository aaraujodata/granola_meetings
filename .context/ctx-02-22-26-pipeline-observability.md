# Pipeline Observability: Wide Events + Log Streaming

## Problem

The pipeline dashboard (`/pipeline`) showed minimal info per job — just action name, timestamp, and a colored status badge. When triggering "Export All" or "Full Sync", users saw a blue "running" badge and nothing else until completion. No logs, no progress, no error details, no timing. Debugging failures was impossible.

## Solution: Wide Events + Log Streaming

Applied the [loggingsucks.com](https://loggingsucks.com/) wide events philosophy — one rich structured event per job that accumulates during execution, plus real-time log output streamed from Python pipeline scripts to the frontend.

### Architecture

```
Pipeline Script (export_all.py)
       │ logging.info("[42/573] Exporting: Title")
       ▼
JobLogHandler (custom logging.Handler)
       │ Serializes to JSON, pushes to Redis list
       │ Parses [N/M] and "Progress: N/M" patterns
       ▼
Redis: granola:job:{id}:logs   (list of JSON log entries)
Redis: granola:job:{id}        (wide event: timing, progress, errors, steps)
       ▼
GET /api/pipeline/jobs/{id}/logs?after=0  (cursor-based incremental fetch)
GET /api/pipeline/jobs/{id}               (enhanced with wide event fields)
       ▼
LogViewer component    (terminal-style, auto-scroll, color-coded)
JobProgressBar         (items processed, sync step tracker, timing)
```

## Files Created

| File | Purpose |
|------|---------|
| `web/backend/app/log_handler.py` | `JobLogHandler(logging.Handler)` — captures logs to Redis, parses progress, tracks errors |
| `web/frontend/src/components/LogViewer.tsx` | Terminal-style log viewer with auto-scroll and color-coded levels |
| `web/frontend/src/components/JobProgressBar.tsx` | Progress bar, sync step tracker, duration display |

## Files Modified

| File | Changes |
|------|---------|
| `web/backend/app/schemas.py` | Added `LogEntry`, `JobLogsResponse`; extended `JobResponse` with wide-event fields |
| `web/backend/app/worker.py` | Log handler install/remove around all 4 tasks; timing; step tracking for sync |
| `web/backend/app/routers/pipeline.py` | New `GET /pipeline/jobs/{id}/logs` endpoint; wide-event fields in job data |
| `web/frontend/src/types/index.ts` | `LogEntry`, `JobLogsResponse` interfaces; extended `JobResponse` |
| `web/frontend/src/lib/api.ts` | Added `getJobLogs()` |
| `web/frontend/src/hooks/useJobPoller.ts` | Added `useJobLogPoller()` with cursor-based incremental polling |
| `web/frontend/src/app/pipeline/page.tsx` | Integrated progress bar, log viewer, expandable recent jobs |

## Key Design Decisions

### Synchronous Redis in Log Handler

The `JobLogHandler` uses a **synchronous** `redis.Redis` client (not `redis.asyncio`). This is intentional — the handler runs inside `run_in_executor` on a thread, not the async event loop. Using async Redis here would require an event loop that doesn't exist in the executor thread.

### Handler Attached to Root Logger Only

Initially attached the handler to root + `scripts` + `scripts.export_all` + etc. This caused **3x duplicate log entries** because Python logging propagates up the hierarchy. A log from `scripts.build_index` would be caught by:
1. `scripts.build_index` handler
2. `scripts` handler (propagation)
3. root handler (propagation)

**Fix**: Attach only to the root logger. All child loggers propagate to root by default.

### Progress Regex Handles Two Formats

The pipeline scripts use two different progress formats:
- `export_all.py` / `process_meetings.py`: `[42/573] Exporting: Title` (bracket format)
- `build_index.py`: `Progress: 50/573 directories processed` (no brackets)

The regex handles both:
```python
PROGRESS_RE = re.compile(r"(?:\[(\d+)/(\d+)\]|Progress:\s*(\d+)/(\d+))")
```

A naive `(\d+)/(\d+)` would false-match dates like `2/22` in timestamps.

### Cursor-Based Log Polling

The frontend `useJobLogPoller` hook tracks a `cursor` (starts at 0) and fetches `getJobLogs(jobId, cursor)` every 1.5s. Each response advances the cursor by `logs.length`. This ensures:
- No duplicate log entries in the UI
- Efficient — only fetches new entries since last poll
- Final fetch on terminal status to catch any stragglers

### Wide Event Fields on JobResponse

Extended `JobResponse` with optional fields that accumulate during execution:

```
started_at, completed_at, duration_seconds
items_processed, items_total
error_count
current_step, steps_completed (for sync jobs)
```

All fields default to `None`/`0`/`[]` so existing jobs (created before this feature) still deserialize correctly.

## Bugs Encountered & Fixes

### 1. No Logs in Redis (Worker Not Restarted)

**Symptom**: LogViewer showed empty dark box. No `:logs` keys in Redis.
**Root Cause**: ARQ worker was still running old code without the log handler. The worker process must be restarted to pick up Python code changes — ARQ imports task functions once at startup.
**Evidence**: Job data had `started_at: null` despite the new code always setting it.
**Fix**: Kill and restart the ARQ worker process.
**Lesson**: Always restart the ARQ worker after modifying `worker.py` or any module it imports.

### 2. Duplicate Log Entries (3x)

**Symptom**: "Found 573 meeting directories" appeared 3 times in logs (53 entries instead of ~19).
**Root Cause**: Handler attached to root + `scripts` + `scripts.build_index` loggers. Python propagation caused triple capture.
**Fix**: Attach handler to root logger only.

### 3. Progress Not Parsed for build_index

**Symptom**: `items_processed: 0, items_total: 0` despite logs showing `Progress: 50/573`.
**Root Cause**: Regex `\[(\d+)/(\d+)\]` only matched bracket format. `build_index.py` uses `Progress: N/M`.
**Fix**: Extended regex to handle both formats with alternation.

### 4. Empty LogViewer for Completed Jobs

**Symptom**: Expanding a completed job showed empty dark box with no message.
**Root Cause**: LogViewer only showed "Waiting for logs..." when `!isTerminal`. For `isTerminal && logs.length === 0`, nothing rendered.
**Fix**: Added "No logs available for this job." message for terminal state with no logs.

### 5. Next.js `.next` Cache Corruption (500 on all routes)

**Symptom**: `Cannot find module './411.js'` error, all routes returning 500.
**Root Cause**: Webpack chunk IDs in `.next/server/` got out of sync when source files were edited while the dev server was running. The server-side webpack runtime references chunk `411.js` but the file was regenerated with different chunk IDs during hot reload.
**Fix**: Kill dev server → `rm -rf .next` → restart. This is a known Next.js dev server issue when files change significantly during a session.
**Prevention**: If you see `Cannot find module './NNN.js'` errors, always clean `.next` and restart.

## API Reference

### GET /api/pipeline/jobs/{id}/logs

Cursor-based log retrieval.

**Query params:**
- `after` (int, default 0): Start index in the Redis list
- `limit` (int, default 200, max 1000): Max entries to return

**Response:**
```json
{
  "logs": [
    {"timestamp": "2026-02-22T21:24:26.650Z", "level": "INFO", "message": "Found 573 meeting directories", "logger": "scripts.build_index"}
  ],
  "total": 19,
  "has_more": true
}
```

**Polling pattern:**
```
cursor = 0
loop:
  response = GET /logs?after={cursor}
  cursor += len(response.logs)
  if job.status in (completed, failed): break
  sleep(1.5s)
```

### Enhanced GET /api/pipeline/jobs/{id}

Now returns wide-event fields:
```json
{
  "job_id": "...",
  "status": "completed",
  "action": "index",
  "started_at": "2026-02-22T21:24:26Z",
  "completed_at": "2026-02-22T21:24:36Z",
  "duration_seconds": 9.52,
  "items_processed": 550,
  "items_total": 573,
  "error_count": 0,
  "current_step": null,
  "steps_completed": ["export", "index", "process"]
}
```

## Redis Key Schema

| Key | Type | TTL | Purpose |
|-----|------|-----|---------|
| `granola:job:{id}` | string (JSON) | 86400s | Job metadata + wide event |
| `granola:job:{id}:logs` | list (JSON entries) | 86400s | Ordered log entries |
| `granola:recent_jobs` | list (job IDs) | none | Last 50 job IDs for listing |
