import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { SPRING_SMOOTH } from "../lib/animations";

type SearchResultProps = {
  title: string;
  contentType: string;
  date: string;
  snippet: string;
  delay: number;
};

export const SearchResult: React.FC<SearchResultProps> = ({
  title,
  contentType,
  date,
  snippet,
  delay,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({ frame, fps, delay, config: SPRING_SMOOTH });
  const translateY = interpolate(entrance, [0, 1], [20, 0]);

  // Strip <mark> tags and manually render with highlight spans
  const parts = snippet.split(/(<mark>.*?<\/mark>)/g);

  return (
    <div
      className="rounded-2xl border-2 border-gray-200 bg-white p-5"
      style={{
        opacity: entrance,
        transform: `translateY(${translateY}px)`,
      }}
    >
      <div className="flex items-center gap-3">
        <p className="text-lg font-bold text-gray-900">{title}</p>
        <span className="rounded-md bg-blue-100 px-2.5 py-1 text-sm font-semibold text-blue-700">
          {contentType}
        </span>
        <span className="text-sm text-gray-400">{date}</span>
      </div>
      <p className="mt-3 text-base leading-relaxed text-gray-600">
        {parts.map((part, i) => {
          if (part.startsWith("<mark>")) {
            const text = part.replace(/<\/?mark>/g, "");
            return (
              <span key={i} className="rounded bg-yellow-200 px-1 font-semibold text-gray-900">
                {text}
              </span>
            );
          }
          return <span key={i}>{part}</span>;
        })}
      </p>
    </div>
  );
};
