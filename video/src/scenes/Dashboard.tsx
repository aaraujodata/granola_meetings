import { useCurrentFrame, interpolate } from "remotion";
import { AppShell } from "../components/AppShell";
import { StatCard } from "../components/StatCard";
import { Caption } from "../components/Caption";
import { fontFamilySans } from "../lib/fonts";
import type { PromoVideoProps } from "../data/schema";

export const Dashboard: React.FC<
  Pick<PromoVideoProps, "meetingCount" | "searchEntries" | "exportedCount">
> = ({ meetingCount, searchEntries, exportedCount }) => {
  const frame = useCurrentFrame();

  const headerOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AppShell activeNav="Dashboard">
      <div style={{ fontFamily: fontFamilySans }}>
        <div style={{ opacity: headerOpacity }}>
          <h2 className="text-4xl font-bold text-gray-900">Dashboard</h2>
          <p className="mt-2 text-lg text-gray-500">
            Overview of your Granola meeting data
          </p>
        </div>

        <div className="mt-8 grid grid-cols-4 gap-5">
          <StatCard label="Meetings" value={meetingCount} delay={5} />
          <StatCard label="Search Entries" value={searchEntries} delay={15} />
          <StatCard label="Exported" value={exportedCount} delay={25} />
          <StatCard label="Token" value="Valid" sub="42m remaining" delay={35} />
        </div>
      </div>

      <Caption text="Real-time dashboard" />
    </AppShell>
  );
};
