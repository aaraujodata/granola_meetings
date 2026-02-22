"use client";

import { useEffect, useRef } from "react";
import type { LogEntry } from "@/types";

const levelColors: Record<string, string> = {
  ERROR: "text-red-400",
  WARNING: "text-yellow-400",
  INFO: "text-green-400",
  DEBUG: "text-gray-500",
};

interface LogViewerProps {
  logs: LogEntry[];
  isStreaming: boolean;
  isTerminal: boolean;
}

export default function LogViewer({ logs, isStreaming, isTerminal }: LogViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const shouldAutoScroll = useRef(true);

  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    shouldAutoScroll.current = atBottom;
  };

  useEffect(() => {
    const el = containerRef.current;
    if (el && shouldAutoScroll.current) {
      el.scrollTop = el.scrollHeight;
    }
  }, [logs.length]);

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="max-h-72 overflow-y-auto rounded-lg bg-gray-900 p-3 font-mono text-xs leading-relaxed"
    >
      {logs.length === 0 && !isTerminal && (
        <span className="text-gray-500">Waiting for logs...</span>
      )}
      {logs.length === 0 && isTerminal && (
        <span className="text-gray-500">No logs available for this job.</span>
      )}
      {logs.map((entry, i) => {
        const color = levelColors[entry.level] ?? "text-gray-300";
        const ts = entry.timestamp.slice(11, 19);
        return (
          <div key={i} className="whitespace-pre-wrap">
            <span className="text-gray-600">{ts}</span>{" "}
            <span className={color}>[{entry.level.padEnd(7)}]</span>{" "}
            <span className="text-gray-100">{entry.message}</span>
          </div>
        );
      })}
      {isTerminal && logs.length > 0 && (
        <div className="mt-1 text-gray-500">--- Job complete ---</div>
      )}
      {isStreaming && (
        <div className="mt-1 animate-pulse text-gray-500">...</div>
      )}
    </div>
  );
}
