import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { fontFamilySans } from "../lib/fonts";
import type { PromoVideoProps } from "../data/schema";

export const TitleIntro: React.FC<
  Pick<PromoVideoProps, "title" | "tagline" | "accentColor">
> = ({ title, tagline, accentColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleScale = spring({ frame, fps, config: { damping: 15 } });
  const titleOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  const taglineOpacity = interpolate(frame, [15, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const taglineY = interpolate(frame, [15, 30], [15, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill className="flex items-center justify-center bg-gray-50">
      <div className="flex flex-col items-center" style={{ fontFamily: fontFamilySans }}>
        <h1
          className="font-bold text-gray-900"
          style={{
            fontSize: 80,
            opacity: titleOpacity,
            transform: `scale(${titleScale})`,
          }}
        >
          {title}
        </h1>
        <p
          className="mt-6 font-medium tracking-widest"
          style={{
            fontSize: 28,
            color: accentColor,
            opacity: taglineOpacity,
            transform: `translateY(${taglineY}px)`,
          }}
        >
          {tagline}
        </p>
      </div>
    </AbsoluteFill>
  );
};
