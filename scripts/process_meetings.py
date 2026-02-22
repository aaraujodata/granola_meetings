#!/usr/bin/env python3
"""Process exported meetings with Claude API to extract intelligence.

For each meeting, reads notes.md + summary.md + transcript.md, sends to Claude
for extraction, and writes metadata.md.

Usage:
    python scripts/process_meetings.py [--limit N] [--since YYYY-MM-DD] [--dry-run]
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import MEETINGS_DIR
from src.processor import extract_meeting_intelligence

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and return (metadata, body)."""
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


def read_meeting_content(meeting_dir: Path) -> tuple[dict, str, str, str]:
    """Read all content files for a meeting.

    Returns (metadata, notes_body, summary_body, transcript_body).
    """
    meta = {}
    notes_body = ""
    summary_body = ""
    transcript_body = ""

    notes_path = meeting_dir / "notes.md"
    if notes_path.exists():
        m, body = parse_frontmatter(notes_path.read_text(encoding="utf-8"))
        meta.update(m)
        notes_body = body

    summary_path = meeting_dir / "summary.md"
    if summary_path.exists():
        m, body = parse_frontmatter(summary_path.read_text(encoding="utf-8"))
        meta.update(m)
        summary_body = body

    transcript_path = meeting_dir / "transcript.md"
    if transcript_path.exists():
        m, body = parse_frontmatter(transcript_path.read_text(encoding="utf-8"))
        meta.update(m)
        transcript_body = body

    return meta, notes_body, summary_body, transcript_body


def write_metadata_md(meeting_dir: Path, meta: dict, intelligence: dict):
    """Write metadata.md with extracted intelligence."""
    now = datetime.now(timezone.utc).isoformat()

    lines = ["---"]
    lines.append(f'granola_id: "{meta.get("granola_id", "")}"')
    lines.append(f'title: "{meta.get("title", "")}"')
    lines.append(f'date: "{meta.get("date", "")}"')
    lines.append('type: "metadata"')
    lines.append(f'processed_at: "{now}"')

    # Tags
    if intelligence["tags"]:
        lines.append("tags:")
        for tag in intelligence["tags"]:
            lines.append(f'  - "{tag}"')

    # Action items
    if intelligence["action_items"]:
        lines.append("action_items:")
        for item in intelligence["action_items"]:
            lines.append(f'  - owner: "{item.get("owner", "Unknown")}"')
            lines.append(f'    task: "{item.get("task", "")}"')
            lines.append(f'    due: {json.dumps(item.get("due"))}')

    # Key decisions
    if intelligence["key_decisions"]:
        lines.append("key_decisions:")
        for decision in intelligence["key_decisions"]:
            lines.append(f'  - "{decision}"')

    # People
    if intelligence["people_mentioned"]:
        lines.append("people_mentioned:")
        for person in intelligence["people_mentioned"]:
            lines.append(f'  - "{person}"')

    # Topics
    if intelligence["topics"]:
        lines.append("topics:")
        for topic in intelligence["topics"]:
            lines.append(f'  - "{topic}"')

    lines.append("---")
    lines.append("")

    title = meta.get("title", "Unknown")
    lines.append(f"# Meeting Intelligence: {title}")
    lines.append("")

    # Action items section
    lines.append("## Action Items")
    if intelligence["action_items"]:
        for item in intelligence["action_items"]:
            owner = item.get("owner", "Unknown")
            task = item.get("task", "")
            lines.append(f"- [ ] **{owner}**: {task}")
    else:
        lines.append("*No action items identified.*")
    lines.append("")

    # Key decisions
    lines.append("## Key Decisions")
    if intelligence["key_decisions"]:
        for decision in intelligence["key_decisions"]:
            lines.append(f"- {decision}")
    else:
        lines.append("*No key decisions identified.*")
    lines.append("")

    # Tags
    lines.append("## Tags")
    if intelligence["tags"]:
        lines.append(" ".join(f"`{tag}`" for tag in intelligence["tags"]))
    else:
        lines.append("*No tags.*")
    lines.append("")

    (meeting_dir / "metadata.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Process meetings with Claude API")
    parser.add_argument("--limit", type=int, help="Max meetings to process")
    parser.add_argument("--since", type=str, help="Only process meetings after this date")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    parser.add_argument("--reprocess", action="store_true",
                        help="Re-process meetings that already have metadata.md")
    parser.add_argument("--model", default="claude-sonnet-4-20250514",
                        help="Claude model to use")
    args = parser.parse_args()

    if not MEETINGS_DIR.exists():
        log.error("No meetings/ directory. Run export first.")
        sys.exit(1)

    # Find all meeting directories
    meeting_dirs = sorted(MEETINGS_DIR.glob("*/*/*/"))
    log.info("Found %d meeting directories", len(meeting_dirs))

    # Filter already processed (unless --reprocess)
    if not args.reprocess:
        meeting_dirs = [d for d in meeting_dirs if not (d / "metadata.md").exists()]
        log.info("After filtering already-processed: %d remaining", len(meeting_dirs))

    # Filter by date
    if args.since:
        meeting_dirs = [d for d in meeting_dirs
                        if d.name[:10] >= args.since]
        log.info("After date filter (>= %s): %d", args.since, len(meeting_dirs))

    # Apply limit
    if args.limit:
        meeting_dirs = meeting_dirs[:args.limit]

    if args.dry_run:
        print(f"\nWould process {len(meeting_dirs)} meetings:")
        for d in meeting_dirs:
            print(f"  {d.name}")
        return

    log.info("Processing %d meetings with Claude API (%s)...", len(meeting_dirs), args.model)

    success = 0
    errors = 0

    for i, meeting_dir in enumerate(meeting_dirs):
        log.info("[%d/%d] %s", i + 1, len(meeting_dirs), meeting_dir.name)

        meta, notes, summary, transcript = read_meeting_content(meeting_dir)
        title = meta.get("title", meeting_dir.name)

        # Need at least summary or transcript
        if not summary and not transcript:
            log.warning("  Skipping: no summary or transcript")
            continue

        try:
            intelligence = extract_meeting_intelligence(
                title=title,
                summary_text=summary,
                transcript_text=transcript,
                model=args.model,
            )
            write_metadata_md(meeting_dir, meta, intelligence)
            tags = ", ".join(intelligence.get("tags", []))
            items = len(intelligence.get("action_items", []))
            log.info("  ✓ %d action items, tags: [%s]", items, tags)
            success += 1

        except Exception as e:
            log.error("  ✗ Error: %s", e)
            errors += 1

    log.info("=" * 60)
    log.info("Processing complete! Success: %d, Errors: %d", success, errors)


if __name__ == "__main__":
    main()
