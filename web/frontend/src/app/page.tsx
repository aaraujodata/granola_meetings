"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getStatus } from "@/lib/api";
import type { StatusResponse } from "@/types";

export default function DashboardPage() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStatus()
      .then(setStatus)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
      <p className="mt-1 text-sm text-gray-500">
        Overview of your Granola meeting data
      </p>

      {error && (
        <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
          Failed to load status: {error}
        </div>
      )}

      {status && (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Meetings"
            value={status.db_stats.meetings ?? 0}
          />
          <StatCard
            label="Search Entries"
            value={status.db_stats.search_index ?? 0}
          />
          <StatCard
            label="Exported"
            value={status.export_count}
          />
          <StatCard
            label="Token"
            value={status.token_valid ? "Valid" : "Expired"}
            sub={
              status.token_valid
                ? `${Math.round(status.token_remaining_seconds / 60)}m remaining`
                : "Open Granola to refresh"
            }
          />
        </div>
      )}

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <QuickLink href="/meetings" label="Browse Meetings" description="View all exported meetings" />
        <QuickLink href="/search" label="Search" description="Full-text search across all content" />
        <QuickLink href="/pipeline" label="Pipeline" description="Trigger export, index, or process jobs" />
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <p className="text-xs font-medium uppercase text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
      {sub && <p className="mt-1 text-xs text-gray-400">{sub}</p>}
    </div>
  );
}

function QuickLink({
  href,
  label,
  description,
}: {
  href: string;
  label: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="rounded-lg border border-gray-200 bg-white p-4 transition hover:border-blue-300 hover:shadow-sm"
    >
      <p className="text-sm font-semibold text-gray-900">{label}</p>
      <p className="mt-1 text-xs text-gray-500">{description}</p>
    </Link>
  );
}
