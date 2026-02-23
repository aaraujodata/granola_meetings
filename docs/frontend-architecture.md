# Frontend Architecture: Next.js + Tailwind CSS

## The Problem It Solves

The FastAPI backend exposes 7 API endpoints, but JSON responses in a terminal aren't user-friendly. Users need a visual interface to browse 573 meetings, search with instant results, read transcripts with speaker colors, and trigger pipeline jobs with one click.

**Real scenario**: A user wants to find what was decided in the "Bank of America metrics duplication" meeting, read the full transcript, and then trigger a re-export because new meetings happened today. Without the frontend, that's three terminal commands. With the UI: search → click meeting → read transcript tab → click "Export All" button.

---

## Architecture Overview

```mermaid
flowchart TB
    subgraph BROWSER["Browser (:3000)"]
        direction TB
        subgraph PAGES["App Router Pages"]
            DASH["/ Dashboard\nStats, quick links"]
            MEET_LIST["/meetings\nPaginated list, date filter"]
            MEET_DETAIL["/meetings/[id]\nNotes | Summary | Transcript tabs"]
            SEARCH["/search\nFull-text search + filters"]
            PIPE["/pipeline\nTrigger jobs, view history"]
        end

        subgraph COMPONENTS["Shared Components"]
            MC["MeetingCard"]
            SB["SearchBar"]
            TV["TranscriptViewer"]
            JSB["JobStatusBadge"]
            PC["PipelineControls"]
        end

        subgraph INFRA["Client Infrastructure"]
            API_CLIENT["lib/api.ts\nTyped fetch wrappers"]
            TYPES["types/index.ts\nTypeScript interfaces"]
            HOOKS["hooks/useJobPoller.ts\nPoll job status every 2s"]
        end

        PAGES --> COMPONENTS
        PAGES --> INFRA
    end

    subgraph NEXTJS["Next.js Dev Server"]
        REWRITE["next.config.ts\nrewrites: /api/* →\nlocalhost:8000/api/*"]
    end

    subgraph BACKEND["FastAPI (:8000)"]
        ENDPOINTS["/api/meetings\n/api/search\n/api/status\n/api/pipeline"]
    end

    BROWSER --> NEXTJS
    NEXTJS --> BACKEND

    style PAGES fill:#1a1a2e,stroke:#0f3460,color:#fff
    style COMPONENTS fill:#1a1a2e,stroke:#e94560,color:#fff
    style INFRA fill:#1a1a2e,stroke:#533483,color:#fff
    style BACKEND fill:#1a1a2e,stroke:#16213e,color:#fff
```

---

## Page-by-Page Breakdown

### Dashboard (`/`) — `app/page.tsx`

Shows at-a-glance stats and navigation:

```mermaid
flowchart LR
    MOUNT["Page mounts"] --> FETCH["getStatus()"]
    FETCH --> RENDER["Render 4 stat cards:\n• 573 Meetings\n• 1,165 Search Entries\n• 586 Exported\n• Token: Valid (347m)"]
    RENDER --> LINKS["3 quick links:\nBrowse Meetings\nSearch\nPipeline"]

    style MOUNT fill:#0f3460,color:#fff
    style RENDER fill:#533483,color:#fff
```

**Real scenario**: User opens `localhost:3000` and immediately sees that the token expires in 347 minutes — plenty of time to run a full sync. They also see 573 meetings are indexed. They click "Search" to find a specific discussion.

---

### Meetings List (`/meetings`) — `app/meetings/page.tsx`

Paginated grid of all meetings with date filtering:

