"use client";

interface TranscriptViewerProps {
  content: string;
}

interface TranscriptLine {
  timestamp: string;
  speaker: string;
  text: string;
}

function parseLine(line: string): TranscriptLine | null {
  // Match: **[HH:MM:SS] Speaker:** text
  const match = line.match(/^\*\*\[(\d{2}:\d{2}:\d{2})\]\s+(.+?):\*\*\s*(.*)/);
  if (!match) return null;
  return { timestamp: match[1], speaker: match[2], text: match[3] };
}

export default function TranscriptViewer({ content }: TranscriptViewerProps) {
  if (!content) {
    return <p className="text-sm text-gray-500">No transcript available.</p>;
  }

  const lines = content.split("\n").filter((l) => l.trim());
  const entries: TranscriptLine[] = [];

  for (const line of lines) {
    const parsed = parseLine(line);
    if (parsed) {
      entries.push(parsed);
    }
  }

  if (entries.length === 0) {
    // Fallback: render raw content
    return (
      <pre className="whitespace-pre-wrap text-sm text-gray-700">{content}</pre>
    );
  }

  return (
    <div className="space-y-2">
      {entries.map((entry, i) => {
        const isYou = entry.speaker === "You";
        return (
          <div key={i} className="flex gap-3 text-sm">
            <span className="w-16 shrink-0 text-gray-400 tabular-nums">
              {entry.timestamp}
            </span>
            <span
              className={`w-14 shrink-0 font-medium ${
                isYou ? "text-blue-600" : "text-gray-500"
              }`}
            >
              {entry.speaker}
            </span>
            <span className="text-gray-800">{entry.text}</span>
          </div>
        );
      })}
    </div>
  );
}
