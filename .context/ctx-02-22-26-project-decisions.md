# Project Architecture Decisions

## Why Internal API Over Granola MCP

- Granola's official MCP tools (query_granola_meetings, list_meetings, get_meetings) are designed for conversational queries, not bulk export
- MCP has no endpoint for raw transcript access
- MCP responses are AI-summarized (lossy) — we want raw data
- Internal API gives us full control over pagination, rate limiting, and data format
- We confirmed 5 working endpoints that cover all data types

## Why File-Per-Aspect Over Single File

Each meeting gets 3 files (notes.md, summary.md, transcript.md) instead of one combined file because:

- **Separation of concerns**: User notes, AI summaries, and raw transcripts serve different purposes
- **Size management**: Transcripts can be very large (253+ entries); separate files keep things browsable
- **Selective processing**: Can search/process only summaries or only transcripts
- **Incremental updates**: Can re-export just transcripts without touching notes

## Why SQLite FTS5 Over Alternatives

- **vs. Elasticsearch**: SQLite is zero-config, embedded, no server needed
- **vs. Plain grep**: FTS5 gives ranked results, porter stemming, phrase queries
- **vs. Tantivy/Whoosh**: SQLite is stdlib Python, no extra binary dependencies
- **vs. Vector DB**: Full-text search is the primary need; semantic search can be layered later
- FTS5 supports `tokenize='porter unicode61'` for English stemming + Unicode support

## Why Python Over TypeScript/Other

- Granola's API returns JSON — Python's json/requests are natural fit
- SQLite is in Python stdlib
- markdownify library handles HTML→MD conversion
- anthropic SDK for Claude API processing
- All dependencies are lightweight and well-maintained

## Directory Layout Rationale

```
meetings/YYYY/MM/YYYY-MM-DD_slug/   — Date-organized for chronological browsing
db/                                  — SQLite + progress tracking (gitignored)
exports/                             — Analysis outputs (gitignored)
.context/                            — Reverse-engineering knowledge (committed)
src/                                 — Reusable library code
scripts/                             — Executable scripts
```

## Rate Limiting Strategy

- 100ms between API calls (conservative, ~10 req/sec)
- Total: 586 docs × ~1 transcript call each × 100ms ≈ 1 minute
- Exponential backoff on 429 (not yet observed)
- Auto-refresh token on 401

## Resume Capability

- `db/export_progress.json` tracks completed document IDs
- Re-running export skips already-exported documents
- Safe to interrupt and resume at any point
