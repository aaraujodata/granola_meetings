"""Meetings router: list and detail endpoints."""

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import get_search_db
from app.schemas import MeetingSummary, MeetingDetail, MeetingsListResponse
from src.config import MEETINGS_DIR

router = APIRouter(tags=["meetings"])


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and return (metadata, body)."""
    match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not match:
        return {}, text

    fm_text = match.group(1)
    body = match.group(2)

    metadata = {}
    current_key = None
    current_list = None

    for line in fm_text.split("\n"):
        if line.startswith("  - "):
            if current_key and current_list is not None:
                current_list.append(line.strip()[2:].strip().strip('"'))
        elif ":" in line and not line.startswith("  "):
            if current_key and current_list is not None:
                metadata[current_key] = current_list

            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"')

            if not value:
                current_key = key
                current_list = []
            else:
                metadata[key] = value
                current_key = None
                current_list = None

    if current_key and current_list is not None:
        metadata[current_key] = current_list

    return metadata, body


@router.get("/meetings", response_model=MeetingsListResponse)
def list_meetings(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
):
    db = get_search_db()
    conn = db._connect()

    where_clauses = []
    params: list = []

    if date_from:
        where_clauses.append("date >= ?")
        params.append(date_from)
    if date_to:
        where_clauses.append("date <= ?")
        params.append(date_to)

    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Total count
    count_sql = f"SELECT COUNT(*) FROM meetings {where}"
    total = conn.execute(count_sql, params).fetchone()[0]

    # Paginated results
    sql = f"""
        SELECT id, title, date FROM meetings
        {where}
        ORDER BY date DESC
        LIMIT ? OFFSET ?
    """
    rows = conn.execute(sql, params + [limit, offset]).fetchall()

    meetings = []
    for row in rows:
        meeting_id = row["id"]
        title = row["title"]
        date = row["date"]

        # Check which content files exist on disk
        meeting_dir = _find_meeting_dir(meeting_id, date, title)
        has_notes = False
        has_summary = False
        has_transcript = False

        if meeting_dir and meeting_dir.exists():
            has_notes = (meeting_dir / "notes.md").exists()
            has_summary = (meeting_dir / "summary.md").exists()
            has_transcript = (meeting_dir / "transcript.md").exists()

        meetings.append(MeetingSummary(
            id=meeting_id,
            title=title or "Untitled",
            date=date or "",
            has_notes=has_notes,
            has_summary=has_summary,
            has_transcript=has_transcript,
        ))

    return MeetingsListResponse(
        meetings=meetings,
        total=total,
        offset=offset,
        limit=limit,
    )


def _find_meeting_dir(meeting_id: str, date: str, title: str) -> Path | None:
    """Locate the meeting directory on disk by scanning for matching frontmatter ID."""
    if not date:
        return None

    parts = date.split("-")
    if len(parts) < 3:
        return None

    year, month = parts[0], parts[1]
    month_dir = MEETINGS_DIR / year / month

    if not month_dir.exists():
        return None

    # Look for directory starting with the date
    candidates = []
    for d in month_dir.iterdir():
        if d.is_dir() and d.name.startswith(date):
            # Verify by checking frontmatter granola_id in any .md file
            for md_file in d.glob("*.md"):
                if md_file.name == "metadata.md":
                    continue
                text = md_file.read_text(encoding="utf-8")
                meta, _ = _parse_frontmatter(text)
                if meta.get("granola_id") == meeting_id:
                    return d
            candidates.append(d)

    # Fallback: if only one directory matches the date, assume it's correct
    if len(candidates) == 1:
        return candidates[0]

    return None


@router.get("/meetings/{meeting_id}", response_model=MeetingDetail)
def get_meeting(meeting_id: str):
    db = get_search_db()
    conn = db._connect()

    row = conn.execute(
        "SELECT id, title, date FROM meetings WHERE id = ?",
        (meeting_id,),
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Meeting not found")

    title = row["title"]
    date = row["date"]

    meeting_dir = _find_meeting_dir(meeting_id, date, title)

    notes_content = ""
    summary_content = ""
    transcript_content = ""
    attendees: list[str] = []
    created_at = ""
    updated_at = ""
    calendar_event = ""

    has_notes = False
    has_summary = False
    has_transcript = False

    if meeting_dir and meeting_dir.exists():
        # Notes
        notes_path = meeting_dir / "notes.md"
        if notes_path.exists():
            has_notes = True
            meta, body = _parse_frontmatter(notes_path.read_text(encoding="utf-8"))
            notes_content = body.strip()
            created_at = meta.get("created_at", "")
            updated_at = meta.get("updated_at", "")
            calendar_event = meta.get("calendar_event", "")
            att = meta.get("attendees", [])
            if isinstance(att, list):
                attendees = att

        # Summary
        summary_path = meeting_dir / "summary.md"
        if summary_path.exists():
            has_summary = True
            _, body = _parse_frontmatter(summary_path.read_text(encoding="utf-8"))
            summary_content = body.strip()

        # Transcript
        transcript_path = meeting_dir / "transcript.md"
        if transcript_path.exists():
            has_transcript = True
            _, body = _parse_frontmatter(transcript_path.read_text(encoding="utf-8"))
            transcript_content = body.strip()

    return MeetingDetail(
        id=meeting_id,
        title=title or "Untitled",
        date=date or "",
        has_notes=has_notes,
        has_summary=has_summary,
        has_transcript=has_transcript,
        notes_content=notes_content,
        summary_content=summary_content,
        transcript_content=transcript_content,
        attendees=attendees,
        created_at=created_at,
        updated_at=updated_at,
        calendar_event=calendar_event,
    )
