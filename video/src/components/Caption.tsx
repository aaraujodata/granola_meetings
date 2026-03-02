import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { fontFamilySans } from "../lib/fonts";

type CaptionProps = {
  text: string;
};

export const Caption: React.FC<CaptionProps> = ({ text }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const opacity = interpolate(frame, [0, 15, durationInFrames - 10, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      className="absolute bottom-10 left-0 right-0 flex justify-center"
      style={{ opacity }}
    >
      <div
        className="rounded-full bg-gray-900/80 px-8 py-3 text-lg font-semibold text-white"
        style={{ fontFamily: fontFamilySans }}
      >
        {text}
      </div>
    </div>
  );
};
