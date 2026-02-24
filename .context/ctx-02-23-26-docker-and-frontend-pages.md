# Context: Docker Setup, Frontend Pages, and Logging Improvements

**Date**: 2026-02-23
**Scope**: Dockerization, meetings pages, 404 page, wide events logging

---

## 1. Dockerization

The app is now fully Docker-first. All development, testing, and debugging happens through Docker Compose.

### New Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Defines 4 services: `redis`, `backend`, `worker`, `frontend` |
| `web/backend/Dockerfile` | Python 3.12-slim, installs both `requirements.txt` files, copies `src/`, `scripts/`, `web/backend/` |
| `web/frontend/Dockerfile` | Node 22-alpine, `npm ci` + `npm run dev` |
| `Makefile` | 19 self-documenting targets (`make help` to list all) |
| `.dockerignore` | Excludes `.git`, `node_modules`, `.next`, data dirs from build context |

### Service Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  frontend   │────>│   backend   │────>│    redis     │
│  :3000      │     │   :8000     │     │    :6379     │
│  (Next.js)  │     │  (FastAPI)  │     │              │
└─────────────┘     └─────────────┘     └──────┬───────┘
                                               │
                    ┌─────────────┐            │
                    │   worker    │────────────┘
                    │  (ARQ)      │
                    └─────────────┘
```

- **redis**: Message broker + job state store. Named volume `redis-data` for persistence.
- **backend**: FastAPI API server with `--reload`. Mounts `db/`, `meetings/`, `exports/` from host.
- **worker**: Same Docker image as backend, different CMD (`python -m arq app.worker.WorkerSettings`). Processes queued pipeline jobs.
- **frontend**: Next.js dev server. Proxies `/api/*` to backend via rewrites.

### Environment Variables

| Variable | Set by Docker Compose | Default (host) | Used by |
|----------|----------------------|-----------------|---------|
| `REDIS_URL` | `redis://redis:6379` | `redis://localhost:6379` | backend, worker |
| `BACKEND_URL` | `http://backend:8000` | `http://localhost:8000` | frontend (server-side rewrites) |
| `NEXT_PUBLIC_API_URL` | `/api` | `http://localhost:8000/api` | frontend (client-side API calls) |

### Key Makefile Targets

```
make up              # Start all services
make down            # Stop all services
make logs            # Tail all logs
make logs-worker     # Tail worker logs (job execution)
make dev-backend     # Local: start FastAPI (without Docker)
make dev-worker      # Local: start ARQ worker (without Docker)
make dev-frontend    # Local: start Next.js (without Docker)
make clean           # Remove containers, volumes, images
make help            # Show all targets
```

---

## 2. Frontend: Meetings Pages and 404

### New Files

| File | Purpose |
|------|---------|
| `web/frontend/src/app/not-found.tsx` | Global 404 page with "Lost Meeting" CSS animation |
| `web/frontend/src/app/meetings/page.tsx` | Meetings list with loading/empty/data states, pagination |
| `web/frontend/src/app/meetings/[id]/page.tsx` | Meeting detail with tabs (Notes/Summary/Transcript) |
| `web/frontend/src/components/EmptyState.tsx` | Reusable empty state component (dashed border, icon, CTA) |

### API Functions Added (`web/frontend/src/lib/api.ts`)

```typescript
getMeetings(offset, limit)  // GET /api/meetings?offset=0&limit=24
getMeeting(id)              // GET /api/meetings/{id}
```

### Page States

**`/not-found` (404)**:
- CSS-only floating meeting card animation (`@keyframes float`: translateY + rotate, 3s)
- Disconnected camera icon with pulsing signal arcs (`@keyframes signal`: opacity + scale, staggered)
- CTAs: "Back to Dashboard" + "Browse Meetings"

**`/meetings` (list)**:
- **Loading**: 6 skeleton cards with `animate-pulse`
- **Empty** (total === 0): Bouncing calendar icon + "Go to Pipeline" CTA
- **Data**: Grid of `MeetingCard` components, prev/next pagination (24 per page)

**`/meetings/[id]` (detail)**:
- Uses `use(params)` for Next.js 15 async params unwrapping
- **Loading**: Skeleton placeholders
- **Not found** (API 404): Ghost meeting illustration (dashed card + "?" badge) via `EmptyState`
- **Error**: Red error box
- **Data**: Title, date, attendee badges, tab bar (Notes/Summary/Transcript), auto-selects first available tab, disabled tabs for missing content

---

## 3. Logging: Wide Events Pattern

Applied the wide events (canonical log lines) pattern to the worker job execution.

### Modified Files

**`web/backend/app/log_handler.py`**:
- `get_wide_event()` now returns richer context:
  - `warning_count`, `log_line_count`, `handler_elapsed_s` (observability)
  - `commit_hash`, `python_version`, `platform`, `pid` (environment context)
- Environment context resolved once at module load via `_get_env_context()` (cached)

**`web/backend/app/worker.py`**:
- New `_emit_canonical_log()` — emits **one structured JSON log line per job** at completion
- Canonical log line contains: `action`, `job_id`, `outcome`, `duration_seconds`, `items_processed`, `items_total`, `error_count`, `warning_count`, `log_line_count`, `commit_hash`, `params`
- Every task function (export, index, process, sync, refresh) calls `_emit_canonical_log()` in both success and error paths
- Fixed `original_argv` possibly-unbound issue in `task_sync` and `task_refresh`

**Example canonical log line** (one per job, emitted at completion):
```json
{
  "event": "job_completed",
  "action": "index",
  "job_id": "abc-123",
  "outcome": "success",
  "duration_seconds": 4.21,
  "items_processed": 573,
  "items_total": 573,
  "error_count": 0,
  "warning_count": 2,
  "log_line_count": 47,
  "commit_hash": "a399db7"
}
```

---

## 4. Other Modifications

**`web/backend/app/dependencies.py`**:
- `REDIS_URL` read from `os.environ` (defaults to `redis://localhost:6379`)
- New `_parse_redis_settings()` converts URL into ARQ `RedisSettings`
- `get_redis()` uses `Redis.from_url()` instead of hardcoded host/port
- `get_arq_pool()` uses `_parse_redis_settings()` instead of default `RedisSettings()`

**`web/frontend/next.config.ts`**:
- Rewrite destination reads `BACKEND_URL` env var (defaults to `http://localhost:8000`)

**`.gitignore`**:
- Added `exports/` (was missing, listed in CLAUDE.md as gitignored)

**`CLAUDE.md`**:
- Restructured to lead with Docker as primary development method
- Added "Running the App (Docker)" section with service table, debugging commands, env vars
- Updated Web Layer description to include worker and meeting detail page
- Added "Docker-first development" convention
