"use client";

import type { JobResponse } from "@/types";

const SYNC_STEPS = ["export", "index", "process"];
const REFRESH_STEPS = ["export", "index"];

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s}s`;
}

interface JobProgressBarProps {
  job: JobResponse;
  elapsed: number;
}

export default function JobProgressBar({ job, elapsed }: JobProgressBarProps) {
  const pct =
    job.items_total && job.items_total > 0
      ? Math.round(((job.items_processed ?? 0) / job.items_total) * 100)
      : null;

  const duration = job.duration_seconds ?? elapsed;
  const steps =
    job.action === "sync" ? SYNC_STEPS :
    job.action === "refresh" ? REFRESH_STEPS :
    null;

  return (
    <div className="space-y-2">
      {/* Items progress bar */}
      {pct !== null && (
        <div>
          <div className="flex items-center justify-between text-xs text-gray-600">
            <span>
              {job.items_processed} / {job.items_total} items
            </span>
            <span>{pct}%</span>
          </div>
          <div className="mt-1 h-2 overflow-hidden rounded-full bg-gray-200">
            <div
              className="h-full rounded-full bg-blue-500 transition-all duration-300"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}

      {/* Step tracker (sync / refresh) */}
      {steps && (
        <div className="flex items-center gap-1 text-xs">
          {steps.map((step, i) => {
            const isCompleted = job.steps_completed?.includes(step);
            const isCurrent = job.current_step === step;
            let className =
              "rounded-full px-2.5 py-0.5 font-medium transition-colors";
            if (isCompleted) {
              className += " bg-green-100 text-green-800";
            } else if (isCurrent) {
              className += " bg-blue-100 text-blue-800 animate-pulse";
            } else {
              className += " bg-gray-100 text-gray-400";
            }
            return (
              <span key={step}>
                {i > 0 && <span className="mr-1 text-gray-300">&rarr;</span>}
                <span className={className}>{step}</span>
              </span>
            );
          })}
        </div>
      )}

      {/* Duration */}
      <div className="text-xs text-gray-500">
        {job.status === "running" || job.status === "queued"
          ? `Elapsed: ${formatDuration(duration)}`
          : `Duration: ${formatDuration(duration)}`}
        {job.error_count > 0 && (
          <span className="ml-2 text-red-500">
            {job.error_count} error{job.error_count > 1 ? "s" : ""}
          </span>
        )}
      </div>
    </div>
  );
}
