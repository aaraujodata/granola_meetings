import { useCurrentFrame, interpolate } from "remotion";

type FlowArrowProps = {
  delay: number;
  width?: number;
};

export const FlowArrow: React.FC<FlowArrowProps> = ({
  delay,
  width = 40,
}) => {
  const frame = useCurrentFrame();

  const progress = interpolate(frame, [delay, delay + 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div className="flex items-center" style={{ width, opacity: progress }}>
      <svg viewBox={`0 0 ${width} 20`} width={width} height={20}>
        <line
          x1={0}
          y1={10}
          x2={width - 8}
          y2={10}
          stroke="#9ca3af"
          strokeWidth={2}
          strokeDasharray={width}
          strokeDashoffset={(1 - progress) * width}
        />
        <polygon
          points={`${width - 8},5 ${width},10 ${width - 8},15`}
          fill="#9ca3af"
          opacity={progress}
        />
      </svg>
    </div>
  );
};
