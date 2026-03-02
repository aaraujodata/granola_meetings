import { useCurrentFrame, interpolate } from "remotion";
import { AppShell } from "../components/AppShell";
import { MeetingCard } from "../components/MeetingCard";
import { Caption } from "../components/Caption";
import { meetings } from "../data/mockData";
import { fontFamilySans } from "../lib/fonts";
import type { PromoVideoProps } from "../data/schema";

export const MeetingGrid: React.FC<
  Pick<PromoVideoProps, "meetingCount">
> = ({ meetingCount }) => {
  const frame = useCurrentFrame();

  const headerOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AppShell activeNav="Meetings">
      <div style={{ fontFamily: fontFamilySans }}>
        <div style={{ opacity: headerOpacity }}>
          <h2 className="text-4xl font-bold text-gray-900">Meetings</h2>
          <p className="mt-2 text-lg text-gray-500">
            {meetingCount} meetings exported
          </p>
        </div>

        <div className="mt-8 grid grid-cols-3 gap-5">
          {meetings.map((meeting, i) => (
            <MeetingCard
              key={meeting.title}
              title={meeting.title}
              date={meeting.date}
              hasNotes={meeting.hasNotes}
              hasSummary={meeting.hasSummary}
              hasTranscript={meeting.hasTranscript}
              delay={5 + i * 8}
            />
          ))}
        </div>
      </div>

      <Caption text={`${meetingCount} meetings organized`} />
    </AppShell>
  );
};
