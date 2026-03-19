"use client";

import { useEffect, useState, useMemo } from "react";
import { getMeetings } from "@/lib/api";
import MeetingRow from "@/components/MeetingRow";
import type { MeetingSummary } from "@/types";

const PAGE_SIZE = 50;

function getDayLabel(dateStr: string, createdAt: string): string {
  const now = new Date();
  const meetingDate = createdAt ? new Date(createdAt) : new Date(dateStr);

  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  const meetingDay = new Date(
    meetingDate.getFullYear(),
    meetingDate.getMonth(),
    meetingDate.getDate()
  );

  if (meetingDay.getTime() === today.getTime()) return "Today";
  if (meetingDay.getTime() === yesterday.getTime()) return "Yesterday";

  return meetingDate.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function groupByDay(
  meetings: MeetingSummary[]
): { label: string; meetings: MeetingSummary[] }[] {
  const groups: Map<string, MeetingSummary[]> = new Map();

  for (const m of meetings) {
    const label = getDayLabel(m.date, m.created_at);
    const existing = groups.get(label);
    if (existing) {
      existing.push(m);
    } else {
      groups.set(label, [m]);
    }
  }

  return Array.from(groups.entries()).map(([label, meetings]) => ({
    label,
    meetings,
  }));
}

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMeetings = (newOffset: number) => {
    setLoading(true);
    setError(null);
    getMeetings(
      newOffset,
      PAGE_SIZE,
      dateFrom || undefined,
      dateTo || undefined
    )
      .then((data) => {
        setMeetings(data.meetings);
        setTotal(data.total);
        setOffset(newOffset);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchMeetings(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFilter = () => fetchMeetings(0);
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const dayGroups = useMemo(() => groupByDay(meetings), [meetings]);

  return (
    <div className="mx-auto max-w-2xl">
      <div className="flex items-baseline justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Meetings</h2>
        <span className="text-sm text-gray-400">{total} total</span>
      </div>

      {/* Date filters */}
      <div className="mt-4 flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs text-gray-500">From</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="mt-1 rounded-md border border-gray-300 px-2 py-1 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500">To</label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="mt-1 rounded-md border border-gray-300 px-2 py-1 text-sm"
          />
        </div>
        <button
          onClick={handleFilter}
          className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
        >
          Filter
        </button>
        {(dateFrom || dateTo) && (
          <button
            onClick={() => {
              setDateFrom("");
              setDateTo("");
              setTimeout(() => fetchMeetings(0), 0);
            }}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Clear
          </button>
        )}
      </div>

      {error && (
        <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <p className="mt-8 text-sm text-gray-500">Loading meetings...</p>
      ) : (
        <>
          <div className="mt-6 space-y-2">
            {dayGroups.map((group, i) => (
              <section key={group.label}>
                <div
                  className={`sticky top-0 z-10 flex items-center gap-3 bg-gray-50 py-3 px-3 ${i > 0 ? "mt-2 border-t border-gray-200" : ""}`}
                >
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                    {group.label}
                  </h3>
                  <span className="text-xs text-gray-300">
                    {group.meetings.length}
                  </span>
                </div>
                <div>
                  {group.meetings.map((m) => (
                    <MeetingRow key={m.id} meeting={m} />
                  ))}
                </div>
              </section>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-8 flex items-center justify-between">
              <button
                onClick={() => fetchMeetings(offset - PAGE_SIZE)}
                disabled={offset === 0}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm disabled:opacity-40"
              >
                Previous
              </button>
              <span className="text-sm text-gray-500">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => fetchMeetings(offset + PAGE_SIZE)}
                disabled={offset + PAGE_SIZE >= total}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
