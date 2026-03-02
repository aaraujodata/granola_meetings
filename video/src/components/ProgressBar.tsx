import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

type Step = {
  label: string;
  status: "completed" | "running" | "pending";
};

type ProgressBarProps = {
  progress: number; // 0-100
  steps: Step[];
};

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  steps,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const barWidth = interpolate(frame, [0, 2 * fps], [0, progress], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div>
      {/* Progress bar */}
      <div className="h-4 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-blue-600"
          style={{ width: `${barWidth}%` }}
        />
      </div>
      <p className="mt-2 text-right text-base font-semibold text-gray-500">
        {Math.round(barWidth)}%
      </p>

      {/* Step tracker */}
      <div className="mt-4 flex items-center gap-3">
        {steps.map((step, i) => (
          <div key={step.label} className="flex items-center gap-3">
            {i > 0 && <span className="text-lg text-gray-300">&rarr;</span>}
            <div
              className={`flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold ${
                step.status === "completed"
                  ? "bg-green-100 text-green-800"
                  : step.status === "running"
                    ? "bg-blue-100 text-blue-800"
                    : "bg-gray-100 text-gray-400"
              }`}
            >
              {step.status === "completed" && <span>&#10003;</span>}
              {step.status === "running" && <span>&#9697;</span>}
              {step.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
