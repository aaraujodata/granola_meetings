"use client";

import type { PipelineAction } from "@/types";

interface PipelineControlsProps {
  onTrigger: (action: PipelineAction) => void;
  disabled?: boolean;
}

const actions: { action: PipelineAction; label: string; description: string }[] = [
  { action: "export", label: "Export All", description: "Fetch meetings from Granola API" },
  { action: "index", label: "Rebuild Index", description: "Rebuild SQLite FTS5 search index" },
  { action: "process", label: "Process with Claude", description: "Extract intelligence with Claude API" },
  { action: "sync", label: "Full Sync", description: "Export + Index + Process sequentially" },
];

export default function PipelineControls({ onTrigger, disabled }: PipelineControlsProps) {
  return (
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
  );
}
