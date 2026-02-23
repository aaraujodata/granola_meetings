"use client";

import { useState } from "react";
import type { PipelineAction, PipelineParams } from "@/types";

interface PipelineControlsProps {
  onTrigger: (action: PipelineAction, params?: PipelineParams) => void;
  disabled?: boolean;
}

const actions: { action: PipelineAction; label: string; description: string }[] = [
  { action: "export", label: "Export All", description: "Fetch meetings from Granola API" },
  { action: "index", label: "Rebuild Index", description: "Rebuild SQLite FTS5 search index" },
  { action: "process", label: "Process with Claude", description: "Extract intelligence with Claude API" },
  { action: "sync", label: "Full Sync", description: "Export + Index + Process sequentially" },
];

function daysAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

const presets = [
  { label: "Today", days: 0 },
  { label: "Last 3 days", days: 3 },
  { label: "Last 7 days", days: 7 },
  { label: "Last 14 days", days: 14 },
];

export default function PipelineControls({ onTrigger, disabled }: PipelineControlsProps) {
  const [since, setSince] = useState("");
  const [limit, setLimit] = useState<string>("");

  const handleRefresh = () => {
    if (!since) return;
    const params: PipelineParams = { since };
    if (limit && Number(limit) > 0) {
      params.limit = Number(limit);
    }
    onTrigger("refresh", params);
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-2">
        {actions.map(({ action, label, description }) => (
          <button
            key={action}
            onClick={() => onTrigger(action)}
            disabled={disabled}
            className="rounded-lg border border-gray-200 bg-white p-4 text-left transition hover:border-blue-300 hover:shadow-sm disabled:cursor-not-allowed disabled:opacity-50"
          >
            <div className="text-sm font-semibold text-gray-900">{label}</div>
            <div className="mt-1 text-xs text-gray-500">{description}</div>
          </button>
        ))}
      </div>

      {/* Refresh Recent section */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="text-sm font-semibold text-gray-900">Refresh Recent</div>
        <p className="mt-1 text-xs text-gray-500">
          Export meetings from a specific date and rebuild the search index
        </p>

        <div className="mt-3 flex flex-wrap gap-2">
          {presets.map(({ label, days }) => (
            <button
              key={label}
              onClick={() => setSince(daysAgo(days))}
              className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                since === daysAgo(days)
                  ? "bg-blue-100 text-blue-800"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="mt-3 flex items-end gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-600">Since date</label>
            <input
              type="date"
              value={since}
              onChange={(e) => setSince(e.target.value)}
              className="mt-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600">
              Limit <span className="text-gray-400">(optional)</span>
            </label>
            <input
              type="number"
              min="1"
              value={limit}
              onChange={(e) => setLimit(e.target.value)}
              placeholder="all"
              className="mt-1 w-20 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            />
          </div>
          <button
            onClick={handleRefresh}
            disabled={disabled || !since}
            className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Refresh
          </button>
        </div>
      </div>
    </div>
  );
}
