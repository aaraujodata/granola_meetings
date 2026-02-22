#!/usr/bin/env python3
"""CLI search tool for the Granola meeting search index.

Usage:
    python scripts/search.py "bank of america duplication"
    python scripts/search.py --type transcript "data pipeline"
    python scripts/search.py --date-from 2026-01-01 --date-to 2026-02-28 "sprint review"
    python scripts/search.py --limit 5 "budget"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import SEARCH_DB_PATH
from src.search_db import SearchDB


def main():
    parser = argparse.ArgumentParser(description="Search Granola meetings")
    parser.add_argument("query", help="Search query (FTS5 syntax: AND, OR, NOT, \"phrases\")")
    parser.add_argument("--type", "-t", choices=["notes", "summary", "transcript"],
                        help="Filter by content type")
    parser.add_argument("--date-from", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--date-to", help="End date (YYYY-MM-DD)")
    parser.add_argument("--limit", "-n", type=int, default=20, help="Max results (default: 20)")
    args = parser.parse_args()

    if not SEARCH_DB_PATH.exists():
        print("Error: Search database not found. Run 'python scripts/build_index.py' first.",
              file=sys.stderr)
        sys.exit(1)

    db = SearchDB()
    db.initialize()

    results = db.search(
        query=args.query,
        content_type=args.type,
        date_from=args.date_from,
        date_to=args.date_to,
        limit=args.limit,
    )

    if not results:
        print(f"No results found for: {args.query}")
        sys.exit(0)

    print(f"\n{'='*70}")
    print(f"  {len(results)} result(s) for: {args.query}")
    print(f"{'='*70}\n")

    for i, r in enumerate(results, 1):
        print(f"  {i}. [{r['content_type'].upper()}] {r['title']}")
        print(f"     Date: {r['date']}  |  ID: {r['meeting_id'][:8]}...")
        print(f"     {r['snippet']}")
        print()

    db.close()


if __name__ == "__main__":
    main()
