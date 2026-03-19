import Link from "next/link";
import type { MeetingSummary } from "@/types";

function formatTime(isoString: string): string {
  if (!isoString) return "";
  try {
    const d = new Date(isoString);
    return d
      .toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      })
      .toUpperCase();
  } catch {
    return "";
  }
}

function DocumentIcon() {
  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gray-100 text-gray-400">
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>
    </div>
  );
}

export default function MeetingRow({ meeting }: { meeting: MeetingSummary }) {
  const time = formatTime(meeting.created_at);

  return (
    <Link
      href={`/meetings/${encodeURIComponent(meeting.id)}`}
      className="flex items-center gap-3 rounded-lg px-3 py-3 transition hover:bg-gray-50"
    >
      <DocumentIcon />
      <div className="min-w-0 flex-1">
        <h3 className="truncate text-sm font-semibold text-gray-900">
          {meeting.title}
        </h3>
        <p className="text-xs text-gray-400">Me</p>
      </div>
      {time && (
        <span className="shrink-0 text-xs text-gray-400">{time}</span>
      )}
    </Link>
  );
}
