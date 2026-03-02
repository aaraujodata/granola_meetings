import { AbsoluteFill } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { TitleIntro } from "./scenes/TitleIntro";
import { PipelineFlow } from "./scenes/PipelineFlow";
import { Dashboard } from "./scenes/Dashboard";
import { MeetingGrid } from "./scenes/MeetingGrid";
import { SearchDemo } from "./scenes/SearchDemo";
import { PipelineExec } from "./scenes/PipelineExec";
import { CtaOutro } from "./scenes/CtaOutro";
import { AudioLayer } from "./components/AudioLayer";
import type { PromoVideoProps } from "./data/schema";

const TRANSITION_DURATION = 10;
const transitionTiming = linearTiming({ durationInFrames: TRANSITION_DURATION });
const transitionPresentation = fade();

/**
 * Scene durations (in frames at 30fps):
 * TitleIntro: 90 (3s)
 * PipelineFlow: 125 (4.17s)
 * Dashboard: 125 (4.17s)
 * MeetingGrid: 110 (3.67s)
 * SearchDemo: 145 (4.83s)
 * PipelineExec: 125 (4.17s)
 * CtaOutro: 90 (3s)
 *
 * Total scene frames: 810
 * Transitions: 6 x 10 = 60 frames overlap
 * Effective duration: 810 - 60 = 750 frames = 25s
 */

export const PromoVideo: React.FC<PromoVideoProps> = ({
  title,
  tagline,
  meetingCount,
  searchEntries,
  exportedCount,
  searchQuery,
  accentColor,
}) => {
  return (
    <AbsoluteFill>
      {/* Visual layer */}
      <TransitionSeries>
        {/* Scene 0: Title Intro */}
        <TransitionSeries.Sequence durationInFrames={90}>
          <TitleIntro title={title} tagline={tagline} accentColor={accentColor} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={transitionPresentation}
          timing={transitionTiming}
        />

        {/* Scene 1: Pipeline Flow */}
        <TransitionSeries.Sequence durationInFrames={125}>
          <PipelineFlow />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={transitionPresentation}
          timing={transitionTiming}
        />

        {/* Scene 2: Dashboard */}
        <TransitionSeries.Sequence durationInFrames={125}>
          <Dashboard
            meetingCount={meetingCount}
            searchEntries={searchEntries}
            exportedCount={exportedCount}
          />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={transitionPresentation}
          timing={transitionTiming}
        />

        {/* Scene 3: Meeting Grid */}
        <TransitionSeries.Sequence durationInFrames={110}>
          <MeetingGrid meetingCount={meetingCount} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={transitionPresentation}
          timing={transitionTiming}
        />

        {/* Scene 4: Search Demo */}
        <TransitionSeries.Sequence durationInFrames={145}>
          <SearchDemo searchQuery={searchQuery} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={transitionPresentation}
          timing={transitionTiming}
        />

        {/* Scene 5: Pipeline Exec */}
        <TransitionSeries.Sequence durationInFrames={125}>
          <PipelineExec />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={transitionPresentation}
          timing={transitionTiming}
        />

        {/* Scene 6: CTA Outro */}
        <TransitionSeries.Sequence durationInFrames={90}>
          <CtaOutro title={title} />
        </TransitionSeries.Sequence>
      </TransitionSeries>

      {/* Audio layer — synced sound effects */}
      <AudioLayer />
    </AbsoluteFill>
  );
};
