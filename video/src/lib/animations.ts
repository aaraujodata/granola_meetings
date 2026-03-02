import { interpolate, spring } from "remotion";

/** Smooth spring with no bounce — ideal for subtle reveals. */
export const SPRING_SMOOTH = { damping: 200 };

/** Snappy spring with minimal bounce — ideal for UI elements. */
export const SPRING_SNAPPY = { damping: 20, stiffness: 200 };

/** Bouncy spring — ideal for playful entrances. */
export const SPRING_BOUNCY = { damping: 8 };

/** Fade in over a range of frames. */
export function fadeIn(
  frame: number,
  startFrame: number,
  durationFrames: number,
): number {
  return interpolate(frame, [startFrame, startFrame + durationFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
}

/** Scale in using a spring. */
export function springScale(
  frame: number,
  fps: number,
  delay: number = 0,
  config = SPRING_SMOOTH,
): number {
  return spring({ frame, fps, delay, config });
}

/** Counter that animates from 0 to target. */
export function animatedCounter(
  frame: number,
  fps: number,
  target: number,
  delay: number = 0,
): number {
  const progress = spring({
    frame,
    fps,
    delay,
    config: { damping: 200 },
  });
  return Math.round(progress * target);
}

/** Stagger delay for item at given index. */
export function staggerDelay(
  index: number,
  framesPerItem: number,
): number {
  return index * framesPerItem;
}
