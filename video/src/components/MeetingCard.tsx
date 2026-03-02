import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { SPRING_SNAPPY } from "../lib/animations";

type MeetingCardProps = {
  title: string;
  date: string;
  hasNotes: boolean;
  hasSummary: boolean;
  hasTranscript: boolean;
  delay: number;
};

const Badge: React.FC<{ label: string; active: boolean; badgeDelay: number }> = ({
  label,
  active,
  badgeDelay,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({ frame, fps, delay: badgeDelay, config: SPRING_SNAPPY });

  return (
    <span
      className={`inline-block rounded-md px-3 py-1 text-sm font-semibold ${
        active
          ? "bg-blue-100 text-blue-700"
          : "bg-gray-100 text-gray-400"
      }`}
      style={{ transform: `scale(${scale})` }}
    >
      {label}
    </span>
  );
};

export const MeetingCard: React.FC<MeetingCardProps> = ({
  title,
  date,
  hasNotes,
  hasSummary,
  hasTranscript,
  delay,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({ frame, fps, delay, config: SPRING_SNAPPY });
  const translateX = interpolate(entrance, [0, 1], [-40, 0]);

  return (
    <div
      className="rounded-2xl border-2 border-gray-200 bg-white p-5"
      style={{
        opacity: entrance,
        transform: `translateX(${translateX}px)`,
      }}
    >
      <p className="text-lg font-bold text-gray-900">{title}</p>
      <p className="mt-1 text-sm text-gray-400">{date}</p>
      <div className="mt-3 flex gap-2">
        <Badge label="Notes" active={hasNotes} badgeDelay={delay + 10} />
        <Badge label="Summary" active={hasSummary} badgeDelay={delay + 15} />
        <Badge label="Transcript" active={hasTranscript} badgeDelay={delay + 20} />
      </div>
    </div>
  );
};
