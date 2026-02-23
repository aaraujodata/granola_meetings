#!/usr/bin/env python3
"""Bulk export all Granola meetings to structured markdown files.

Usage:
    python scripts/export_all.py [--limit N] [--since YYYY-MM-DD] [--ids UUID1 UUID2 ...]

Output structure:
    meetings/YYYY/MM/YYYY-MM-DD_slug/
        notes.md
        summary.md
        transcript.md
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api_client import GranolaClient, GranolaAPIError
from src.auth import is_token_valid, get_token_info
from src.config import MEETINGS_DIR, EXPORT_PROGRESS_PATH, DB_DIR
from src.converters import (
    format_transcript,
    html_to_markdown,
    prosemirror_to_markdown,
    sanitize_filename,
    calculate_duration_minutes,
)
from src.models import GranolaDocument, Meeting

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def load_progress() -> set[str]:
    """Load the set of already-exported document IDs."""
    if EXPORT_PROGRESS_PATH.exists():
        data = json.loads(EXPORT_PROGRESS_PATH.read_text())
        return set(data.get("completed", []))
    return set()


def save_progress(completed: set[str]):
    """Persist completed document IDs for resume capability."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_PROGRESS_PATH.write_text(json.dumps({"completed": sorted(completed)}, indent=2))


def meeting_output_dir(doc: GranolaDocument) -> Path:
    """Compute the output directory for a meeting: meetings/YYYY/MM/YYYY-MM-DD_slug/."""
    date_str = doc.date  # e.g. "2026-02-19"
    parts = date_str.split("-")
    if len(parts) >= 3:
        year, month = parts[0], parts[1]
    else:
        year, month = "unknown", "00"

    slug = sanitize_filename(doc.title)
    folder_name = f"{date_str}_{slug}"
    return MEETINGS_DIR / year / month / folder_name


def write_notes_md(output_dir: Path, doc: GranolaDocument):
    """Write notes.md with frontmatter."""
    content = doc.notes_markdown
    if not content and doc.notes:
        content = prosemirror_to_markdown(doc.notes)
    if not content:
        content = doc.notes_plain or ""

    if not content.strip():
        return  # Skip empty notes

    attendee_names = [a.get("name", a.get("email", "")) for a in doc.attendees]

    frontmatter = _build_frontmatter({
        "granola_id": doc.id,
        "title": doc.title,
        "date": doc.date,
        "type": "notes",
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "attendees": attendee_names or None,
        "calendar_event": doc.calendar_event_title or None,
    })

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "notes.md").write_text(f"{frontmatter}\n# {doc.title}\n\n{content}\n")


def write_summary_md(output_dir: Path, doc: GranolaDocument, panels: list):
    """Write summary.md from AI-generated panel content."""
    if not panels:
        return

    panel = panels[0]  # Primary summary panel
    content = html_to_markdown(panel.original_content)
    if not content and panel.content:
        content = prosemirror_to_markdown(panel.content)
    if not content:
        return

    frontmatter = _build_frontmatter({
        "granola_id": doc.id,
        "title": doc.title,
        "date": doc.date,
        "type": "summary",
        "template": panel.template_slug,
        "panel_id": panel.id,
    })

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.md").write_text(f"{frontmatter}\n# Summary: {doc.title}\n\n{content}\n")


def write_transcript_md(output_dir: Path, doc: GranolaDocument, transcript: list):
    """Write transcript.md with speaker labels and timestamps."""
    if not transcript:
        return

    content = format_transcript(transcript)
    duration = calculate_duration_minutes(transcript)
    sources = sorted({e.source for e in transcript})
    speaker_labels = ["You" if s == "microphone" else "Other" for s in sources]

    frontmatter = _build_frontmatter({
        "granola_id": doc.id,
        "title": doc.title,
        "date": doc.date,
        "type": "transcript",
        "total_entries": len(transcript),
        "duration_minutes": duration,
        "speakers": speaker_labels,
    })

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "transcript.md").write_text(
        f"{frontmatter}\n# Transcript: {doc.title}\n\n{content}\n"
    )


