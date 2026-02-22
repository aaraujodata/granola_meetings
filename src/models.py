"""Dataclasses for Granola documents, panels, and transcript entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TranscriptEntry:
    id: str
    document_id: str
    text: str
    source: str  # "microphone" (user) or "system" (others)
    start_timestamp: str
    end_timestamp: str
    is_final: bool = True

    @classmethod
    def from_api(cls, data: dict) -> "TranscriptEntry":
        return cls(
            id=data["id"],
            document_id=data["document_id"],
            text=data.get("text", ""),
            source=data.get("source", "unknown"),
            start_timestamp=data.get("start_timestamp", ""),
            end_timestamp=data.get("end_timestamp", ""),
            is_final=data.get("is_final", True),
        )

    @property
    def speaker_label(self) -> str:
        return "You" if self.source == "microphone" else "Other"


@dataclass
class Panel:
    id: str
    document_id: str
    title: str
    template_slug: str
    original_content: str  # HTML
    content: dict | None = None  # ProseMirror JSON
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_api(cls, data: dict) -> "Panel":
        return cls(
            id=data["id"],
            document_id=data["document_id"],
            title=data.get("title", "Summary"),
            template_slug=data.get("template_slug", ""),
            original_content=data.get("original_content", ""),
            content=data.get("content"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


@dataclass
class GranolaDocument:
    id: str
    title: str
    created_at: str
    updated_at: str
    notes_markdown: str = ""
    notes_plain: str = ""
    notes: dict | None = None  # ProseMirror JSON
    people: dict | None = None
    google_calendar_event: dict | None = None
    workspace_id: str = ""
    type: str = "meeting"
    transcribe: bool = False
    deleted_at: str | None = None

    @classmethod
    def from_api(cls, data: dict) -> "GranolaDocument":
        return cls(
            id=data["id"],
            title=data.get("title") or "Untitled",
            created_at=data.get("created_at") or "",
            updated_at=data.get("updated_at") or "",
            notes_markdown=data.get("notes_markdown", "") or "",
            notes_plain=data.get("notes_plain", "") or "",
            notes=data.get("notes"),
            people=data.get("people"),
            google_calendar_event=data.get("google_calendar_event"),
            workspace_id=data.get("workspace_id", ""),
            type=data.get("type", "meeting"),
            transcribe=data.get("transcribe", False),
            deleted_at=data.get("deleted_at"),
        )

    @property
    def date(self) -> str:
        """Return the ISO date portion of created_at (YYYY-MM-DD)."""
        if self.created_at:
            return self.created_at[:10]
        return "unknown-date"

    @property
    def attendees(self) -> list[dict]:
        """Extract attendee list from people field."""
        if not self.people:
            return []
        return self.people.get("attendees", [])

    @property
    def calendar_event_title(self) -> str:
        """Get the calendar event title if available."""
        if self.people:
            return self.people.get("title", "")
        return ""


@dataclass
class Meeting:
    """Composite object combining document + panels + transcript."""
    document: GranolaDocument
    panels: list[Panel] = field(default_factory=list)
    transcript: list[TranscriptEntry] = field(default_factory=list)

    @property
    def has_transcript(self) -> bool:
        return len(self.transcript) > 0

    @property
    def has_summary(self) -> bool:
        return len(self.panels) > 0
