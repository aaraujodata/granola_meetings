"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getJobStatus, getJobLogs } from "@/lib/api";
import type { JobResponse, LogEntry } from "@/types";

export function useJobPoller(jobId: string | null) {
  const [job, setJob] = useState<JobResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      setError(null);
      return;
    }

    let cancelled = false;

    const poll = async () => {
      try {
        const data = await getJobStatus(jobId);
        if (cancelled) return;
        setJob(data);
        setError(null);

        if (data.status === "completed" || data.status === "failed") {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Polling failed");
        }
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 2000);

    return () => {
      cancelled = true;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [jobId]);

  return { job, error };
}

export function useJobLogPoller(jobId: string | null, jobStatus?: string) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const cursorRef = useRef(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const reset = useCallback(() => {
    setLogs([]);
    cursorRef.current = 0;
    setIsStreaming(false);
  }, []);

  useEffect(() => {
    if (!jobId) {
      reset();
      return;
    }

    setIsStreaming(true);
    let cancelled = false;

    const poll = async () => {
      try {
        const data = await getJobLogs(jobId, cursorRef.current);
        if (cancelled) return;
        if (data.logs.length > 0) {
          cursorRef.current += data.logs.length;
          setLogs((prev) => [...prev, ...data.logs]);
        }
      } catch {
        // Silently ignore polling errors
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 1500);

    return () => {
      cancelled = true;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [jobId, reset]);

  // Stop polling when job reaches terminal status
  useEffect(() => {
    if (jobStatus === "completed" || jobStatus === "failed") {
      // Do one final fetch then stop
      if (jobId) {
        getJobLogs(jobId, cursorRef.current).then((data) => {
          if (data.logs.length > 0) {
            cursorRef.current += data.logs.length;
            setLogs((prev) => [...prev, ...data.logs]);
          }
        }).catch(() => {});
      }
      setIsStreaming(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  }, [jobStatus, jobId]);

  return { logs, isStreaming };
}
