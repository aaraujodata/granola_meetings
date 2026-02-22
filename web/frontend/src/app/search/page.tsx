"use client";

import { useState } from "react";
import Link from "next/link";
import { search } from "@/lib/api";
import SearchBar from "@/components/SearchBar";
import type { SearchResult } from "@/types";

export default function SearchPage() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const handleSearch = (query: string, type?: string, dateFrom?: string, dateTo?: string) => {
    setLoading(true);
    setError(null);
    search(query, type, dateFrom, dateTo)
      .then((data) => {
        setResults(data);
        setSearched(true);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900">Search</h2>
      <p className="mt-1 mb-6 text-sm text-gray-500">
        Full-text search across all meeting content (supports AND, OR, NOT, &quot;phrases&quot;)
      </p>

      <SearchBar onSearch={handleSearch} loading={loading} />

      {error && (
        <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="mt-6 space-y-3">
        {searched && results.length === 0 && !loading && (
          <p className="text-sm text-gray-500">No results found.</p>
        )}

        {results.map((r, i) => (
          <Link
            key={i}
            href={`/meetings/${encodeURIComponent(r.meeting_id)}`}
            className="block rounded-lg border border-gray-200 bg-white p-4 transition hover:border-blue-300 hover:shadow-sm"
          >
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-gray-900">
                {r.title}
              </h3>
              <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">
                {r.content_type}
              </span>
            </div>
            <p className="mt-1 text-xs text-gray-500">{r.date}</p>
            <p
              className="mt-2 text-sm text-gray-700"
              dangerouslySetInnerHTML={{
                __html: r.snippet.replace(
                  /\*\*(.*?)\*\*/g,
                  '<mark class="bg-yellow-200 px-0.5 rounded">$1</mark>'
                ),
              }}
            />
          </Link>
        ))}
      </div>
    </div>
  );
}
