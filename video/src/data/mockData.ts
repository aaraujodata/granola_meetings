export const meetings = [
  {
    title: "Q4 Product Roadmap Review",
    date: "2026-01-15",
    hasNotes: true,
    hasSummary: true,
    hasTranscript: true,
  },
  {
    title: "Weekly Engineering Standup",
    date: "2026-01-14",
    hasNotes: true,
    hasSummary: true,
    hasTranscript: true,
  },
  {
    title: "Client Onboarding Sync",
    date: "2026-01-13",
    hasNotes: true,
    hasSummary: false,
    hasTranscript: true,
  },
  {
    title: "Sprint Retrospective",
    date: "2026-01-12",
    hasNotes: true,
    hasSummary: true,
    hasTranscript: false,
  },
  {
    title: "Design System Workshop",
    date: "2026-01-10",
    hasNotes: true,
    hasSummary: true,
    hasTranscript: true,
  },
  {
    title: "Budget Planning Q1",
    date: "2026-01-09",
    hasNotes: true,
    hasSummary: true,
    hasTranscript: true,
  },
];

export const searchResults = [
  {
    title: "Q4 Product Roadmap Review",
    contentType: "Notes",
    date: "2026-01-15",
    snippet:
      'Review <mark>action items</mark> from the previous quarter and align on priorities for Q1 launch.',
  },
  {
    title: "Sprint Retrospective",
    contentType: "Summary",
    date: "2026-01-12",
    snippet:
      'Team agreed on <mark>action items</mark>: improve CI pipeline, reduce flaky tests, and document API endpoints.',
  },
  {
    title: "Client Onboarding Sync",
    contentType: "Transcript",
    date: "2026-01-13",
    snippet:
      'Let\'s finalize the <mark>action items</mark> before the end of day so we can update the client.',
  },
];

export const logEntries = [
  { level: "INFO" as const, message: "Starting full sync pipeline..." },
  { level: "INFO" as const, message: "Exported 142 meetings" },
  {
    level: "INFO" as const,
    message: "Built search index: 1,165 entries",
  },
  { level: "INFO" as const, message: "Processing with Claude AI..." },
  {
    level: "INFO" as const,
    message: "Extracted intelligence for 142 meetings",
  },
];

export const pipelineNodes = [
  { label: "Granola App", color: "gray" as const },
  { label: "Export", color: "blue" as const },
  { label: "Index", color: "blue" as const },
  { label: "Search", color: "blue" as const },
  { label: "Claude AI", color: "purple" as const },
];

export const navItems = [
  { label: "Dashboard" },
  { label: "Meetings" },
  { label: "Search" },
  { label: "Pipeline" },
];
