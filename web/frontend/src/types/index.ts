export interface MeetingSummary {
  id: string;
  title: string;
  date: string;
  has_notes: boolean;
  has_summary: boolean;
  has_transcript: boolean;
}

export interface MeetingsListResponse {
  meetings: MeetingSummary[];
  total: number;
  offset: number;
  limit: number;
}

export interface MeetingDetail {
  id: string;
  title: string;
  date: string;
  has_notes: boolean;
  has_summary: boolean;
  has_transcript: boolean;
  notes_content: string;
  summary_content: string;
  transcript_content: string;
  attendees: string[];
  created_at: string;
  updated_at: string;
  calendar_event: string;
}

export interface SearchResult {
  meeting_id: string;
  title: string;
  content_type: string;
  date: string;
  snippet: string;
}

export type PipelineAction = "export" | "index" | "process" | "sync" | "refresh";
export type JobStatusType = "queued" | "running" | "completed" | "failed";

export interface PipelineParams {
  since?: string;
  limit?: number;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  logger: string;
}

export interface JobLogsResponse {
  logs: LogEntry[];
  total: number;
  has_more: boolean;
}

export interface JobResponse {
  job_id: string;
  status: JobStatusType;
  action: string;
  created_at: string;
  result: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  items_processed: number | null;
  items_total: number | null;
  error_count: number;
  current_step: string | null;
  steps_completed: string[];
  params: Record<string, string | number> | null;
}

export interface StatusResponse {
  token_valid: boolean;
  token_remaining_seconds: number;
  db_stats: Record<string, number>;
  export_count: number;
}
