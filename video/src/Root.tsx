import { Composition, Folder } from "remotion";
import "./index.css";
import { PromoVideo } from "./PromoVideo";
import { TitleIntro } from "./scenes/TitleIntro";
import { PipelineFlow } from "./scenes/PipelineFlow";
import { Dashboard } from "./scenes/Dashboard";
import { MeetingGrid } from "./scenes/MeetingGrid";
import { SearchDemo } from "./scenes/SearchDemo";
import { PipelineExec } from "./scenes/PipelineExec";
import { CtaOutro } from "./scenes/CtaOutro";
import { promoVideoSchema } from "./data/schema";

const FPS = 30;
const WIDTH = 1920;
const HEIGHT = 1080;

/**
 * Total duration: sum(scene_durations) - sum(transition_durations)
 * = (90+125+125+110+145+125+90) - (6*10) = 810 - 60 = 750 frames = 25s
 */
const PROMO_DURATION = 750;

const defaultProps = {
  title: "Granola Meeting Explorer",
  tagline: "Export \u00b7 Index \u00b7 Search \u00b7 Enrich",
  meetingCount: 573,
  searchEntries: 1165,
  exportedCount: 573,
  searchQuery: "action items from Q4",
  accentColor: "#2563eb",
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Full promo video */}
      <Composition
        id="PromoVideo"
        component={PromoVideo}
        schema={promoVideoSchema}
        durationInFrames={PROMO_DURATION}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        defaultProps={defaultProps}
      />

      {/* Individual scenes for preview/development */}
      <Folder name="Scenes">
        <Composition
          id="TitleIntro"
          component={TitleIntro}
          durationInFrames={90}
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
          defaultProps={{
            title: defaultProps.title,
            tagline: defaultProps.tagline,
            accentColor: defaultProps.accentColor,
          }}
        />
        <Composition
          id="PipelineFlow"
          component={PipelineFlow}
          durationInFrames={125}
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
        />
        <Composition
          id="Dashboard"
          component={Dashboard}
          durationInFrames={125}
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
          defaultProps={{
            meetingCount: defaultProps.meetingCount,
            searchEntries: defaultProps.searchEntries,
            exportedCount: defaultProps.exportedCount,
          }}
        />
        <Composition
          id="MeetingGrid"
          component={MeetingGrid}
          durationInFrames={110}
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
          defaultProps={{
            meetingCount: defaultProps.meetingCount,
          }}
        />
        <Composition
          id="SearchDemo"
          component={SearchDemo}
          durationInFrames={145}
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
          defaultProps={{
            searchQuery: defaultProps.searchQuery,
          }}
        />
        <Composition
          id="PipelineExec"
          component={PipelineExec}
          durationInFrames={125}
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
        />
        <Composition
          id="CtaOutro"
          component={CtaOutro}
          durationInFrames={90}
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
          defaultProps={{
            title: defaultProps.title,
          }}
        />
      </Folder>
    </>
  );
};
