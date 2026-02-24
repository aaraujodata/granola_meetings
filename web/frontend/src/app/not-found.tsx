import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0) rotate(-2deg); }
          50% { transform: translateY(-12px) rotate(1deg); }
        }
        @keyframes signal {
          0% { opacity: 0; transform: scale(0.5); }
          40% { opacity: 0.6; }
          100% { opacity: 0; transform: scale(1.2); }
        }
        .float-card { animation: float 3s ease-in-out infinite; }
        .signal-arc { animation: signal 2s ease-out infinite; }
        .signal-arc-2 { animation: signal 2s ease-out 0.3s infinite; }
        .signal-arc-3 { animation: signal 2s ease-out 0.6s infinite; }
      `}</style>

      {/* Floating lost meeting card illustration */}
      <div className="float-card mb-8">
        <div className="relative">
          {/* Card */}
          <div className="w-56 rounded-lg border-2 border-dashed border-gray-300 bg-white p-5 shadow-lg">
            {/* Camera icon with signal arcs */}
            <div className="mb-3 flex items-center gap-2">
              <div className="relative">
                <svg
                  className="h-6 w-6 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
                  />
                </svg>
                {/* Signal arcs */}
                <div className="signal-arc absolute -right-2 -top-2 h-3 w-3 rounded-full border border-gray-300" />
                <div className="signal-arc-2 absolute -right-3 -top-3 h-5 w-5 rounded-full border border-gray-200" />
                <div className="signal-arc-3 absolute -right-4 -top-4 h-7 w-7 rounded-full border border-gray-100" />
              </div>
              <div className="h-2 w-2 rounded-full bg-red-400" />
            </div>
            {/* Fake content lines */}
            <div className="space-y-2">
              <div className="h-2.5 w-3/4 rounded bg-gray-200" />
              <div className="h-2 w-full rounded bg-gray-100" />
              <div className="h-2 w-5/6 rounded bg-gray-100" />
            </div>
            {/* Fake badges */}
            <div className="mt-3 flex gap-1.5">
              <div className="h-4 w-10 rounded bg-gray-100" />
              <div className="h-4 w-12 rounded bg-gray-100" />
            </div>
          </div>

          {/* Dotted trail below card */}
          <div className="mx-auto mt-2 flex flex-col items-center gap-1.5">
            <div className="h-1 w-1 rounded-full bg-gray-300" />
            <div className="h-1 w-1 rounded-full bg-gray-200" />
            <div className="h-1 w-1 rounded-full bg-gray-100" />
          </div>
        </div>
      </div>

      <h2 className="text-2xl font-bold text-gray-900">
        This meeting has left the building
      </h2>
      <p className="mt-2 max-w-md text-sm text-gray-500">
        The page you&apos;re looking for doesn&apos;t exist, or it may have
        wandered off to find better Wi-Fi.
      </p>

      <div className="mt-6 flex gap-3">
        <Link
          href="/"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700"
        >
          Back to Dashboard
        </Link>
        <Link
          href="/meetings"
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50"
        >
          Browse Meetings
        </Link>
      </div>

      <p className="mt-10 text-xs text-gray-300">Error 404</p>
    </div>
  );
}
