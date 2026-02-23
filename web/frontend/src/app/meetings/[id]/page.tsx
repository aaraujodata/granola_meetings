"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getMeeting } from "@/lib/api";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import TranscriptViewer from "@/components/TranscriptViewer";
import type { MeetingDetail } from "@/types";

type Tab = "notes" | "summary" | "transcript";

export default function MeetingDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [meeting, setMeeting] = useState<MeetingDetail | null>(null);
  const [tab, setTab] = useState<Tab>("summary");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMeeting(id)
      .then((data) => {
        setMeeting(data);
        // Pick first available tab
        if (data.has_summary) setTab("summary");
        else if (data.has_notes) setTab("notes");
        else if (data.has_transcript) setTab("transcript");
      })
      .catch((err) => setError(err.message));
  }, [id]);

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (!meeting) {
    return <p className="text-sm text-gray-500">Loading meeting...</p>;
  }

  const tabs: { key: Tab; label: string; available: boolean }[] = [
    { key: "notes", label: "Notes", available: meeting.has_notes },
    { key: "summary", label: "Summary", available: meeting.has_summary },
    { key: "transcript", label: "Transcript", available: meeting.has_transcript },
  ];

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{meeting.title}</h2>
        <p className="mt-1 text-sm text-gray-500">{meeting.date}</p>
        {meeting.attendees.length > 0 && (
          <p className="mt-1 text-xs text-gray-400">
            Attendees: {meeting.attendees.join(", ")}
          </p>
        )}
        {meeting.calendar_event && (
          <p className="mt-1 text-xs text-gray-400">
            Calendar: {meeting.calendar_event}
          </p>
        )}
      </div>

      {/* Tab bar */}
      <div className="border-b border-gray-200">
        <div className="flex gap-4">
          {tabs.map(({ key, label, available }) => (
            <button
              key={key}
              onClick={() => available && setTab(key)}
              disabled={!available}
              className={`border-b-2 px-1 pb-2 text-sm font-medium transition ${
                tab === key
                  ? "border-blue-600 text-blue-600"
                  : available
                    ? "border-transparent text-gray-500 hover:text-gray-700"
                    : "border-transparent text-gray-300 cursor-not-allowed"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="mt-6">
        {tab === "notes" && (
          <MarkdownRenderer content={meeting.notes_content} />
        )}
        {tab === "summary" && (
          <MarkdownRenderer content={meeting.summary_content} />
        )}
        {tab === "transcript" && (
          <TranscriptViewer content={meeting.transcript_content} />
        )}
      </div>
    </div>
  );
}
