#!/usr/bin/env python3
"""Granola Meeting Data Pipeline — single CLI entrypoint.

Usage:
    python granola_pipeline.py export --all
    python granola_pipeline.py export --since 2026-01-01
    python granola_pipeline.py export --limit 5
    python granola_pipeline.py export --ids <uuid1> <uuid2>

    python granola_pipeline.py index [--rebuild]

    python granola_pipeline.py search "query here"
    python granola_pipeline.py search --type transcript "query"

    python granola_pipeline.py process --all
    python granola_pipeline.py process --limit 5
    python granola_pipeline.py process --since 2026-02-01

    python granola_pipeline.py sync   # export + index + process

    python granola_pipeline.py status  # Show token + database stats
"""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def cmd_export(args):
    """Export meetings to markdown."""
    from src.api_client import GranolaClient
    from src.auth import is_token_valid, get_token_info
    from src.config import MEETINGS_DIR, DB_DIR
    from scripts.export_all import (
        export_meeting, load_progress, save_progress, main as export_main,
    )

    # Build sys.argv for export_all.main()
    export_args = []
    if args.all:
        pass  # No filter
    if args.since:
        export_args.extend(["--since", args.since])
    if args.limit:
        export_args.extend(["--limit", str(args.limit)])
    if args.ids:
        export_args.extend(["--ids"] + args.ids)
    if args.no_resume:
        export_args.append("--no-resume")

    sys.argv = ["export_all.py"] + export_args
    export_main()


def cmd_index(args):
    """Build search index."""
    from scripts.build_index import main as index_main
    sys.argv = ["build_index.py"]
    if args.rebuild:
        sys.argv.append("--rebuild")
    index_main()


def cmd_search(args):
    """Search meetings."""
    from scripts.search import main as search_main

    search_args = [args.query]
    if args.type:
        search_args.extend(["--type", args.type])
    if args.date_from:
        search_args.extend(["--date-from", args.date_from])
    if args.date_to:
        search_args.extend(["--date-to", args.date_to])
    if args.limit:
        search_args.extend(["--limit", str(args.limit)])

    sys.argv = ["search.py"] + search_args
    search_main()


def cmd_process(args):
    """Process meetings with Claude API."""
    from scripts.process_meetings import main as process_main

    process_args = []
    if args.limit:
        process_args.extend(["--limit", str(args.limit)])
    if args.since:
        process_args.extend(["--since", args.since])
    if args.reprocess:
        process_args.append("--reprocess")
    if args.model:
        process_args.extend(["--model", args.model])

    sys.argv = ["process_meetings.py"] + process_args
    process_main()


def cmd_sync(args):
    """Run full pipeline: export + index + process."""
    log.info("=== Phase 1: Export ===")
    from scripts.export_all import main as export_main
    export_sys_args = ["export_all.py"]
    if args.since:
        export_sys_args.extend(["--since", args.since])
    sys.argv = export_sys_args
    export_main()

    log.info("\n=== Phase 2: Build Index ===")
    from scripts.build_index import main as index_main
    sys.argv = ["build_index.py", "--rebuild"]
    index_main()

    if args.skip_process:
        log.info("\nSkipping Claude processing (--skip-process)")
        return

    log.info("\n=== Phase 3: Process with Claude ===")
    from scripts.process_meetings import main as process_main
    process_sys_args = ["process_meetings.py"]
    if args.since:
        process_sys_args.extend(["--since", args.since])
    sys.argv = process_sys_args
    process_main()


def cmd_status(args):
    """Show token and database status."""
    from src.auth import get_token_info, is_token_valid
    from src.config import SEARCH_DB_PATH, MEETINGS_DIR, EXPORT_PROGRESS_PATH

    import json

    print("\n=== Token Status ===")
    try:
        info = get_token_info()
        valid = is_token_valid()
        remaining_min = info["remaining_seconds"] / 60
        print(f"  Valid: {'YES' if valid else 'NO'}")
        print(f"  Token length: {info['token_length']}")
        print(f"  Remaining: {remaining_min:.0f} minutes")
        print(f"  Has refresh token: {info['has_refresh_token']}")
    except Exception as e:
        print(f"  Error reading token: {e}")

    print("\n=== Export Status ===")
    if EXPORT_PROGRESS_PATH.exists():
        data = json.loads(EXPORT_PROGRESS_PATH.read_text())
        print(f"  Exported meetings: {len(data.get('completed', []))}")
    else:
        print("  No exports yet")

    if MEETINGS_DIR.exists():
        dirs = list(MEETINGS_DIR.glob("*/*/*/"))
        print(f"  Meeting directories: {len(dirs)}")
    else:
        print("  meetings/ directory not found")

    print("\n=== Search Index ===")
    if SEARCH_DB_PATH.exists():
        from src.search_db import SearchDB
        db = SearchDB()
        db.initialize()
        stats = db.get_stats()
        db.close()
        for k, v in stats.items():
            print(f"  {k}: {v}")
    else:
        print("  Not built yet")


def main():
    parser = argparse.ArgumentParser(
        description="Granola Meeting Data Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # ── export ─────────────────────────────────────────────────────────
    p_export = subparsers.add_parser("export", help="Export meetings to markdown")
    p_export.add_argument("--all", action="store_true", help="Export all meetings")
    p_export.add_argument("--since", type=str, help="Only meetings after this date")
    p_export.add_argument("--limit", type=int, help="Max meetings to export")
    p_export.add_argument("--ids", nargs="+", help="Specific document IDs")
    p_export.add_argument("--no-resume", action="store_true", help="Ignore saved progress")
    p_export.set_defaults(func=cmd_export)

    # ── index ──────────────────────────────────────────────────────────
    p_index = subparsers.add_parser("index", help="Build search index")
    p_index.add_argument("--rebuild", action="store_true", help="Rebuild from scratch")
    p_index.set_defaults(func=cmd_index)

    # ── search ─────────────────────────────────────────────────────────
    p_search = subparsers.add_parser("search", help="Search meetings")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--type", "-t", choices=["notes", "summary", "transcript"])
    p_search.add_argument("--date-from", help="Start date")
    p_search.add_argument("--date-to", help="End date")
    p_search.add_argument("--limit", "-n", type=int, default=20)
    p_search.set_defaults(func=cmd_search)

    # ── process ────────────────────────────────────────────────────────
    p_process = subparsers.add_parser("process", help="Process meetings with Claude API")
    p_process.add_argument("--all", action="store_true")
    p_process.add_argument("--since", type=str)
    p_process.add_argument("--limit", type=int)
    p_process.add_argument("--reprocess", action="store_true")
    p_process.add_argument("--model", default="claude-sonnet-4-20250514")
    p_process.set_defaults(func=cmd_process)

    # ── sync ───────────────────────────────────────────────────────────
    p_sync = subparsers.add_parser("sync", help="Full pipeline: export + index + process")
    p_sync.add_argument("--since", type=str, help="Only meetings after this date")
    p_sync.add_argument("--skip-process", action="store_true",
                        help="Skip Claude processing step")
    p_sync.set_defaults(func=cmd_sync)

    # ── status ─────────────────────────────────────────────────────────
    p_status = subparsers.add_parser("status", help="Show pipeline status")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
