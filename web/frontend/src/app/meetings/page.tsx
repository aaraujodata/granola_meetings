"use client";

import { useEffect, useState } from "react";
import { getMeetings } from "@/lib/api";
import MeetingCard from "@/components/MeetingCard";
import type { MeetingSummary } from "@/types";

const PAGE_SIZE = 50;

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

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900">Meetings</h2>
      <p className="mt-1 text-sm text-gray-500">
        {total} meetings total
      </p>

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
          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {meetings.map((m) => (
              <MeetingCard key={m.id} meeting={m} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-between">
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
