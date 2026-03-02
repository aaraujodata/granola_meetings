import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { AppShell } from "../components/AppShell";
import { ProgressBar } from "../components/ProgressBar";
import { TerminalLog } from "../components/TerminalLog";
import { Caption } from "../components/Caption";
import { logEntries } from "../data/mockData";
import { fontFamilySans } from "../lib/fonts";
import { SPRING_SNAPPY } from "../lib/animations";

export const PipelineExec: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Button pulse
  const buttonScale = spring({
    frame,
    fps,
    delay: 5,
    config: SPRING_SNAPPY,
  });

  // Determine step statuses based on frame
  const exportDone = frame > 25;
  const indexDone = frame > 40;

  const steps = [
    {
      label: "Export",
      status: (exportDone ? "completed" : frame > 15 ? "running" : "pending") as
        | "completed"
        | "running"
        | "pending",
    },
    {
      label: "Index",
      status: (indexDone ? "completed" : exportDone ? "running" : "pending") as
        | "completed"
        | "running"
        | "pending",
    },
    {
      label: "Process",
      status: (indexDone ? "running" : "pending") as
        | "completed"
        | "running"
        | "pending",
    },
  ];

  return (
    <AppShell activeNav="Pipeline">
      <div style={{ fontFamily: fontFamilySans }}>
        <div style={{ opacity: headerOpacity }}>
          <h2 className="text-4xl font-bold text-gray-900">Pipeline</h2>
          <p className="mt-2 text-lg text-gray-500">
            Trigger export, index, or process jobs
          </p>
        </div>

        {/* Action button */}
        <div className="mt-6">
          <button
            className="rounded-xl bg-blue-600 px-6 py-3 text-base font-semibold text-white"
            style={{ transform: `scale(${buttonScale})` }}
          >
            Full Sync
          </button>
        </div>

        {/* Progress area */}
        {frame > 15 && (
          <div className="mt-6 rounded-xl border-2 border-blue-200 bg-blue-50 p-5">
            <ProgressBar progress={75} steps={steps} />
          </div>
        )}

        {/* Terminal log */}
        {frame > 25 && (
          <div className="mt-4">
            <TerminalLog
              entries={logEntries}
              startFrame={25}
              framesPerLine={8}
            />
          </div>
        )}
      </div>

      <Caption text="One-click pipeline execution" />
    </AppShell>
  );
};
