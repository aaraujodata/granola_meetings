"""Pydantic models for all API request/response types."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MeetingSummary(BaseModel):
    id: str
    title: str
    date: str
    has_notes: bool = False
    has_summary: bool = False
    has_transcript: bool = False


class MeetingDetail(BaseModel):
    id: str
    title: str
    date: str
    has_notes: bool = False
    has_summary: bool = False
    has_transcript: bool = False
    notes_content: str = ""
    summary_content: str = ""
    transcript_content: str = ""
    attendees: list[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    calendar_event: str = ""


class MeetingsListResponse(BaseModel):
    meetings: list[MeetingSummary]
    total: int
    offset: int
    limit: int


class SearchResult(BaseModel):
    meeting_id: str
    title: str
    content_type: str
    date: str
    snippet: str


class SearchParams(BaseModel):
    query: str
    content_type: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    limit: int = 20


class PipelineAction(str, Enum):
    export = "export"
    index = "index"
    process = "process"
    sync = "sync"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    logger: str


class JobLogsResponse(BaseModel):
    logs: list[LogEntry]
    total: int
    has_more: bool


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    action: str
    created_at: str = ""
    result: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    duration_seconds: float | None = None
    items_processed: int | None = None
    items_total: int | None = None
    error_count: int = 0
    current_step: str | None = None
    steps_completed: list[str] = Field(default_factory=list)


class StatusResponse(BaseModel):
    token_valid: bool
    token_remaining_seconds: float
    db_stats: dict
    export_count: int
