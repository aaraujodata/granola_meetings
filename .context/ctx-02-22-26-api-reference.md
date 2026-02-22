# Granola Internal API Reference

> Reverse-engineered from Granola desktop app v5.354.0 on 2026-02-22.
> All endpoints confirmed working with live tests.

## Base URL

```
https://api.granola.ai
```

## Required Headers

```http
Authorization: Bearer <access_token>
Content-Type: application/json
User-Agent: Granola/5.354.0
X-Client-Version: 5.354.0
```

---

## Endpoints

### 1. `POST /v2/get-documents`

Paginated list of all user documents (meetings).

**Request:**
```json
{
  "limit": 100,
  "offset": 0,
  "include_last_viewed_panel": false
}
```

**Response:**
```json
{
  "docs": [ { /* Document objects - 39 keys each */ } ],
  "deleted": [ "uuid1", "uuid2" ]
}
```

**Notes:**
- Max `limit` is 100
- Total docs ~586 (offset 500 returns 86, offset 600 returns 0)
- 6 pages needed to fetch all: offsets 0, 100, 200, 300, 400, 500
- `deleted` array contains UUIDs of deleted documents

---

### 2. `POST /v1/get-document-transcript`

Full transcript for a single document.

**Request:**
```json
{
  "document_id": "<uuid>"
}
```

**Response:** Array of transcript entries directly (not wrapped in object):
```json
[
  {
    "document_id": "<uuid>",
    "start_timestamp": "2026-02-19T23:39:02.305Z",
    "text": "Okay. So give me",
    "source": "system",
    "id": "<uuid>",
    "is_final": true,
    "end_timestamp": "2026-02-19T23:39:05.175Z"
  }
]
```

**Speaker mapping:**
- `"microphone"` = user (You)
- `"system"` = other participants

**Notes:**
- Returns empty array `[]` for meetings without transcripts
- Only 4 transcripts cached locally; rest must be fetched via API

---

### 3. `POST /v1/get-document-panels`

AI-generated summary panels for a document.

**Request:**
```json
{
  "document_id": "<uuid>"
}
```

**Response:** Array of panel objects:
```json
[
  {
    "document_id": "<uuid>",
    "id": "<panel-uuid>",
    "created_at": "2026-02-19T23:59:52.936Z",
    "title": "Summary",
    "content": { /* ProseMirror JSON */ },
    "deleted_at": null,
    "template_slug": "meeting-summary-consolidated",
    "last_viewed_at": "...",
    "updated_at": "...",
    "content_updated_at": "...",
    "affinity_note_id": null,
    "original_content": "<h3>Title</h3><ul><li>Point 1</li></ul>",
    "suggested_questions": null,
    "generated_lines": [ {"text": "...", "matches": false} ],
    "user_feedback": null,
    "ydoc_version": null
  }
]
```

**Notes:**
- Most documents have 1 panel (the "Summary")
- `original_content` is HTML — the primary content to convert to markdown
- `content` is ProseMirror JSON (alternative structured format)
- `template_slug` values seen: `meeting-summary-consolidated`, `v2:meeting-summary-consolidated`

---

### 4. `POST /v1/get-documents-batch`

Fetch multiple documents by ID at once.

**Request:**
```json
{
  "document_ids": ["<uuid1>", "<uuid2>"]
}
```

**Response:**
```json
{
  "docs": [ { /* Document objects */ } ]
}
```

**Notes:**
- Key must be `document_ids` (not `ids`, `documentIds`, or `doc_ids`)
- Other payload keys return 400 Bad Request

---

### 5. `POST /v1/get-workspaces`

Workspace information.

**Request:**
```json
{}
```

**Response:**
```json
{
  "workspaces": [
    {
      "workspace": {
        "workspace_id": "<uuid>",
        "slug": "consumertrack.com",
        "display_name": "AlexisGBR",
        "is_locked": true,
        "created_at": "...",
        "updated_at": "...",
        "privacy_mode_enabled": false,
        "sharing_link_visibility": null,
        "transcript_retention_hours": null,
        "logo_url": "https://..."
      }
    }
  ]
}
```

---

## Rate Limiting

- No explicit rate limit headers observed in testing
- Conservative approach: 100ms between requests (~10 req/sec)
- Retry on 429 with exponential backoff
- Refresh token on 401

## Error Responses

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad Request (invalid payload key names) |
| 401 | Unauthorized (expired token) |
| 404 | Not Found (invalid endpoint) |
| 429 | Rate limited (not observed but expected) |
