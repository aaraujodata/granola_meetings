"""SQLite FTS5 search index for Granola meeting data."""

import logging
import sqlite3

from .config import SEARCH_DB_PATH, DB_DIR

log = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY,
    title TEXT,
    date TEXT,
    created_at TEXT,
    updated_at TEXT,
    attendees TEXT,
    calendar_event TEXT,
    workspace_id TEXT
);

CREATE TABLE IF NOT EXISTS notes (
    meeting_id TEXT REFERENCES meetings(id),
    content TEXT
);

CREATE TABLE IF NOT EXISTS summaries (
    meeting_id TEXT REFERENCES meetings(id),
    panel_id TEXT,
    template_slug TEXT,
    content TEXT
);

CREATE TABLE IF NOT EXISTS transcripts (
    meeting_id TEXT REFERENCES meetings(id),
    speaker TEXT,
    start_time TEXT,
    end_time TEXT,
    text TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
    meeting_id,
    title,
    content_type,
    content,
    tokenize='porter unicode61'
);
"""


class SearchDB:
    """Manages the SQLite FTS5 search database."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or str(SEARCH_DB_PATH)
        self._conn = None

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            DB_DIR.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def initialize(self):
        """Create all tables and the FTS5 index."""
        conn = self._connect()
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        log.info("Database initialized at %s", self.db_path)

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── Insert methods ─────────────────────────────────────────────────

    def upsert_meeting(self, meeting_id: str, title: str, date: str,
                       created_at: str, updated_at: str,
                       attendees: str = "", calendar_event: str = "",
                       workspace_id: str = ""):
        conn = self._connect()
        conn.execute("""
            INSERT OR REPLACE INTO meetings
                (id, title, date, created_at, updated_at, attendees, calendar_event, workspace_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (meeting_id, title, date, created_at, updated_at,
              attendees, calendar_event, workspace_id))

    def insert_notes(self, meeting_id: str, content: str):
        conn = self._connect()
        conn.execute("DELETE FROM notes WHERE meeting_id = ?", (meeting_id,))
        conn.execute("INSERT INTO notes (meeting_id, content) VALUES (?, ?)",
                      (meeting_id, content))

    def insert_summary(self, meeting_id: str, panel_id: str,
                       template_slug: str, content: str):
        conn = self._connect()
        conn.execute("DELETE FROM summaries WHERE meeting_id = ?", (meeting_id,))
        conn.execute("""
            INSERT INTO summaries (meeting_id, panel_id, template_slug, content)
            VALUES (?, ?, ?, ?)
        """, (meeting_id, panel_id, template_slug, content))

    def insert_transcript_entries(self, meeting_id: str,
                                  entries: list[tuple[str, str, str, str]]):
        """Insert transcript entries: list of (speaker, start_time, end_time, text)."""
        conn = self._connect()
        conn.execute("DELETE FROM transcripts WHERE meeting_id = ?", (meeting_id,))
        conn.executemany("""
            INSERT INTO transcripts (meeting_id, speaker, start_time, end_time, text)
            VALUES (?, ?, ?, ?, ?)
        """, [(meeting_id, *e) for e in entries])

    def index_content(self, meeting_id: str, title: str,
                      content_type: str, content: str):
        """Add content to the FTS5 search index."""
        conn = self._connect()
        # Remove old index entries for this meeting + type
        conn.execute("""
            DELETE FROM search_index
            WHERE meeting_id = ? AND content_type = ?
        """, (meeting_id, content_type))
        conn.execute("""
            INSERT INTO search_index (meeting_id, title, content_type, content)
            VALUES (?, ?, ?, ?)
        """, (meeting_id, title, content_type, content))

    def commit(self):
        if self._conn:
            self._conn.commit()

    # ── Search methods ─────────────────────────────────────────────────

    def search(self, query: str, content_type: str | None = None,
               date_from: str | None = None, date_to: str | None = None,
               limit: int = 20) -> list[dict]:
        """Full-text search across all meeting content.

        Args:
            query: FTS5 search query (supports AND, OR, NOT, phrases).
            content_type: Filter by 'notes', 'summary', or 'transcript'.
            date_from: ISO date lower bound.
            date_to: ISO date upper bound.
            limit: Max results.

        Returns list of dicts with meeting_id, title, content_type, snippet.
        """
        conn = self._connect()

        where_clauses = ["search_index MATCH ?"]
        params: list = [query]

        if content_type:
            where_clauses.append("s.content_type = ?")
            params.append(content_type)

        if date_from:
            where_clauses.append("m.date >= ?")
            params.append(date_from)

        if date_to:
            where_clauses.append("m.date <= ?")
            params.append(date_to)

        params.append(limit)

        where = " AND ".join(where_clauses)

        sql = f"""
            SELECT
                s.meeting_id,
                s.title,
                s.content_type,
                m.date,
                snippet(search_index, 3, '**', '**', '...', 40) as snippet,
                rank
            FROM search_index s
            JOIN meetings m ON m.id = s.meeting_id
            WHERE {where}
            ORDER BY rank
            LIMIT ?
        """

        cursor = conn.execute(sql, params)
        results = []
        for row in cursor:
            results.append({
                "meeting_id": row["meeting_id"],
                "title": row["title"],
                "content_type": row["content_type"],
                "date": row["date"],
                "snippet": row["snippet"],
            })
        return results

    def get_stats(self) -> dict:
        """Return index statistics."""
        conn = self._connect()
        stats = {}
        for table in ["meetings", "notes", "summaries", "transcripts"]:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        cursor = conn.execute("SELECT COUNT(*) FROM search_index")
        stats["search_index"] = cursor.fetchone()[0]
        return stats
