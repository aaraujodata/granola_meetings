import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { SPRING_SMOOTH } from "../lib/animations";

type StatCardProps = {
  label: string;
  value: number | string;
  sub?: string;
  delay: number;
};

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  sub,
  delay,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({ frame, fps, delay, config: SPRING_SMOOTH });
  const translateY = interpolate(entrance, [0, 1], [30, 0]);
  const displayValue =
    typeof value === "number"
      ? Math.round(
          spring({ frame, fps, delay, config: { damping: 200 } }) * value,
        ).toLocaleString()
      : value;

  return (
    <div
      className="rounded-2xl border-2 border-gray-200 bg-white p-6"
      style={{
        opacity: entrance,
        transform: `translateY(${translateY}px)`,
      }}
    >
      <p className="text-base font-semibold uppercase tracking-wide text-gray-500">{label}</p>
      <p className="mt-2 font-bold text-gray-900" style={{ fontSize: 48 }}>{displayValue}</p>
      {sub && <p className="mt-2 text-sm text-gray-400">{sub}</p>}
    </div>
  );
};
