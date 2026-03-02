import { useCurrentFrame, interpolate } from "remotion";
import { fontFamilyMono } from "../lib/fonts";

type LogEntry = {
  level: "INFO" | "WARN" | "ERROR";
  message: string;
};

type TerminalLogProps = {
  entries: LogEntry[];
  startFrame: number;
  framesPerLine: number;
};

const levelColor: Record<string, string> = {
  INFO: "text-green-400",
  WARN: "text-yellow-400",
  ERROR: "text-red-400",
};

export const TerminalLog: React.FC<TerminalLogProps> = ({
  entries,
  startFrame,
  framesPerLine,
}) => {
  const frame = useCurrentFrame();

  return (
    <div
      className="rounded-2xl bg-gray-900 p-6"
      style={{ fontFamily: fontFamilyMono }}
    >
      {entries.map((entry, i) => {
        const entryStart = startFrame + i * framesPerLine;
        const opacity = interpolate(
          frame,
          [entryStart, entryStart + 5],
          [0, 1],
          {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          },
        );

        return (
          <div
            key={i}
            className="py-1 text-base"
            style={{ opacity }}
          >
            <span className={levelColor[entry.level]}>
              [{entry.level}]
            </span>{" "}
            <span className="text-gray-300">{entry.message}</span>
          </div>
        );
      })}
    </div>
  );
};
