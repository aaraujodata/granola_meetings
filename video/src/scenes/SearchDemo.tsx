import { useCurrentFrame, interpolate } from "remotion";
import { AppShell } from "../components/AppShell";
import { SearchResult } from "../components/SearchResult";
import { Caption } from "../components/Caption";
import { searchResults } from "../data/mockData";
import { fontFamilySans } from "../lib/fonts";
import type { PromoVideoProps } from "../data/schema";

const CHAR_FRAMES = 3;
const CURSOR_BLINK_FRAMES = 16;

export const SearchDemo: React.FC<Pick<PromoVideoProps, "searchQuery">> = ({
  searchQuery,
}) => {
  const frame = useCurrentFrame();

  const headerOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Typewriter
  const typedChars = Math.min(
    searchQuery.length,
    Math.floor(Math.max(0, frame - 10) / CHAR_FRAMES),
  );
  const typedText = searchQuery.slice(0, typedChars);
  const typingDone = typedChars >= searchQuery.length;

  // Cursor blink
  const cursorOpacity = interpolate(
    frame % CURSOR_BLINK_FRAMES,
    [0, CURSOR_BLINK_FRAMES / 2, CURSOR_BLINK_FRAMES],
    [1, 0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // Results appear after typing is done
  const typingEndFrame = 10 + searchQuery.length * CHAR_FRAMES;

  return (
    <AppShell activeNav="Search">
      <div style={{ fontFamily: fontFamilySans }}>
        <div style={{ opacity: headerOpacity }}>
          <h2 className="text-4xl font-bold text-gray-900">Search</h2>
          <p className="mt-2 text-lg text-gray-500">
            Full-text search across all meeting content
          </p>
        </div>

        {/* Search bar */}
        <div className="mt-6 flex gap-3">
          <div className="flex-1 rounded-xl border-2 border-gray-200 bg-white px-5 py-3">
            <span className="text-base text-gray-900">{typedText}</span>
            <span
              className="inline-block w-0.5 bg-blue-600"
              style={{
                height: "1em",
                verticalAlign: "text-bottom",
                opacity: cursorOpacity,
                marginLeft: 1,
              }}
            />
          </div>
          <button
            className="rounded-xl bg-blue-600 px-6 py-3 text-base font-semibold text-white"
            style={{
              opacity: typingDone ? 1 : 0.5,
            }}
          >
            Search
          </button>
        </div>

        {/* Results */}
        {typingDone && (
          <div className="mt-4 flex flex-col gap-3">
            {searchResults.map((result, i) => (
              <SearchResult
                key={result.title}
                title={result.title}
                contentType={result.contentType}
                date={result.date}
                snippet={result.snippet}
                delay={typingEndFrame + 5 + i * 8}
              />
            ))}
          </div>
        )}
      </div>

      <Caption text="Full-text search across all content" />
    </AppShell>
  );
};
