#!/usr/bin/env python3
"""Build the SQLite FTS5 search index from exported markdown files.

Walks meetings/ directory, parses frontmatter + content from each .md file,
and inserts into the SQLite database.

Usage:
    python scripts/build_index.py [--rebuild]
"""

import argparse
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import MEETINGS_DIR, SEARCH_DB_PATH
from src.search_db import SearchDB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and return (metadata dict, body content)."""
    match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not match:
        return {}, text

    fm_text = match.group(1)
    body = match.group(2)

    metadata = {}
    for line in fm_text.split("\n"):
        if ":" in line and not line.startswith("  "):
            key, _, value = line.partition(":")
            value = value.strip().strip('"')
            metadata[key.strip()] = value

    return metadata, body


def index_meeting_dir(db: SearchDB, meeting_dir: Path) -> bool:
    """Index all markdown files in a single meeting directory.

    Returns True if any content was indexed.
    """
    indexed = False
    meeting_id = None
    title = ""
    date = ""

    for md_file in sorted(meeting_dir.glob("*.md")):
        if md_file.name == "metadata.md":
            continue

        text = md_file.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(text)

        if not meeting_id:
            meeting_id = metadata.get("granola_id", meeting_dir.name)
            title = metadata.get("title", meeting_dir.name)
            date = metadata.get("date", "")

        content_type = metadata.get("type", md_file.stem)

        if content_type == "notes":
            db.insert_notes(meeting_id, body.strip())
        elif content_type == "summary":
            panel_id = metadata.get("panel_id", "")
            template = metadata.get("template", "")
            db.insert_summary(meeting_id, panel_id, template, body.strip())
        elif content_type == "transcript":
            # Store the full transcript body for search (individual entries
            # already have speaker attribution in the formatted text)
            pass

        # Index all content types in FTS5
        db.index_content(meeting_id, title, content_type, body.strip())
        indexed = True

    if meeting_id and indexed:
        created_at = ""
        updated_at = ""
        attendees = ""
        calendar_event = ""
        workspace_id = ""

        # Re-read notes.md for full metadata
        notes_path = meeting_dir / "notes.md"
        if notes_path.exists():
            meta, _ = parse_frontmatter(notes_path.read_text(encoding="utf-8"))
            created_at = meta.get("created_at", "")
            updated_at = meta.get("updated_at", "")
            calendar_event = meta.get("calendar_event", "")

        db.upsert_meeting(
            meeting_id=meeting_id,
            title=title,
            date=date,
            created_at=created_at,
            updated_at=updated_at,
            attendees=attendees,
            calendar_event=calendar_event,
            workspace_id=workspace_id,
        )

    return indexed


def main():
    parser = argparse.ArgumentParser(description="Build search index from exported meetings")
    parser.add_argument("--rebuild", action="store_true",
                        help="Drop and rebuild the entire index")
    args = parser.parse_args()

    db = SearchDB()
    db.initialize()

    if args.rebuild:
        log.info("Clearing existing data for rebuild...")
        conn = db._connect()
        for table in ["search_index", "notes", "summaries", "transcripts", "meetings"]:
            conn.execute(f"DELETE FROM {table}")
        conn.commit()

    if not MEETINGS_DIR.exists():
        log.error("No meetings/ directory found. Run export first.")
        sys.exit(1)

    # Walk all meeting directories (meetings/YYYY/MM/YYYY-MM-DD_slug/)
    meeting_dirs = sorted(MEETINGS_DIR.glob("*/*/*/"))
    log.info("Found %d meeting directories", len(meeting_dirs))

    indexed_count = 0
    for i, meeting_dir in enumerate(meeting_dirs):
        if not meeting_dir.is_dir():
            continue

        if index_meeting_dir(db, meeting_dir):
            indexed_count += 1

        if (i + 1) % 50 == 0:
            db.commit()
            log.info("Progress: %d/%d directories processed", i + 1, len(meeting_dirs))

    db.commit()
    db.close()

    stats = SearchDB()
    stats.initialize()
    counts = stats.get_stats()
    stats.close()

    log.info("=" * 60)
    log.info("Index build complete!")
    log.info("  Meetings indexed: %d", indexed_count)
    log.info("  DB stats: %s", counts)
    log.info("  Database: %s", SEARCH_DB_PATH)


if __name__ == "__main__":
    main()
