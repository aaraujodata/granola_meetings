# Granola Local Cache Map

## File Location

```
~/Library/Application Support/Granola/cache-v3.json
```

Size: ~22MB

## Structure

```
cache-v3.json
  └── cache (JSON string — must be parsed twice)
       └── state
            ├── documents          → dict (587 entries) — full document metadata + notes
            ├── documentPanels     → dict (570 entries) — AI summaries, keyed by document_id
            ├── transcripts        → dict (4 entries)   — ONLY 4 cached locally!
            ├── events             → list (5 entries)    — upcoming calendar events
            ├── panelTemplates     → list (30 entries)   — available summary templates
            ├── people             → list (3 entries)    — contact info
            ├── calendars          → list (5 entries)    — connected calendars
            ├── meetingsMetadata   → dict (129 entries)  — calendar metadata for meetings
            ├── featureFlags       → dict (253 entries)  — feature toggles
            ├── workspacesById     → dict                — workspace info
            └── ... (40+ other state keys for UI state, chat history, etc.)
```

## Key Insight: What's Local vs API-Only

| Data | Local Cache | API Required |
|------|-------------|--------------|
| Document metadata (title, dates, people) | 587 ✅ | Available via /v2/get-documents |
| User notes (ProseMirror + markdown) | 587 ✅ | Available in document response |
| AI summary panels (HTML) | 570 ✅ | Available via /v1/get-document-panels |
| **Transcripts** | **4 only** ❌ | **Must fetch 583 via API** |

## Reading the Cache

```python
import json

with open(cache_path) as f:
    raw = json.load(f)

# Double-parse: top-level "cache" is a JSON string
cache = json.loads(raw["cache"])
state = cache["state"]

# Access documents
documents = state["documents"]  # dict keyed by UUID
print(len(documents))  # 587

# Access panels (keyed by document_id, then by panel_id)
panels = state["documentPanels"]  # dict[doc_id] -> dict[panel_id] -> panel_obj
for doc_id, panel_dict in panels.items():
    for panel_id, panel in panel_dict.items():
        print(panel["original_content"][:100])

# Access transcripts (only 4!)
transcripts = state["transcripts"]  # dict[doc_id] -> list of entries
for doc_id, entries in transcripts.items():
    print(f"{doc_id}: {len(entries)} entries")
```

## Optimization Strategy

Since documents and panels are already cached locally (587 and 570 respectively), the export pipeline can:

1. Read documents + panels from local cache (instant, no API calls)
2. Only call API for transcripts (583 calls needed)
3. Fall back to API for any missing panels (17 documents without panels)

This reduces API calls from ~1,174 (docs + panels + transcripts) to ~600 (transcripts only + missing panels).
