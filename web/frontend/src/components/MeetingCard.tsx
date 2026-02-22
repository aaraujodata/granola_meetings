import Link from "next/link";
import type { MeetingSummary } from "@/types";

function Badge({ label, active }: { label: string; active: boolean }) {
  return (
    <span
      className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${
        active
          ? "bg-blue-100 text-blue-700"
          : "bg-gray-100 text-gray-400"
      }`}
    >
      {label}
    </span>
  );
}

export default function MeetingCard({ meeting }: { meeting: MeetingSummary }) {
  return (
    <Link
      href={`/meetings/${encodeURIComponent(meeting.id)}`}
      className="block rounded-lg border border-gray-200 bg-white p-4 transition hover:border-blue-300 hover:shadow-sm"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold text-gray-900">
            {meeting.title}
          </h3>
          <p className="mt-1 text-xs text-gray-500">{meeting.date}</p>
        </div>
      </div>
      <div className="mt-3 flex gap-2">
        <Badge label="Notes" active={meeting.has_notes} />
        <Badge label="Summary" active={meeting.has_summary} />
        <Badge label="Transcript" active={meeting.has_transcript} />
      </div>
    </Link>
  );
}
