import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import { SPRING_SNAPPY } from "../lib/animations";
import { fontFamilySans } from "../lib/fonts";

type FlowNodeProps = {
  label: string;
  color: "gray" | "blue" | "purple";
  delay: number;
};

const colorMap = {
  gray: { bg: "bg-gray-100", border: "border-gray-300", text: "text-gray-700" },
  blue: { bg: "bg-blue-50", border: "border-blue-300", text: "text-blue-700" },
  purple: {
    bg: "bg-purple-50",
    border: "border-purple-300",
    text: "text-purple-700",
  },
};

export const FlowNode: React.FC<FlowNodeProps> = ({ label, color, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({ frame, fps, delay, config: SPRING_SNAPPY });
  const c = colorMap[color];

  return (
    <div
      className={`flex items-center justify-center rounded-2xl border-2 px-7 py-4 ${c.bg} ${c.border}`}
      style={{
        transform: `scale(${scale})`,
        fontFamily: fontFamilySans,
      }}
    >
      <span className={`text-lg font-bold ${c.text}`}>{label}</span>
    </div>
  );
};
