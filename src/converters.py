"""Content conversion utilities: ProseMirror→MD, HTML→MD, transcript formatting."""

import re
from datetime import datetime, timezone


def sanitize_filename(title: str) -> str:
    """Convert a title to a safe, lowercase, hyphenated folder name.

    >>> sanitize_filename("Bank of America metrics duplication")
    'bank-of-america-metrics-duplication'
    """
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug[:80] if slug else "untitled"


def html_to_markdown(html: str) -> str:
    """Convert HTML (from panel original_content) to markdown.

    Handles the common elements found in Granola summaries:
    h1-h6, ul/ol/li, p, strong, em, a, br
    """
    if not html:
        return ""

    try:
        from markdownify import markdownify as md
        result = md(html, heading_style="ATX", bullets="-")
        # Clean up excessive blank lines
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()
    except ImportError:
        return _html_to_markdown_fallback(html)


def _html_to_markdown_fallback(html: str) -> str:
    """Minimal HTML→MD without markdownify dependency."""
    text = html

    # Headings
    for level in range(6, 0, -1):
        prefix = "#" * level
        text = re.sub(rf"<h{level}[^>]*>(.*?)</h{level}>", rf"\n{prefix} \1\n", text, flags=re.DOTALL)

    # Bold and italic
    text = re.sub(r"<strong>(.*?)</strong>", r"**\1**", text, flags=re.DOTALL)
    text = re.sub(r"<b>(.*?)</b>", r"**\1**", text, flags=re.DOTALL)
    text = re.sub(r"<em>(.*?)</em>", r"*\1*", text, flags=re.DOTALL)
    text = re.sub(r"<i>(.*?)</i>", r"*\1*", text, flags=re.DOTALL)

    # Links
    text = re.sub(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.DOTALL)

    # List items
    text = re.sub(r"<li>(.*?)</li>", r"- \1", text, flags=re.DOTALL)

    # Remove remaining tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode HTML entities
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")

    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def prosemirror_to_markdown(doc: dict) -> str:
    """Convert a ProseMirror JSON document to markdown.

    Handles: paragraph, heading, bulletList, orderedList, listItem,
    text (with bold/italic/link marks), hardBreak.
    """
    if not doc or not isinstance(doc, dict):
        return ""

    content = doc.get("content", [])
    return _render_nodes(content, depth=0).strip()


def _render_nodes(nodes: list, depth: int = 0) -> str:
    """Recursively render a list of ProseMirror nodes."""
    parts = []
    for node in nodes:
        parts.append(_render_node(node, depth))
    return "".join(parts)


def _render_node(node: dict, depth: int = 0) -> str:
    """Render a single ProseMirror node to markdown."""
    node_type = node.get("type", "")

    if node_type == "text":
        return _render_text(node)

    if node_type == "paragraph":
        inner = _render_nodes(node.get("content", []), depth)
        return f"{inner}\n\n"

    if node_type == "heading":
        level = node.get("attrs", {}).get("level", 1)
        prefix = "#" * level
        inner = _render_nodes(node.get("content", []), depth)
        return f"{prefix} {inner}\n\n"

    if node_type == "bulletList":
        return _render_list(node, ordered=False, depth=depth)

    if node_type == "orderedList":
        return _render_list(node, ordered=True, depth=depth)

    if node_type == "listItem":
        inner = _render_nodes(node.get("content", []), depth + 1)
        # Remove trailing newlines from the inner content for cleaner list output
        inner = inner.rstrip("\n")
        indent = "  " * depth
        return f"{indent}- {inner}\n"

    if node_type == "hardBreak":
        return "  \n"

    if node_type == "blockquote":
        inner = _render_nodes(node.get("content", []), depth)
        lines = inner.strip().split("\n")
        return "\n".join(f"> {line}" for line in lines) + "\n\n"

    if node_type == "codeBlock":
        inner = _render_nodes(node.get("content", []), depth)
        lang = node.get("attrs", {}).get("language", "")
        return f"```{lang}\n{inner.strip()}\n```\n\n"

    if node_type == "horizontalRule":
        return "---\n\n"

    # Unknown node — recurse into children if any
    if "content" in node:
        return _render_nodes(node["content"], depth)
    return ""


def _render_list(node: dict, ordered: bool, depth: int) -> str:
    """Render a list node (bullet or ordered)."""
    items = node.get("content", [])
    parts = []
    for i, item in enumerate(items):
        if ordered:
            inner = _render_nodes(item.get("content", []), depth + 1)
            inner = inner.rstrip("\n")
            indent = "  " * depth
            parts.append(f"{indent}{i + 1}. {inner}\n")
        else:
            parts.append(_render_node(item, depth))
    result = "".join(parts)
    if depth == 0:
        result += "\n"
    return result


def _render_text(node: dict) -> str:
    """Render a text node with marks (bold, italic, link, code)."""
    text = node.get("text", "")
    marks = node.get("marks", [])

    for mark in marks:
        mark_type = mark.get("type", "")
        if mark_type == "bold":
            text = f"**{text}**"
        elif mark_type == "italic":
            text = f"*{text}*"
        elif mark_type == "code":
            text = f"`{text}`"
        elif mark_type == "link":
            href = mark.get("attrs", {}).get("href", "")
            text = f"[{text}]({href})"

    return text


def format_transcript(entries: list, first_timestamp: str | None = None) -> str:
    """Format transcript entries with relative timestamps and speaker labels.

    Args:
        entries: List of TranscriptEntry dataclass instances or dicts.
        first_timestamp: Override for the base timestamp (ISO 8601).

    Returns:
        Formatted transcript string with **[HH:MM:SS] Speaker:** lines.
    """
    if not entries:
        return ""

    # Determine base timestamp
    first = entries[0]
    if first_timestamp:
        base_ts = first_timestamp
    elif hasattr(first, "start_timestamp"):
        base_ts = first.start_timestamp
    else:
        base_ts = first.get("start_timestamp", "")

    base_dt = _parse_iso(base_ts)

    lines = []
    for entry in entries:
        if hasattr(entry, "start_timestamp"):
            ts = entry.start_timestamp
            text = entry.text
            source = entry.source
        else:
            ts = entry.get("start_timestamp", "")
            text = entry.get("text", "")
            source = entry.get("source", "unknown")

        speaker = "You" if source == "microphone" else "Other"
        relative = _format_relative_time(base_dt, _parse_iso(ts))
        lines.append(f"**[{relative}] {speaker}:** {text}")

    return "\n\n".join(lines)


def _parse_iso(ts: str) -> datetime:
    """Parse an ISO 8601 timestamp string to datetime."""
    if not ts:
        return datetime(2000, 1, 1, tzinfo=timezone.utc)
    # Handle 'Z' suffix and fractional seconds
    ts = ts.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return datetime(2000, 1, 1, tzinfo=timezone.utc)


def _format_relative_time(base: datetime, current: datetime) -> str:
    """Format the time difference as HH:MM:SS."""
    delta = current - base
    total_seconds = max(0, int(delta.total_seconds()))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def calculate_duration_minutes(entries: list) -> int:
    """Calculate meeting duration in minutes from transcript entries."""
    if not entries:
        return 0

    first = entries[0]
    last = entries[-1]

    if hasattr(first, "start_timestamp"):
        start_ts = first.start_timestamp
        end_ts = last.end_timestamp
    else:
        start_ts = first.get("start_timestamp", "")
        end_ts = last.get("end_timestamp", "")

    start = _parse_iso(start_ts)
    end = _parse_iso(end_ts)
    delta = end - start
    return max(0, int(delta.total_seconds() / 60))
