import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { fontFamilySans } from "../lib/fonts";
import type { PromoVideoProps } from "../data/schema";

const techStack = ["Next.js", "FastAPI", "Claude AI", "SQLite"];

export const CtaOutro: React.FC<Pick<PromoVideoProps, "title">> = ({
  title,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleScale = spring({ frame, fps, config: { damping: 15 } });
  const titleOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  const builtWithOpacity = interpolate(frame, [10, 25], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill className="flex flex-col items-center justify-center bg-gray-900">
      <div
        className="flex flex-col items-center"
        style={{ fontFamily: fontFamilySans }}
      >
        <h1
          className="font-bold text-white"
          style={{
            fontSize: 72,
            opacity: titleOpacity,
            transform: `scale(${titleScale})`,
          }}
        >
          {title}
        </h1>

        <div className="mt-10" style={{ opacity: builtWithOpacity }}>
          <p className="text-center text-lg text-gray-400">Built with</p>
          <div className="mt-4 flex items-center gap-5">
            {techStack.map((tech, i) => {
              const techOpacity = interpolate(
                frame,
                [15 + i * 4, 20 + i * 4],
                [0, 1],
                {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                },
              );
              return (
                <span
                  key={tech}
                  className="rounded-full border-2 border-gray-700 px-5 py-2 text-base font-semibold text-gray-300"
                  style={{ opacity: techOpacity }}
                >
                  {tech}
                </span>
              );
            })}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
