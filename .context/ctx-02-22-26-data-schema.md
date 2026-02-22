# Granola Data Schemas

## Document (39 keys)

From `/v2/get-documents` and local cache `state.documents`:

| Key | Type | Description |
|-----|------|-------------|
| `id` | string (UUID) | Document primary key |
| `title` | string | Meeting title |
| `created_at` | string (ISO 8601) | Creation timestamp |
| `updated_at` | string (ISO 8601) | Last update timestamp |
| `deleted_at` | string/null | Soft delete timestamp |
| `type` | string | Always "meeting" |
| `status` | string/null | Document status |
| `user_id` | string (UUID) | Owner user ID |
| `workspace_id` | string (UUID) | Workspace this belongs to |
| `notes` | object | ProseMirror JSON document (`{type: "doc", content: [...]}`) |
| `notes_markdown` | string | Pre-rendered markdown of notes (may be empty) |
| `notes_plain` | string | Plain text version of notes |
| `summary` | string/null | Brief summary |
| `overview` | string/null | Overview text |
| `chapters` | array/null | Meeting chapters |
| `people` | object | `{url, title, creator, attendees, created_at}` |
| `google_calendar_event` | object/null | `{id, end, etag, kind, start, status, created, ...}` |
| `creation_source` | string | e.g. "macOS" |
| `transcribe` | bool | Whether transcription was enabled |
| `transcript_deleted_at` | string/null | When transcript was deleted |
| `valid_meeting` | bool | Whether this is a valid meeting |
| `public` | bool | Public visibility |
| `privacy_mode_enabled` | bool | Privacy mode |
| `has_shareable_link` | bool | Has sharing link |
| `sharing_link_visibility` | string/null | "public" or null |
| `show_private_notes` | bool | Show private notes |
| `visibility` | string/null | Visibility setting |
| `selected_template` | string/null | Panel template selection |
| `subscription_plan_id` | string | e.g. "granola.plan.free-trial.v1" |
| `meeting_end_count` | int | Number of meeting end signals |
| `metadata` | object/null | Additional metadata |
| `attachments` | array | File attachments |
| `notification_config` | object/null | Notification settings |
| `audio_file_handle` | string/null | Audio file reference |
| `external_transcription_id` | string/null | External transcription service ID |
| `cloned_from` | string/null | If cloned, source document ID |
| `affinity_note_id` | string/null | Affinity CRM integration |
| `attio_shared_at` | string/null | Attio CRM integration |
| `hubspot_note_url` | string/null | HubSpot CRM integration |

### people Object Structure

```json
{
  "url": "https://www.google.com/calendar/event?eid=...",
  "title": "Meeting Title",
  "creator": {
    "name": "Alexis Araujo",
    "email": "aaraujo@consumertrack.com",
    "details": { "person": { ... } }
  },
  "attendees": [
    {
      "name": "Person Name",
      "email": "person@example.com",
      "details": { ... }
    }
  ],
  "created_at": "2025-07-14T..."
}
```

### google_calendar_event Structure

```json
{
  "id": "<google-event-id>",
  "end": { "dateTime": "2025-07-15T12:00:00-06:00", "timeZone": "America/Chicago" },
  "start": { "dateTime": "2025-07-15T11:30:00-06:00", "timeZone": "America/Chicago" },
  "etag": "\"...\"",
  "kind": "calendar#event",
  "status": "confirmed",
  "created": "2025-07-14T..."
}
```

---

## Panel (16 keys)

From `/v1/get-document-panels`:

| Key | Type | Description |
|-----|------|-------------|
| `id` | string (UUID) | Panel primary key |
| `document_id` | string (UUID) | Parent document |
| `title` | string | Usually "Summary" |
| `template_slug` | string | e.g. "meeting-summary-consolidated", "v2:meeting-summary-consolidated" |
| `content` | object | ProseMirror JSON document |
| `original_content` | string (HTML) | AI-generated summary as HTML |
| `created_at` | string (ISO 8601) | Creation timestamp |
| `updated_at` | string (ISO 8601) | Last update |
| `content_updated_at` | string (ISO 8601) | Content-specific update |
| `deleted_at` | string/null | Soft delete |
| `last_viewed_at` | string (ISO 8601) | Last viewed |
| `affinity_note_id` | string/null | CRM integration |
| `suggested_questions` | array/null | AI-suggested follow-up questions |
| `generated_lines` | array | `[{text: string, matches: bool}]` |
| `user_feedback` | string/null | User feedback on summary |
| `ydoc_version` | int/null | Yjs document version |

### original_content HTML Format

```html
<h3>Section Title</h3>
<ul>
<li>Bullet point 1</li>
<li>Bullet point 2
<ul>
<li>Sub-bullet</li>
</ul>
</li>
</ul>
<h3>Another Section</h3>
<ul>
<li>More content</li>
</ul>
```

---

## Transcript Entry (7 keys)

From `/v1/get-document-transcript`:

| Key | Type | Description |
|-----|------|-------------|
| `id` | string (UUID) | Entry primary key |
| `document_id` | string (UUID) | Parent document |
| `text` | string | Spoken text content |
| `source` | string | `"microphone"` (user) or `"system"` (others) |
| `start_timestamp` | string (ISO 8601) | When this segment started |
| `end_timestamp` | string (ISO 8601) | When this segment ended |
| `is_final` | bool | Whether transcription is finalized |

---

## Meetings Metadata (7 keys)

From local cache `state.meetingsMetadata` (129 entries):

| Key | Type | Description |
|-----|------|-------------|
| `title` | string | Meeting title |
| `url` | string | Calendar event URL |
| `creator` | object | `{name, email}` |
| `attendees` | array | `[{name, email, details}]` |
| `conferencing` | object | Conference link info |
| `created_at` | string | Creation timestamp |
| `sharing_link_visibility` | string/null | Sharing setting |