def _build_frontmatter(fields: dict) -> str:
    """Build a YAML frontmatter block from a dict, skipping None values."""
    lines = ["---"]
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f'  - "{_escape_yaml(str(item))}"')
        elif isinstance(value, str) and ("\n" in value or '"' in value or ":" in value):
            lines.append(f'{key}: "{_escape_yaml(value)}"')
        elif isinstance(value, str):
            lines.append(f'{key}: "{value}"')
        elif isinstance(value, bool):
            lines.append(f"{key}: {str(value).lower()}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def _escape_yaml(s: str) -> str:
    """Escape special chars for YAML string values."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def export_meeting(client: GranolaClient, doc: GranolaDocument) -> bool:
    """Export a single meeting: fetch panels + transcript, write files.

    Returns True if successful.
    """
    output_dir = meeting_output_dir(doc)

    try:
        # Fetch panels (AI summary)
        panels = client.get_panels(doc.id)

        # Fetch transcript
        transcript = client.get_transcript(doc.id)

        # Write files
        write_notes_md(output_dir, doc)
        write_summary_md(output_dir, doc, panels)
        write_transcript_md(output_dir, doc, transcript)

        files_written = sum(1 for f in ["notes.md", "summary.md", "transcript.md"]
                           if (output_dir / f).exists())
        log.info("  ✓ %s → %d files", doc.title[:60], files_written)
        return True

    except GranolaAPIError as e:
        log.error("  ✗ API error for %s: %s", doc.id, e)
        return False
    except Exception as e:
        log.error("  ✗ Error exporting %s: %s", doc.id, e)
        return False


def main():
    parser = argparse.ArgumentParser(description="Export Granola meetings to markdown")
    parser.add_argument("--limit", type=int, help="Max meetings to export")
    parser.add_argument("--since", type=str, help="Only export meetings after this date (YYYY-MM-DD)")
    parser.add_argument("--ids", nargs="+", help="Export specific document IDs")
    parser.add_argument("--no-resume", action="store_true", help="Ignore saved progress, re-export all")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # ── Validate token ─────────────────────────────────────────────────
    if not is_token_valid():
        info = get_token_info()
        log.error("Token expired or invalid. Remaining: %.0f seconds", info["remaining_seconds"])
        log.error("Open Granola desktop app to refresh the token, then retry.")
        sys.exit(1)

    log.info("Token valid. Starting export...")

    client = GranolaClient()

    # ── Determine which documents to export ────────────────────────────
    if args.ids:
        log.info("Fetching %d specific documents...", len(args.ids))
        documents = client.get_documents_batch(args.ids)
    else:
        log.info("Fetching all documents...")
        documents = client.get_all_documents()

    # Filter deleted
    documents = [d for d in documents if not d.deleted_at]
    log.info("Found %d active documents", len(documents))

    # Filter by date
    if args.since:
        documents = [d for d in documents if d.date >= args.since]
        log.info("After date filter (>= %s): %d documents", args.since, len(documents))

    # Apply limit
    if args.limit:
        documents = documents[:args.limit]
        log.info("Limiting to %d documents", len(documents))

    # ── Load progress for resume ───────────────────────────────────────
    # Bypass resume when the user explicitly filters with --since or --ids
    skip_resume = args.no_resume or args.since or args.ids
    completed = set() if skip_resume else load_progress()
    remaining = [d for d in documents if d.id not in completed]

    if skip_resume and not args.no_resume:
        log.info("Explicit filter detected (--since/--ids), bypassing resume progress")
    if completed:
        log.info("Resuming: %d already exported, %d remaining", len(completed), len(remaining))

    # ── Export each meeting ────────────────────────────────────────────
    success_count = 0
    error_count = 0

    for i, doc in enumerate(remaining):
        title_display = (doc.title or "Untitled")[:60]
        log.info("[%d/%d] Exporting: %s (%s)", i + 1, len(remaining), title_display, doc.date)

        if export_meeting(client, doc):
            completed.add(doc.id)
            success_count += 1
        else:
            error_count += 1

        # Save progress periodically
        if (i + 1) % 10 == 0:
            save_progress(completed)

    # ── Final save and report ──────────────────────────────────────────
    save_progress(completed)

    log.info("=" * 60)
    log.info("Export complete!")
    log.info("  Successful: %d", success_count)
    log.info("  Errors: %d", error_count)
    log.info("  Total exported (all time): %d", len(completed))
    log.info("  Output: %s", MEETINGS_DIR)


if __name__ == "__main__":
    main()
