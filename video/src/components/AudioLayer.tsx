import { Sequence, staticFile, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";

/**
 * Scene timing (cumulative start frames accounting for transition overlaps):
 * TitleIntro:   0
 * PipelineFlow: 80  (90 - 10)
 * Dashboard:    195 (80 + 125 - 10)
 * MeetingGrid:  310 (195 + 125 - 10)
 * SearchDemo:   410 (310 + 110 - 10)
 * PipelineExec: 545 (410 + 145 - 10)
 * CtaOutro:     660 (545 + 125 - 10)
 */

const SCENE_STARTS = {
  titleIntro: 0,
  pipelineFlow: 80,
  dashboard: 195,
  meetingGrid: 310,
  searchDemo: 410,
  pipelineExec: 545,
  ctaOutro: 660,
} as const;

/** Frames between each typed character in SearchDemo */
const CHAR_FRAMES = 3;
/** Search typing starts at frame 10 within the search scene */
const SEARCH_TYPING_OFFSET = 10;
/** Total characters in "action items from Q4" */
const SEARCH_QUERY_LENGTH = 20;

/**
 * AudioLayer — syncs sound effects to visual keyframes
 *
 * - Ambient background hum (full duration, subtle)
 * - Whoosh on each scene transition
 * - Keyboard clicks during search typewriter
 * - Pop sounds when UI elements appear (stat cards, meeting cards)
 * - Ding on CTA outro reveal
 */
export const AudioLayer: React.FC = () => {
  const { fps } = useVideoConfig();

  // Transition frames (where the fade happens — 10 frames before each scene start)
  const transitionFrames = [
    SCENE_STARTS.pipelineFlow,
    SCENE_STARTS.dashboard,
    SCENE_STARTS.meetingGrid,
    SCENE_STARTS.searchDemo,
    SCENE_STARTS.pipelineExec,
    SCENE_STARTS.ctaOutro,
  ];

  // Stat card pop frames (inside Dashboard scene: delays 5, 15, 25, 35)
  const statCardFrames = [5, 15, 25, 35].map(
    (d) => SCENE_STARTS.dashboard + d,
  );

  // Meeting card pop frames (inside MeetingGrid scene: delays 5, 13, 21, 29, 37, 45)
  const meetingCardFrames = [0, 1, 2, 3, 4, 5].map(
    (i) => SCENE_STARTS.meetingGrid + 5 + i * 8,
  );

  // Pipeline node pop frames (inside PipelineFlow: delays 0, 10, 20, 30, 40)
  const pipelineNodeFrames = [0, 10, 20, 30, 40].map(
    (d) => SCENE_STARTS.pipelineFlow + d,
  );

  // Keyboard click frames during search typing
  const keyClickFrames = Array.from({ length: SEARCH_QUERY_LENGTH }, (_, i) =>
    SCENE_STARTS.searchDemo + SEARCH_TYPING_OFFSET + i * CHAR_FRAMES,
  );

  return (
    <>
      {/* Ambient background — very subtle, full video duration */}
      <Audio
        src={staticFile("ambient.mp3")}
        volume={0.15}
      />

      {/* Whoosh on each scene transition */}
      {transitionFrames.map((frame) => (
        <Sequence key={`whoosh-${frame}`} from={frame} durationInFrames={15}>
          <Audio src={staticFile("whoosh.mp3")} volume={0.5} />
        </Sequence>
      ))}

      {/* Keyboard clicks during search typewriter */}
      {keyClickFrames.map((frame) => (
        <Sequence key={`key-${frame}`} from={frame} durationInFrames={3}>
          <Audio
            src={staticFile("key-click.mp3")}
            volume={(f) => {
              // Slight random-ish variation based on frame position
              const base = 0.3 + (frame % 3) * 0.1;
              return f === 0 ? base : base * 0.8;
            }}
          />
        </Sequence>
      ))}

      {/* Pop sounds for stat cards appearing */}
      {statCardFrames.map((frame) => (
        <Sequence key={`stat-pop-${frame}`} from={frame} durationInFrames={8}>
          <Audio src={staticFile("pop.mp3")} volume={0.4} />
        </Sequence>
      ))}

      {/* Pop sounds for pipeline flow nodes appearing */}
      {pipelineNodeFrames.map((frame) => (
        <Sequence key={`node-pop-${frame}`} from={frame} durationInFrames={8}>
          <Audio src={staticFile("pop.mp3")} volume={0.3} />
        </Sequence>
      ))}

      {/* Pop sounds for meeting cards appearing */}
      {meetingCardFrames.map((frame) => (
        <Sequence key={`meeting-pop-${frame}`} from={frame} durationInFrames={8}>
          <Audio src={staticFile("pop.mp3")} volume={0.25} />
        </Sequence>
      ))}

      {/* Ding on CTA title reveal */}
      <Sequence from={SCENE_STARTS.ctaOutro + 5} durationInFrames={Math.round(fps * 0.5)}>
        <Audio src={staticFile("ding.mp3")} volume={0.5} />
      </Sequence>

      {/* Ding for pipeline exec button press */}
      <Sequence from={SCENE_STARTS.pipelineExec + 5} durationInFrames={Math.round(fps * 0.3)}>
        <Audio src={staticFile("ding.mp3")} volume={0.35} />
      </Sequence>
    </>
  );
};
