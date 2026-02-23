# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a data pipeline that exports meeting data from the Granola desktop app's internal API, stores it as structured markdown, builds a full-text search index, and optionally enriches meetings with Claude API-powered intelligence extraction. It also includes a web UI (FastAPI + Next.js) for browsing and searching meetings.

## Key Commands

### Pipeline CLI (single entrypoint)
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

### Web UI
```bash
# Backend (requires Redis running)
cd web/backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd web/frontend && npm run dev   # http://localhost:3000
```

### Dependencies
```bash
pip install -r requirements.txt                  # Core pipeline
pip install -r web/backend/requirements.txt      # Web backend
cd web/frontend && npm install                   # Web frontend
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
- **Backend**: FastAPI + Redis + ARQ job queue. Routers: meetings, search, pipeline, status. Reuses `src/` modules.
- **Frontend**: Next.js 15 + React 19 + Tailwind CSS 4. Pages: home, meetings list, search.

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
- Export is resumable: `db/export_progress.json` tracks completed document IDs. Safe to interrupt and re-run.
- Speaker mapping in transcripts: `"microphone"` = user ("You"), `"system"` = other participants.
- Panels use two content formats: `original_content` (HTML, preferred) and `content` (ProseMirror JSON, fallback).
- The `processed/` directory contains TSV batch files from an earlier Anthropic Batch API processing approach.
- `db/`, `meetings/`, `exports/`, `processed/` are all gitignored.
- `.context/` contains reverse-engineering documentation about the Granola API and is committed.