```mermaid
sequenceDiagram
    participant U as User
    participant P as Meetings Page
    participant A as API Client
    participant B as Backend

    U->>P: Navigate to /meetings
    P->>A: getMeetings(offset=0, limit=50)
    A->>B: GET /api/meetings?offset=0&limit=50
    B-->>A: {meetings: [...], total: 573}
    A-->>P: MeetingsListResponse
    P->>P: Render 50 MeetingCard components

    U->>P: Set date range: 2026-01-01 to 2026-02-28
    U->>P: Click "Filter"
    P->>A: getMeetings(0, 50, "2026-01-01", "2026-02-28")
    A->>B: GET /api/meetings?offset=0&limit=50&date_from=2026-01-01&date_to=2026-02-28
    B-->>A: {meetings: [...], total: 42}
    A-->>P: Filtered results
    P->>P: Re-render with 42 meetings

    U->>P: Click "Next" page
    P->>A: getMeetings(50, 50, "2026-01-01", "2026-02-28")
```

Each meeting renders as a `MeetingCard` with:
- **Title** (truncated if too long)
- **Date** (e.g., "2026-02-19")
- **Content badges**: Notes (blue if exists, gray if not), Summary, Transcript

**Real scenario**: User filters to January 2026, sees 38 meetings. Each card shows that most have Summary + Transcript but only a few have Notes (because the user didn't write notes for every meeting).

---

### Meeting Detail (`/meetings/[id]`) — `app/meetings/[id]/page.tsx`

Tabbed view of a single meeting's full content:

```mermaid
stateDiagram-v2
    [*] --> Loading: Navigate to /meetings/{id}
    Loading --> Summary: has_summary = true
    Loading --> Notes: has_summary = false, has_notes = true
    Loading --> Transcript: only has_transcript

    Summary --> Notes: Click "Notes" tab
    Summary --> Transcript: Click "Transcript" tab
    Notes --> Summary: Click "Summary" tab
    Notes --> Transcript: Click "Transcript" tab
    Transcript --> Summary: Click "Summary" tab
    Transcript --> Notes: Click "Notes" tab
```

**Tab rendering**:
- **Notes tab** — Raw markdown (whitespace-preserved)
- **Summary tab** — AI-generated summary (whitespace-preserved)
- **Transcript tab** — Uses `TranscriptViewer` component with speaker colors

**Real scenario**: User clicks on "Bank of America metrics duplication investigation with Alexis" from the meetings list. The detail page loads with:
- Summary tab active (default): Shows key decisions and action items in markdown
- Transcript tab: 13,679 characters of conversation, with "You" in blue and "Other" in gray
- Notes tab: Disabled (grayed out) because no user notes exist for this meeting

---

### Search (`/search`) — `app/search/page.tsx`

Full-text search with type filtering and date range:

```mermaid
sequenceDiagram
    participant U as User
    participant P as Search Page
    participant SB as SearchBar Component
    participant A as API Client
    participant B as Backend

    U->>SB: Type "Bank of America"
    U->>SB: Select type: "summary"
    U->>SB: Click "Search"
    SB->>P: onSearch("Bank of America", "summary")
    P->>A: search("Bank of America", "summary")
    A->>B: GET /api/search?q=Bank+of+America&type=summary
    B-->>A: SearchResult[] (7 results)
    A-->>P: Results with snippets
    P->>P: Render result cards with<br/>highlighted snippets

    U->>P: Click result for meeting "DataOps Stand-up"
    P->>P: Navigate to /meetings/{id}
```

**Snippet rendering**: The backend returns `**Bank**` markers around matches. The frontend converts these to `<mark>` tags with yellow highlighting:

```
Input:  "...Alexis **Bank** and Gamebridge are UAT ready..."
Output: "...Alexis <mark>Bank</mark> and Gamebridge are UAT ready..."
```

**Real scenario**: User searches for `"dbt airflow"` (with quotes for phrase match), filters to summaries only. Gets 12 results showing key decisions about their dbt/Airflow pipeline, not raw transcript chatter.

---

### Pipeline (`/pipeline`) — `app/pipeline/page.tsx`

Dashboard for triggering and monitoring async pipeline jobs:

```mermaid
sequenceDiagram
    participant U as User
    participant P as Pipeline Page
    participant PC as PipelineControls
    participant H as useJobPoller Hook
    participant A as API Client
    participant B as Backend

    U->>PC: Click "Export All"
    PC->>P: onTrigger("export")
    P->>A: triggerPipeline("export")
    A->>B: POST /api/pipeline/export
    B-->>A: {job_id: "abc-123", status: "queued"}
    A-->>P: JobResponse
    P->>H: Start polling job "abc-123"

    loop Every 2 seconds
        H->>A: getJobStatus("abc-123")
        A->>B: GET /api/pipeline/jobs/abc-123
        B-->>A: {status: "running"}
        A-->>H: Update state
        H-->>P: job.status = "running"
        P->>P: Show blue spinner badge
    end

    Note over B: Export completes after ~60s
    H->>A: getJobStatus("abc-123")
    A->>B: GET /api/pipeline/jobs/abc-123
    B-->>A: {status: "completed", result: "Export finished"}
    H-->>P: job.status = "completed"
    H->>H: Stop polling
    P->>P: Show green badge, refresh job list
```

**Button states**: All 4 pipeline buttons are disabled while a job is running (`max_jobs=1` on the worker means only one can run at a time).

**Real scenario**: User clicks "Full Sync" after recording 5 new meetings today. The button group disables, a blue "running" badge appears with a spinner. After ~90 seconds (export + index + process), the badge turns green. The user navigates to /meetings to see their new meetings in the list.

---

## Component Details

### `MeetingCard.tsx`

Renders a single meeting in the list grid:

```
┌──────────────────────────────────┐
│ Bank of America metrics dupl...  │
│ 2026-02-19                       │
│                                  │
│ [Notes] [Summary] [Transcript]   │
│  gray    blue      blue          │
└──────────────────────────────────┘
```

- Blue badges = content exists on disk
- Gray badges = no file found
- Entire card is a link to `/meetings/{id}`

### `SearchBar.tsx`

Search form with three filter controls:

```
┌─────────────────────────────┬──────────┐
│ Search meetings...          │ [Search] │
└─────────────────────────────┴──────────┘
[All types ▼]  [From: ____]  [To: ____]
```

- Dropdown filters: All types, Notes, Summary, Transcript
- Date range pickers for temporal filtering
- Submit triggers the `onSearch` callback

### `TranscriptViewer.tsx`

Parses transcript markdown and renders with speaker colors:

```
00:12:34  You    What is the plan for the Bank of America fix?
00:12:45  Other  We need to check the attribution keys first.
00:12:52  You    Can you pull the source table data?
00:13:01  Other  Yes, I'll compare sill table vs final view.
```

- Parses `**[HH:MM:SS] Speaker:** text` format from markdown
- "You" = blue (`text-blue-600`)
- "Other" = gray (`text-gray-500`)
- Timestamps in monospace tabular numerals
- Falls back to raw `<pre>` if parsing fails

### `JobStatusBadge.tsx`

Colored status indicator:

| Status | Color | Extra |
|--------|-------|-------|
| queued | Yellow `bg-yellow-100` | — |
| running | Blue `bg-blue-100` | Spinning border animation |
| completed | Green `bg-green-100` | — |
| failed | Red `bg-red-100` | — |

### `PipelineControls.tsx`

2x2 button grid:

```
┌─────────────────────┬─────────────────────────┐
│ Export All           │ Rebuild Index            │
│ Fetch from Granola   │ Rebuild SQLite FTS5      │
├─────────────────────┼─────────────────────────┤
│ Process with Claude  │ Full Sync                │
│ Extract intelligence │ Export + Index + Process  │
└─────────────────────┴─────────────────────────┘
```

All buttons disabled while any job is running.

---

## `useJobPoller` Hook — Polling Pattern

```mermaid
stateDiagram-v2
    [*] --> Idle: jobId = null
    Idle --> Polling: setJobId("abc-123")
    Polling --> Polling: GET status every 2s
    Polling --> Done: status = "completed"
    Polling --> Failed: status = "failed"
    Done --> Idle: Clear jobId
    Failed --> Idle: Clear jobId
```

**Key behaviors**:
- Starts polling immediately when `jobId` is set
- Polls `GET /api/pipeline/jobs/{id}` every 2 seconds
- Automatically stops when status is terminal (`completed` or `failed`)
- Cleans up interval on unmount (prevents memory leaks)

---

## Data Flow: Types → API → Components

```mermaid
flowchart LR
    subgraph TYPES["types/index.ts"]
        TS_MEET["MeetingSummary\nMeetingDetail"]
        TS_SEARCH["SearchResult"]
        TS_JOB["JobResponse\nPipelineAction"]
        TS_STATUS["StatusResponse"]
    end

    subgraph API["lib/api.ts"]
        F_MEET["getMeetings()\ngetMeeting()"]
        F_SEARCH["search()"]
        F_JOB["triggerPipeline()\ngetJobStatus()\ngetJobs()"]
        F_STATUS["getStatus()"]
    end

    subgraph PAGES["Pages"]
        P_DASH["Dashboard"]
        P_MEET["Meetings List\nMeeting Detail"]
        P_SEARCH["Search"]
        P_PIPE["Pipeline"]
    end

    TS_MEET --> F_MEET --> P_MEET
    TS_SEARCH --> F_SEARCH --> P_SEARCH
    TS_JOB --> F_JOB --> P_PIPE
    TS_STATUS --> F_STATUS --> P_DASH

    style TYPES fill:#1a1a2e,stroke:#0f3460,color:#fff
    style API fill:#1a1a2e,stroke:#e94560,color:#fff
    style PAGES fill:#1a1a2e,stroke:#533483,color:#fff
```

The TypeScript interfaces in `types/index.ts` mirror the Pydantic models in `app/schemas.py` exactly — same field names, same types. This ensures type safety from database to browser.

---

## Next.js Configuration

### API Proxy (`next.config.ts`)

```typescript
async rewrites() {
  return [{ source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' }];
}
```

**Why proxy?** The frontend runs on `:3000`, the backend on `:8000`. Without the proxy, every fetch call would need `http://localhost:8000` and CORS would block cross-origin requests from the browser. The rewrite makes all API calls same-origin.

### Tailwind CSS v4 (`globals.css`)

```css
@import "tailwindcss";
@source "..";
```

The `@source ".."` directive tells Tailwind v4 to scan `src/` (one level up from `src/app/globals.css`) for utility classes used in components, hooks, and pages.

---

## Real Scenario: User's Daily Workflow

```mermaid
flowchart TB
    START["User opens localhost:3000"]
    DASH["Dashboard: 573 meetings,\ntoken valid, 347m remaining"]
    SEARCH_Q["Searches: 'sprint planning Q1'"]
    RESULTS["7 results ranked by relevance"]
    CLICK["Clicks: 'Data Sprint Planning'"]
    SUMMARY["Reads Summary tab:\nkey decisions + action items"]
    TRANSCRIPT["Switches to Transcript tab:\nreads exact conversation"]
    PIPE["Navigates to Pipeline"]
    SYNC["Clicks 'Full Sync'"]
    WAIT["Badge: 🔵 running..."]
    DONE["Badge: 🟢 completed"]
    NEW["Returns to /meetings:\nsees 5 new meetings"]

    START --> DASH --> SEARCH_Q --> RESULTS --> CLICK
    CLICK --> SUMMARY --> TRANSCRIPT
    TRANSCRIPT --> PIPE --> SYNC --> WAIT --> DONE --> NEW

    style START fill:#0f3460,color:#fff
    style DONE fill:#16213e,color:#fff
    style NEW fill:#533483,color:#fff
```
