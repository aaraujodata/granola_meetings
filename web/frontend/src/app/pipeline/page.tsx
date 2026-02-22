"use client";

import { useEffect, useRef, useState } from "react";
import { triggerPipeline, getJobs, getJobLogs } from "@/lib/api";
import { useJobPoller, useJobLogPoller } from "@/hooks/useJobPoller";
import PipelineControls from "@/components/PipelineControls";
import JobStatusBadge from "@/components/JobStatusBadge";
import JobProgressBar from "@/components/JobProgressBar";
import LogViewer from "@/components/LogViewer";
import type { PipelineAction, JobResponse, LogEntry } from "@/types";

function useElapsed(startedAt: string | null | undefined, isActive: boolean) {
  const [elapsed, setElapsed] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!isActive || !startedAt) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }
    const start = new Date(startedAt).getTime();
    const tick = () => setElapsed((Date.now() - start) / 1000);
    tick();
    intervalRef.current = setInterval(tick, 1000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [startedAt, isActive]);

  return elapsed;
}

export default function PipelinePage() {
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [recentJobs, setRecentJobs] = useState<JobResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showLogs, setShowLogs] = useState(true);
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);
  const [expandedLogs, setExpandedLogs] = useState<LogEntry[]>([]);

  const { job: polledJob } = useJobPoller(activeJobId);
  const { logs, isStreaming } = useJobLogPoller(activeJobId, polledJob?.status);

  const isActive = polledJob?.status === "running" || polledJob?.status === "queued";
  const elapsed = useElapsed(polledJob?.started_at, isActive);

  const fetchJobs = () => {
    getJobs()
      .then(setRecentJobs)
      .catch(() => {});
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  useEffect(() => {
    if (polledJob && (polledJob.status === "completed" || polledJob.status === "failed")) {
      setActiveJobId(null);
      fetchJobs();
    }
  }, [polledJob]);

  const handleTrigger = async (action: PipelineAction) => {
    setError(null);
    setShowLogs(true);
    setExpandedJobId(null);
    try {
      const job = await triggerPipeline(action);
      setActiveJobId(job.job_id);
      fetchJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to trigger job");
    }
  };

  const handleExpandJob = async (jobId: string) => {
    if (expandedJobId === jobId) {
      setExpandedJobId(null);
      setExpandedLogs([]);
      return;
    }
    setExpandedJobId(jobId);
    try {
      const data = await getJobLogs(jobId, 0, 1000);
      setExpandedLogs(data.logs);
    } catch {
      setExpandedLogs([]);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900">Pipeline</h2>
      <p className="mt-1 mb-6 text-sm text-gray-500">
        Trigger pipeline jobs and monitor progress
      </p>

      <PipelineControls onTrigger={handleTrigger} disabled={isActive} />

      {error && (
        <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Active job */}
      {polledJob && (
        <div className="mt-6 rounded-lg border border-blue-200 bg-blue-50 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-900">
                Active: {polledJob.action}
              </span>
              <JobStatusBadge status={polledJob.status} />
            </div>
            <button
              onClick={() => setShowLogs((v) => !v)}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              {showLogs ? "Hide Logs" : "Show Logs"}
            </button>
          </div>

          {polledJob.result && (
            <p className="text-sm text-gray-600">{polledJob.result}</p>
          )}

          <JobProgressBar job={polledJob} elapsed={elapsed} />

          {showLogs && (
            <LogViewer
              logs={logs}
              isStreaming={isStreaming}
              isTerminal={polledJob.status === "completed" || polledJob.status === "failed"}
            />
          )}
        </div>
      )}

      {/* Recent jobs */}
      <div className="mt-8">
        <h3 className="text-lg font-semibold text-gray-900">Recent Jobs</h3>
        {recentJobs.length === 0 ? (
          <p className="mt-2 text-sm text-gray-500">No jobs yet.</p>
        ) : (
          <div className="mt-3 space-y-2">
            {recentJobs.map((job) => (
              <div key={job.job_id}>
                <button
                  onClick={() => handleExpandJob(job.job_id)}
                  className="flex w-full items-center justify-between rounded-lg border border-gray-200 bg-white p-3 text-left hover:border-gray-300 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div>
                      <span className="text-sm font-medium text-gray-900">
                        {job.action}
                      </span>
                      <span className="ml-2 text-xs text-gray-400">
                        {new Date(job.created_at).toLocaleString()}
                      </span>
                    </div>
                    {job.duration_seconds != null && (
                      <span className="text-xs text-gray-400">
                        {Math.round(job.duration_seconds)}s
                      </span>
                    )}
                    {job.items_total != null && job.items_total > 0 && (
                      <span className="text-xs text-gray-400">
                        {job.items_processed}/{job.items_total} items
                      </span>
                    )}
                    {job.error_count > 0 && (
                      <span className="text-xs text-red-500">
                        {job.error_count} error{job.error_count > 1 ? "s" : ""}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <JobStatusBadge status={job.status} />
                    <span className="text-xs text-gray-400">
                      {expandedJobId === job.job_id ? "▲" : "▼"}
                    </span>
                  </div>
                </button>
                {expandedJobId === job.job_id && (
                  <div className="mt-1 ml-2">
                    <LogViewer
                      logs={expandedLogs}
                      isStreaming={false}
                      isTerminal={true}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
