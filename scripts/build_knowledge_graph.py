#!/usr/bin/env python3
"""Build a knowledge graph from processed meeting metadata.

Reads all metadata.md files and builds connections:
  people <-> meetings <-> topics <-> action items

Output:
  exports/knowledge_graph.json    — Nodes and edges for visualization
  exports/knowledge_graph_summary.md — Human-readable summary

Usage:
    python scripts/build_knowledge_graph.py
"""

import json
import logging
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import MEETINGS_DIR, EXPORTS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def parse_metadata_frontmatter(text: str) -> dict:
    """Parse the YAML-ish frontmatter from metadata.md files."""
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    fm = match.group(1)
    result = {}
    current_key = None
    current_list = []

    for line in fm.split("\n"):
        if line.startswith("  - "):
            # List item
            value = line.strip().lstrip("- ").strip('"')
            current_list.append(value)
        elif ":" in line and not line.startswith("  "):
            # Save previous list
            if current_key and current_list:
                result[current_key] = current_list
                current_list = []

            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"')
            current_key = key

            if value:
                result[key] = value
                current_key = None
                current_list = []
        elif line.startswith("    "):
            # Sub-field of a list item (action_items nested YAML)
            pass

    if current_key and current_list:
        result[current_key] = current_list

    return result


def build_graph(meetings_dir: Path) -> dict:
    """Build knowledge graph from all metadata.md files.

    Returns dict with 'nodes' and 'edges' arrays.
    """
    nodes = {}
    edges = []
    edge_id = 0

    people_meetings = defaultdict(list)
    tag_meetings = defaultdict(list)
    topic_meetings = defaultdict(list)
    all_action_items = []

    metadata_files = sorted(meetings_dir.glob("*/*/*/metadata.md"))
    log.info("Found %d metadata.md files", len(metadata_files))

    for mf in metadata_files:
        text = mf.read_text(encoding="utf-8")
        meta = parse_metadata_frontmatter(text)

        meeting_id = meta.get("granola_id", mf.parent.name)
        title = meta.get("title", mf.parent.name)
        date = meta.get("date", "")

        # Meeting node
        nodes[meeting_id] = {
            "id": meeting_id,
            "type": "meeting",
            "label": title,
            "date": date,
        }

        # People
        people = meta.get("people_mentioned", [])
        if isinstance(people, str):
            people = [people]
        for person in people:
            person_id = f"person:{person.lower()}"
            if person_id not in nodes:
                nodes[person_id] = {
                    "id": person_id,
                    "type": "person",
                    "label": person,
                }
            edges.append({
                "id": f"e{edge_id}",
                "source": person_id,
                "target": meeting_id,
                "type": "participated_in",
            })
            edge_id += 1
            people_meetings[person].append(meeting_id)

        # Tags
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        for tag in tags:
            tag_id = f"tag:{tag}"
            if tag_id not in nodes:
                nodes[tag_id] = {
                    "id": tag_id,
                    "type": "tag",
                    "label": tag,
                }
            edges.append({
                "id": f"e{edge_id}",
                "source": meeting_id,
                "target": tag_id,
                "type": "tagged_with",
            })
            edge_id += 1
            tag_meetings[tag].append(meeting_id)

        # Topics
        topics = meta.get("topics", [])
        if isinstance(topics, str):
            topics = [topics]
        for topic in topics:
            topic_id = f"topic:{topic.lower()}"
            if topic_id not in nodes:
                nodes[topic_id] = {
                    "id": topic_id,
                    "type": "topic",
                    "label": topic,
                }
            edges.append({
                "id": f"e{edge_id}",
                "source": meeting_id,
                "target": topic_id,
                "type": "discusses",
            })
            edge_id += 1
            topic_meetings[topic].append(meeting_id)

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "stats": {
            "meetings": sum(1 for n in nodes.values() if n["type"] == "meeting"),
            "people": sum(1 for n in nodes.values() if n["type"] == "person"),
            "tags": sum(1 for n in nodes.values() if n["type"] == "tag"),
            "topics": sum(1 for n in nodes.values() if n["type"] == "topic"),
            "edges": len(edges),
        },
        "people_meetings": {k: len(v) for k, v in sorted(people_meetings.items(),
                                                          key=lambda x: -len(x[1]))},
        "tag_frequency": {k: len(v) for k, v in sorted(tag_meetings.items(),
                                                        key=lambda x: -len(x[1]))},
        "topic_frequency": {k: len(v) for k, v in sorted(topic_meetings.items(),
                                                          key=lambda x: -len(x[1]))},
    }


def write_summary_md(graph: dict, output_path: Path):
    """Write a human-readable summary of the knowledge graph."""
    lines = ["# Knowledge Graph Summary", ""]

    stats = graph["stats"]
    lines.append("## Overview")
    lines.append(f"- **Meetings**: {stats['meetings']}")
    lines.append(f"- **People**: {stats['people']}")
    lines.append(f"- **Tags**: {stats['tags']}")
    lines.append(f"- **Topics**: {stats['topics']}")
    lines.append(f"- **Connections**: {stats['edges']}")
    lines.append("")

    lines.append("## Top People (by meeting count)")
    for person, count in list(graph["people_meetings"].items())[:20]:
        lines.append(f"- **{person}**: {count} meetings")
    lines.append("")

    lines.append("## Top Tags")
    for tag, count in list(graph["tag_frequency"].items())[:20]:
        lines.append(f"- `{tag}`: {count} meetings")
    lines.append("")

    lines.append("## Top Topics")
    for topic, count in list(graph["topic_frequency"].items())[:20]:
        lines.append(f"- {topic}: {count} meetings")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    if not MEETINGS_DIR.exists():
        log.error("No meetings/ directory. Run export + process first.")
        sys.exit(1)

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    graph = build_graph(MEETINGS_DIR)

    # Write JSON
    json_path = EXPORTS_DIR / "knowledge_graph.json"
    json_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Wrote %s", json_path)

    # Write summary
    summary_path = EXPORTS_DIR / "knowledge_graph_summary.md"
    write_summary_md(graph, summary_path)
    log.info("Wrote %s", summary_path)

    # Print stats
    stats = graph["stats"]
    log.info("=" * 60)
    log.info("Knowledge graph built!")
    log.info("  Meetings: %d", stats["meetings"])
    log.info("  People: %d", stats["people"])
    log.info("  Tags: %d", stats["tags"])
    log.info("  Topics: %d", stats["topics"])
    log.info("  Connections: %d", stats["edges"])


if __name__ == "__main__":
    main()
