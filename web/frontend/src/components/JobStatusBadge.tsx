import type { JobStatusType } from "@/types";

const statusStyles: Record<JobStatusType, string> = {
  queued: "bg-yellow-100 text-yellow-800",
  running: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
};

export default function JobStatusBadge({ status }: { status: JobStatusType }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${statusStyles[status]}`}
    >
      {status === "running" && (
        <span className="inline-block h-2 w-2 animate-spin rounded-full border border-blue-600 border-t-transparent" />
      )}
      {status}
    </span>
  );
}
