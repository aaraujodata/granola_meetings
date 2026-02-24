# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a data pipeline that exports meeting data from the Granola desktop app's internal API, stores it as structured markdown, builds a full-text search index, and optionally enriches meetings with Claude API-powered intelligence extraction. It also includes a web UI (FastAPI + Next.js) for browsing and searching meetings.

## Running the App (Docker)

**The app runs entirely in Docker.** All development, testing, and debugging happens through Docker Compose. Do not run services locally — use the Makefile targets instead.

### Start / Stop
```bash
make up          # Build and start all 4 services (redis, backend, worker, frontend)
make down        # Stop everything
make restart     # Restart all services
make ps          # Check container status
```

### Debugging and Logs
```bash
make logs            # Tail all service logs (Ctrl-C to exit)
make logs-backend    # Tail only FastAPI backend logs
make logs-worker     # Tail only ARQ worker logs (job execution + canonical log lines)
make logs-frontend   # Tail only Next.js frontend logs
```

### Services (docker-compose.yml)
| Service | Port | Description |
|---------|------|-------------|
| `redis` | 6379 | Message broker for job queue |
| `backend` | 8000 | FastAPI API server (uvicorn with --reload) |
| `worker` | — | ARQ worker that processes queued pipeline jobs |
| `frontend` | 3000 | Next.js dev server |

All 4 services must be running for the app to work. If pipeline jobs stay "queued" with no logs, the `worker` container is likely not running — check with `make ps`.

### Volumes
Docker Compose mounts `db/`, `meetings/`, `exports/`, `supabase.json` (auth token), and `.ca-certs/` (corporate CA certs) from the host. Redis data is stored in a named volume (`redis-data`).

### Corporate Proxy / SSL
If behind a corporate TLS-inspection proxy (Zscaler, NortonLifeLock, etc.), run `make setup-ssl` to export the corporate CA, then `make down && make up`. See `.context/ctx-02-23-26-docker-ssl-corporate-proxy.md` for details.

### Environment Variables (set by Docker Compose)
- `REDIS_URL` — backend and worker use this to connect to Redis (`redis://redis:6379` in Docker)
- `BACKEND_URL` — frontend uses this for server-side rewrites (`http://backend:8000` in Docker)
- `NEXT_PUBLIC_API_URL` — frontend client-side API base (`/api` in Docker, proxied through Next.js rewrites)

### Clean Rebuild
```bash
make clean       # Remove containers, volumes, images, and .next cache
make build       # Rebuild all images from scratch (--no-cache)
```

## Pipeline CLI (single entrypoint)

These commands run directly on the host (outside Docker) for one-off operations:
```bash
python granola_pipeline.py export --all          # Export all meetings to markdown
python granola_pipeline.py export --since 2026-02-01 --limit 10
python granola_pipeline.py index --rebuild       # Build SQLite FTS5 search index
python granola_pipeline.py search "query here"   # Full-text search
python granola_pipeline.py search --type transcript "data pipeline"
python granola_pipeline.py process --limit 5     # Claude API extraction
python granola_pipeline.py sync                  # Full pipeline: export + index + process
python granola_pipeline.py status                # Token + database stats
```

### Individual scripts (if needed)
```bash
python scripts/export_all.py --limit 5
python scripts/build_index.py --rebuild
python scripts/search.py "query"
python scripts/process_meetings.py --limit 3 --model claude-sonnet-4-20250514
python scripts/build_knowledge_graph.py
```

### Dependencies (only needed for host-side CLI usage)
```bash
pip install -r requirements.txt                  # Core pipeline
pip install -r web/backend/requirements.txt      # Web backend
cd web/frontend && npm install                   # Web frontend
# Or: make install
```

## Architecture

### Data Flow
1. **Auth** (`src/auth.py`) — Reads WorkOS JWT from `~/Library/Application Support/Granola/supabase.json`. Token auto-loaded on each API call; ~6hr lifetime, refresh by reopening Granola desktop app.
2. **Export** (`scripts/export_all.py`) — Fetches documents, panels (AI summaries), and transcripts from Granola's internal API. Writes 3 files per meeting: `notes.md`, `summary.md`, `transcript.md` with YAML frontmatter.
3. **Index** (`scripts/build_index.py`) — Parses all markdown files and inserts into SQLite FTS5 database at `db/granola_search.db`.
4. **Process** (`scripts/process_meetings.py`) — Sends meeting content to Claude API, extracts action items/tags/decisions/people, writes `metadata.md`.
5. **Knowledge Graph** (`scripts/build_knowledge_graph.py`) — Builds people-meetings-topics graph from `metadata.md` files, outputs to `exports/`.

### Core Modules (`src/`)
- `config.py` — All paths, API URLs, rate-limit constants. `REPO_ROOT` is the single source of truth for paths.
- `models.py` — Dataclasses: `GranolaDocument`, `Panel`, `TranscriptEntry`, `Meeting`. All have `from_api()` class methods.
- `api_client.py` — `GranolaClient` with rate limiting (100ms), retry on 429/401, paginated document fetching.
- `converters.py` — ProseMirror JSON to markdown, HTML to markdown (via markdownify), transcript formatting with relative timestamps.
- `search_db.py` — `SearchDB` class wrapping SQLite FTS5 with `tokenize='porter unicode61'`.
- `processor.py` — Claude API extraction via `extract_meeting_intelligence()`.

### Web Layer (`web/`)
- **Backend**: FastAPI + Redis + ARQ job queue. Routers: meetings, search, pipeline, status. Reuses `src/` modules. Dockerfile at `web/backend/Dockerfile`.
- **Worker**: Same image as backend, runs `python -m arq app.worker.WorkerSettings`. Processes queued jobs. Emits structured canonical log lines (wide events) at job completion.
- **Frontend**: Next.js 15 + React 19 + Tailwind CSS 4. Pages: home, meetings list, meeting detail, search, pipeline. Dockerfile at `web/frontend/Dockerfile`.

### Meeting Output Structure
```
meetings/YYYY/MM/YYYY-MM-DD_slug/
    notes.md        # User's ProseMirror notes
    summary.md      # AI-generated panel (HTML→MD)
    transcript.md   # Speaker-labeled transcript with timestamps
    metadata.md     # Claude-extracted intelligence (created by process step)
```

All `.md` files have YAML frontmatter with `granola_id`, `title`, `date`, `type`.

### API Details
Granola internal API at `https://api.granola.ai`. All endpoints are POST. Key endpoints: `/v2/get-documents` (paginated, limit 100), `/v1/get-document-transcript`, `/v1/get-document-panels`, `/v1/get-documents-batch`. See `.context/ctx-02-22-26-api-reference.md` for full reference.

### Important Conventions
- **Docker-first development**: Always use `make up` to run the app. All testing and debugging happens inside Docker containers. Use `make logs` to inspect issues.
- Export is resumable: `db/export_progress.json` tracks completed document IDs. Safe to interrupt and re-run.
- Speaker mapping in transcripts: `"microphone"` = user ("You"), `"system"` = other participants.
- Panels use two content formats: `original_content` (HTML, preferred) and `content` (ProseMirror JSON, fallback).
- Redis URL and backend URL are configurable via env vars (`REDIS_URL`, `BACKEND_URL`). Docker Compose sets these automatically; defaults point to `localhost` for host-side usage.
- The `processed/` directory contains TSV batch files from an earlier Anthropic Batch API processing approach.
- `db/`, `meetings/`, `exports/`, `processed/` are all gitignored.
- `.context/` contains reverse-engineering documentation about the Granola API and is committed.
