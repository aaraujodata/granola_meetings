import type {
  MeetingsListResponse,
  MeetingDetail,
  SearchResult,
  JobResponse,
  JobLogsResponse,
  StatusResponse,
  PipelineAction,
  PipelineParams,
} from "@/types";

const BASE = "/api";

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export function getMeetings(
  offset = 0,
  limit = 50,
  dateFrom?: string,
  dateTo?: string
): Promise<MeetingsListResponse> {
  const params = new URLSearchParams({
    offset: String(offset),
    limit: String(limit),
  });
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  return fetchJSON(`${BASE}/meetings?${params}`);
}

export function getMeeting(id: string): Promise<MeetingDetail> {
  return fetchJSON(`${BASE}/meetings/${encodeURIComponent(id)}`);
}

export function search(
  query: string,
  type?: string,
  dateFrom?: string,
  dateTo?: string,
  limit = 20
): Promise<SearchResult[]> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  if (type) params.set("type", type);
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  return fetchJSON(`${BASE}/search?${params}`);
}

export function triggerPipeline(action: PipelineAction, params?: PipelineParams): Promise<JobResponse> {
  const init: RequestInit = { method: "POST" };
  if (params) {
    init.headers = { "Content-Type": "application/json" };
    init.body = JSON.stringify(params);
  }
  return fetchJSON(`${BASE}/pipeline/${action}`, init);
}

export function getJobStatus(jobId: string): Promise<JobResponse> {
  return fetchJSON(`${BASE}/pipeline/jobs/${encodeURIComponent(jobId)}`);
}

export function getJobLogs(jobId: string, after = 0, limit = 200): Promise<JobLogsResponse> {
  return fetchJSON(`${BASE}/pipeline/jobs/${encodeURIComponent(jobId)}/logs?after=${after}&limit=${limit}`);
}

export function getJobs(): Promise<JobResponse[]> {
  return fetchJSON(`${BASE}/pipeline/jobs`);
}

export function getStatus(): Promise<StatusResponse> {
  return fetchJSON(`${BASE}/status`);
}
