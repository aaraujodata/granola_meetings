---
title: "feat: Create Remotion promotional video showcasing Granola Meeting Explorer"
type: feat
status: completed
date: 2026-02-25
---

# feat: Create Remotion Promotional Video for Granola Meeting Explorer

## Overview

Create a standalone Remotion 4.x project (in `video/`) that produces a ~18-second promotional video showcasing the Granola Meeting Explorer app. The video communicates the app's value proposition across 5 feature scenes bookended by a title intro and CTA outro, using the app's existing design system (blue-600 primary, gray-50/white backgrounds, Tailwind v4).

The video should feel like a polished product demo — not a slideshow — with smooth fade transitions, staggered element animations, and text captions tying each scene to a clear benefit.

## Problem Statement / Motivation

The Granola Meeting Explorer is a fully functional data pipeline + web UI that exports, indexes, enriches, and serves meeting data. It has no visual marketing asset to communicate its value quickly. A 15–18 second video would serve as:

- A portfolio showcase piece (GitHub README, personal site)
- A social media asset (LinkedIn, Twitter/X)
- A quick demo for stakeholders who won't read documentation

## Proposed Solution

A Remotion 4.x project at `video/` with:

- **7 scenes** (title intro + 5 features + CTA outro) totaling 540 frames at 30fps (18 seconds)
- **Tailwind CSS v4** matching the existing web app's design tokens
- **Zod-parameterized** compositions for easy stat/title customization
- **Fade transitions** between scenes (10 frames each)
- **Text captions** per scene for clarity
- **Silent render** (audio can be added later)
- **1920x1080 landscape** as the primary format

## Technical Approach

### Architecture

The Remotion project is fully isolated from the web app — its own `package.json`, `tsconfig.json`, `node_modules`, and Tailwind config. No code is shared with `web/frontend/`. Design tokens are extracted into a `theme.ts` constants file.

```
video/
  package.json              # Remotion + React + Tailwind v4
  tsconfig.json             # ES2018, react-jsx
  remotion.config.ts        # Tailwind v4 webpack override
  src/
    index.ts                # registerRoot() entry point
    Root.tsx                 # Composition registry (full promo + individual scenes)
    index.css               # @import 'tailwindcss'
    PromoVideo.tsx           # Full composition orchestrating all scenes
    scenes/
      TitleIntro.tsx         # Scene 0: App name + tagline
      PipelineFlow.tsx       # Scene 1: Data pipeline flow animation
      Dashboard.tsx          # Scene 2: Stats cards animating in
      MeetingGrid.tsx        # Scene 3: Meeting cards with badges
      SearchDemo.tsx         # Scene 4: Typewriter search + highlighted results
      PipelineExec.tsx       # Scene 5: Progress bar + terminal logs
      CtaOutro.tsx           # Scene 6: CTA with tech stack + URL
    components/
      AppShell.tsx           # Shared sidebar chrome (scenes 2-5)
      StatCard.tsx           # Animated counter card
      MeetingCard.tsx        # Card with title, date, badges
      SearchResult.tsx       # Result with highlighted snippet
      ProgressBar.tsx        # Animated fill bar + step tracker
      TerminalLog.tsx        # Scrolling log viewer
      Caption.tsx            # Bottom caption overlay
      FlowNode.tsx           # Pipeline node (circle + label)
      FlowArrow.tsx          # Animated connecting arrow
    data/
      mockData.ts            # All mock content (meetings, logs, stats)
      schema.ts              # Zod parameter schema
    lib/
      theme.ts               # Design tokens extracted from web app
      animations.ts          # Shared spring/interpolation helpers
  public/                    # Static assets (logos, icons if needed)
  out/                       # Rendered output (gitignored)
```

### Scene Timeline (540 frames total @ 30fps = 18 seconds)

| Scene | Name | Frames | Duration | Effective (after transitions) |
|-------|------|--------|----------|-------------------------------|
| 0 | Title Intro | 60 | 2.0s | 1.67s |
| — | *fade transition* | 10 | 0.33s | — |
| 1 | Pipeline Flow | 90 | 3.0s | 2.67s |
| — | *fade transition* | 10 | 0.33s | — |
| 2 | Dashboard Stats | 80 | 2.67s | 2.33s |
| — | *fade transition* | 10 | 0.33s | — |
| 3 | Meeting Grid | 75 | 2.5s | 2.17s |
| — | *fade transition* | 10 | 0.33s | — |
| 4 | Search Demo | 95 | 3.17s | 2.83s |
| — | *fade transition* | 10 | 0.33s | — |
| 5 | Pipeline Exec | 80 | 2.67s | 2.33s |
| — | *fade transition* | 10 | 0.33s | — |
| 6 | CTA Outro | 60 | 2.0s | 2.0s |
| **Total** | | **540** | **18s** | **~16s content** |

> Formula: `sum(scene_frames) - sum(transition_frames) = total_frames`
> `540 - 0 = 540` (transitions overlap adjacent scenes via `TransitionSeries`)

### Scene-by-Scene Storyboard

#### Scene 0: Title Intro (60 frames / 2s)

- **Background**: Solid `bg-gray-50` with subtle gradient
- **Elements**: App name "Granola Meeting Explorer" fades + scales in (spring animation), tagline "Export · Index · Search · Enrich" fades in below with stagger
- **Caption**: None (this IS the title)
- **Exit**: Holds for 0.5s then fades to Scene 1

#### Scene 1: Pipeline Flow (90 frames / 3s)

- **Background**: Clean white with subtle grid pattern
- **Elements**: 5 flow nodes appear sequentially left-to-right:
  1. "Granola App" (gray node)
  2. → "Export" (blue node)
  3. → "Index" (blue node)
  4. → "Search" (blue node)
  5. → "Claude AI" (purple/blue node)
- **Animation**: Each node springs in (scale 0→1) with connecting arrow drawing left-to-right. ~18 frames per node+arrow = 90 frames total
- **Caption**: "Automated data pipeline"

#### Scene 2: Dashboard Stats (80 frames / 2.67s)

- **Background**: App shell with sidebar (Dashboard nav active, blue highlight)
- **Elements**: 4 stat cards in 2x2 grid, each with:
  - Icon area, label, and counter
  - Counter animates from 0 → target value (spring)
  - Cards: "573 Meetings", "1,165 Search Entries", "573 Exported", "Active Token"
- **Animation**: Cards stagger in from bottom (15-frame offset each), counters count up simultaneously
- **Caption**: "Real-time dashboard"

#### Scene 3: Meeting Grid (75 frames / 2.5s)

- **Background**: App shell with sidebar (Meetings nav active)
- **Elements**: 6 meeting cards (3x2 grid) with:
  - Title: "Q4 Product Roadmap Review", "Weekly Engineering Standup", "Client Onboarding Sync", "Sprint Retrospective", "Design System Workshop", "Budget Planning Q1"
  - Date below title
  - 3 badges per card (Notes ✓, Summary ✓, Transcript ✓) — blue for active
- **Animation**: Cards stagger in from left (10-frame offset), badges pop in after card lands
- **Caption**: "573 meetings organized"

#### Scene 4: Search Demo (95 frames / 3.17s)

- **Background**: App shell with sidebar (Search nav active)
- **Elements**:
  1. Search bar with cursor blinking (frames 0-10)
  2. Typewriter effect: "action items from Q4" (~3 frames/char = 54 frames)
  3. Results fade in below (3 result cards with yellow-highlighted snippets)
- **Animation**: Typewriter for query, then results stagger-fade-in with `<mark>` highlights appearing
- **Caption**: "Full-text search across all content"
- **Mock results**: Cards showing meeting titles with highlighted "action items" in snippets

#### Scene 5: Pipeline Exec (80 frames / 2.67s)

- **Background**: App shell with sidebar (Pipeline nav active)
- **Elements**:
  1. "Full Sync" button pulses then activates (frames 0-15)
  2. Progress bar fills from 0% → 75% with step tracker: Export ✓ → Index ✓ → Process ⟳ (frames 15-55)
  3. Terminal log viewer scrolls 4-5 log lines with colored levels (frames 30-80)
- **Animation**: Progress bar smooth fill (interpolate), log lines appear one by one from bottom
- **Caption**: "One-click pipeline execution"
- **Mock logs**: `[INFO] Exported 142 meetings`, `[INFO] Built search index: 1,165 entries`, `[INFO] Processing with Claude AI...`

#### Scene 6: CTA Outro (60 frames / 2s)

- **Background**: `bg-gray-900` (dark) for contrast
- **Elements**:
  - "Built with" text + tech logos/names: Next.js · FastAPI · Claude AI · SQLite
  - App name "Granola Meeting Explorer" centered
  - Optional: GitHub URL or personal site
- **Animation**: Elements fade in with spring, slight scale. Hold for 1 second.
- **Caption**: None

### Design Tokens (`theme.ts`)

Extracted from the existing web frontend components:

```typescript
export const colors = {
  // Backgrounds
  pageBg: '#f9fafb',       // gray-50
  cardBg: '#ffffff',        // white
  terminalBg: '#111827',    // gray-900

  // Text
  textPrimary: '#111827',   // gray-900
  textSecondary: '#6b7280', // gray-500
  textTertiary: '#9ca3af',  // gray-400

  // Borders
  border: '#e5e7eb',        // gray-200
  borderHover: '#93c5fd',   // blue-300

  // Accent / Primary
  primary: '#2563eb',       // blue-600
  primaryDark: '#1d4ed8',   // blue-700
  primaryLight: '#dbeafe',  // blue-100
  primaryText: '#1e40af',   // blue-800

  // Status
  successBg: '#dcfce7',     // green-100
  successText: '#166534',   // green-800
  warningBg: '#fef9c3',     // yellow-100
  warningText: '#854d0e',   // yellow-800
  errorBg: '#fef2f2',       // red-50
  errorText: '#b91c1c',     // red-700

  // Terminal log levels
  logInfo: '#4ade80',       // green-400
  logWarn: '#facc15',       // yellow-400
  logError: '#f87171',      // red-400

  // Search highlights
  highlight: '#fef08a',     // yellow-200

  // Badges
  badgeActiveBg: '#dbeafe', // blue-100
  badgeActiveText: '#1d4ed8', // blue-700
  badgeInactiveBg: '#f3f4f6', // gray-100
  badgeInactiveText: '#9ca3af', // gray-400
} as const;

export const fonts = {
  sans: 'Inter',
  mono: 'JetBrains Mono',
} as const;
```

### Zod Parameter Schema (`schema.ts`)

```typescript
import { z } from 'zod';

export const promoVideoSchema = z.object({
  title: z.string().default('Granola Meeting Explorer'),
  tagline: z.string().default('Export · Index · Search · Enrich'),
  meetingCount: z.number().default(573),
  searchEntries: z.number().default(1165),
  exportedCount: z.number().default(573),
  searchQuery: z.string().default('action items from Q4'),
  accentColor: z.string().default('#2563eb'),
});

export type PromoVideoProps = z.infer<typeof promoVideoSchema>;
```

### Dependencies

```json
{
  "name": "granola-promo-video",
  "private": true,
  "sideEffects": ["*.css"],
  "scripts": {
    "dev": "remotion studio",
    "render": "remotion render PromoVideo out/promo.mp4",
    "render:scene": "remotion render",
    "build": "remotion bundle",
    "upgrade": "remotion upgrade"
  },
  "dependencies": {
    "@remotion/cli": "4.0.429",
    "@remotion/transitions": "4.0.429",
    "@remotion/google-fonts": "4.0.429",
    "@remotion/zod-types": "4.0.429",
    "react": "19.2.3",
    "react-dom": "19.2.3",
    "remotion": "4.0.429",
    "zod": "3.24.2"
  },
  "devDependencies": {
    "@remotion/tailwind-v4": "4.0.429",
    "tailwindcss": "4.2.0",
    "@types/react": "19.2.7",
    "typescript": "5.9.3"
  }
}
```

> **Critical**: All `remotion` and `@remotion/*` packages must be pinned to the exact same version. No `^` prefixes.

### Implementation Phases

#### Phase 1: Project Scaffold + Tailwind (foundation)

**Tasks:**
- [x] Create `video/` directory with `package.json`, `tsconfig.json`, `remotion.config.ts`
- [x] Configure Tailwind v4 via `@remotion/tailwind-v4` in `remotion.config.ts`
- [x] Create `src/index.ts` with `registerRoot()`
- [x] Create `src/Root.tsx` with composition registry (full promo + per-scene compositions)
- [x] Create `src/index.css` with `@import 'tailwindcss'`
- [x] Create `src/lib/theme.ts` with design tokens
- [x] Create `src/lib/animations.ts` with shared spring/interpolation helpers
- [x] Create `src/data/schema.ts` with Zod parameter schema
- [x] Create `src/data/mockData.ts` with all mock content
- [x] Load Inter and JetBrains Mono via `@remotion/google-fonts`
- [x] Add `video/out/` and `video/node_modules/` to `.gitignore`
- [x] Add Makefile targets: `make video-studio`, `make render-video`
- [x] Verify: `npx remotion studio` opens and shows empty composition

**Success criteria:** Studio opens, Tailwind classes render, fonts load, composition displays at 1920x1080.

#### Phase 2: Shared Components + App Shell

**Tasks:**
- [x] Build `AppShell.tsx` — simplified sidebar with 4 nav items, active state via prop
- [x] Build `Caption.tsx` — bottom-positioned text overlay with fade-in animation
- [x] Build `StatCard.tsx` — card with spring-animated counter (interpolate 0→target)
- [x] Build `MeetingCard.tsx` — card with title, date, 3 badge indicators
- [x] Build `SearchResult.tsx` — result card with `<mark>`-style highlighted text
- [x] Build `ProgressBar.tsx` — horizontal bar fill + 3-step tracker (Export→Index→Process)
- [x] Build `TerminalLog.tsx` — dark bg, monospace, color-coded log lines appearing sequentially
- [x] Build `FlowNode.tsx` — circle/rounded-rect with label, spring scale-in
- [x] Build `FlowArrow.tsx` — SVG line that draws left-to-right via `strokeDashoffset`

**Success criteria:** Each component renders correctly in isolation with frame-driven animations (no CSS transitions).

#### Phase 3: Individual Scenes

**Tasks:**
- [x] Build `TitleIntro.tsx` (Scene 0) — title + tagline spring-in
- [x] Build `PipelineFlow.tsx` (Scene 1) — 5 nodes + 4 arrows sequential animation
- [x] Build `Dashboard.tsx` (Scene 2) — AppShell + 4 StatCards staggered
- [x] Build `MeetingGrid.tsx` (Scene 3) — AppShell + 6 MeetingCards staggered
- [x] Build `SearchDemo.tsx` (Scene 4) — AppShell + typewriter + 3 results staggered
- [x] Build `PipelineExec.tsx` (Scene 5) — AppShell + ProgressBar + TerminalLog
- [x] Build `CtaOutro.tsx` (Scene 6) — dark bg with tech stack + app name
- [x] Register each scene as individual `Composition` in `Root.tsx` under a "Scenes" folder

**Success criteria:** Each scene plays correctly in Studio with proper timing, animations feel smooth (no jank), and visual design matches the web app's aesthetic.

#### Phase 4: Full Composition + Transitions + Polish

**Tasks:**
- [x] Build `PromoVideo.tsx` using `TransitionSeries` from `@remotion/transitions`
- [x] Wire all 7 scenes with `fade()` transitions (10 frames each)
- [x] Verify total frame count: exactly 540 frames
- [x] Add captions to scenes 1-5 via `Caption` component
- [x] Fine-tune timing: adjust individual scene allocations if scenes feel rushed/slow
- [x] Visual QA: check color consistency, font rendering, element alignment
- [x] Render final MP4: `npx remotion render PromoVideo out/promo.mp4`
- [ ] Test render at different CRF values for quality vs file size balance

**Success criteria:** Full 18-second video plays smoothly, all transitions are seamless, captions are readable, and the video clearly communicates the app's value proposition to someone who has never seen it.

## Alternative Approaches Considered

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Screen recording of actual app** | Authentic, no coding needed | Requires populated data, hard to control timing, lower quality | Rejected — Remotion gives full control over timing and polish |
| **Static image carousel / GIF** | Simpler to create | No smooth animations, no transitions, feels amateur | Rejected — video is more engaging |
| **Motion Canvas (alternative framework)** | Also React-based, good for motion graphics | Smaller ecosystem, fewer resources, less Tailwind support | Rejected — Remotion has better tooling and existing skill files |
| **After Effects / Premiere** | Industry standard, maximum control | Requires paid software, not code-based, not versionable | Rejected — code-based approach fits developer workflow |
| **20+ second video** | More breathing room per scene | Too long for social media, attention drops | Rejected — 18s is the sweet spot (15s felt too tight after analysis) |

## Acceptance Criteria

### Functional Requirements

- [ ] `video/` directory exists as an isolated Remotion 4.x project with its own `package.json`
- [ ] `npx remotion studio` (from `video/`) opens the Studio and displays all compositions
- [ ] Full "PromoVideo" composition plays for exactly 18 seconds (540 frames @ 30fps)
- [ ] All 7 scenes render with frame-driven animations (zero CSS transitions/animate classes)
- [ ] Tailwind v4 classes render correctly in all scenes
- [ ] Inter and JetBrains Mono fonts load and render correctly
- [ ] `npx remotion render PromoVideo out/promo.mp4` produces a valid MP4 file
- [ ] Zod schema allows customizing title, stats, search query, and accent color via Studio UI
- [ ] Each scene is also registered as an individual composition for standalone preview/render

### Non-Functional Requirements

- [ ] All `remotion`/`@remotion/*` packages pinned to the same exact version
- [ ] No dependencies shared with or imported from `web/frontend/`
- [ ] `video/out/` and `video/node_modules/` are gitignored
- [ ] Makefile targets `make video-studio` and `make render-video` work from repo root

### Quality Gates

- [ ] Video visually matches the web app's design system (colors, typography, spacing)
- [ ] All animations are smooth at 30fps — no jank or abrupt cuts
- [ ] Captions are readable (sufficient contrast, appropriate size, enough display time)
- [ ] The video communicates the app's purpose to someone who has never seen it
- [ ] Rendered MP4 is under 10MB at reasonable quality (CRF 18-23)

## Success Metrics

- Video renders successfully to MP4 without errors
- All 5 feature scenes are visually distinct and clearly represent their respective app features
- A viewer unfamiliar with the app can identify: (1) it manages meetings, (2) it has search, (3) it has an automated pipeline, (4) it uses AI enrichment

## Dependencies & Prerequisites

- **Node.js 16+** on the host (not Docker — Remotion runs locally)
- **npm** for package management
- **FFmpeg** (bundled with `@remotion/cli` or pre-installed)
- **Remotion best practices skill** at `.agents/skills/remotion-best-practices/` (already present, 39 rule files)

## Risk Analysis & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Tailwind v4 + Remotion webpack conflict | Medium | High | Follow exact setup from `@remotion/tailwind-v4` docs; test early in Phase 1 |
| 18s feels too rushed for 7 scenes | Medium | Medium | Individual scene compositions allow easy timeline adjustment; can extend to 20s |
| Font rendering mismatch with web app | Low | Medium | Use exact same Inter weights; validate in Studio before full render |
| Remotion version pinning issues | Low | High | Use `--save-exact` for all installs; run `npx remotion upgrade` to align |
| CSS transition classes accidentally used | Medium | High | Lint rule or manual review; the remotion-best-practices skill explicitly warns about this |

## Future Considerations

- **Audio track**: Add a subtle royalty-free background track via `<Audio>` component
- **Voiceover**: Use ElevenLabs TTS integration (documented in remotion skill)
- **Multi-format**: Add 1:1 (1080x1080) and 9:16 (1080x1920) compositions for social media
- **Dark mode variant**: Create an alternate color scheme composition
- **Live data**: Fetch actual stats from the FastAPI backend at render time via `calculateMetadata`
- **GIF export**: Render a short (6s) teaser as GIF for GitHub README embedding
- **CI rendering**: Add a GitHub Action to auto-render on changes to `video/src/`

## Documentation Plan

- Add a `video/README.md` with setup/render instructions
- Update root `README.md` with a "Promotional Video" section linking to the rendered output
- Add `make video-studio` and `make render-video` to the root Makefile documentation

## References & Research

### Internal References

- Web frontend design system: `web/frontend/src/app/globals.css`, `web/frontend/src/app/layout.tsx`
- Dashboard page (Scene 2 reference): `web/frontend/src/app/page.tsx`
- Meetings page (Scene 3 reference): `web/frontend/src/app/meetings/page.tsx`
- Search page (Scene 4 reference): `web/frontend/src/app/search/page.tsx`
- Pipeline page (Scene 5 reference): `web/frontend/src/app/pipeline/page.tsx`
- Component library: `web/frontend/src/components/` (9 components)
- TypeScript types: `web/frontend/src/types/index.ts`

### Remotion Skill Files

- Master index: `.agents/skills/remotion-best-practices/SKILL.md`
- Compositions: `.agents/skills/remotion-best-practices/rules/compositions.md`
- Animations: `.agents/skills/remotion-best-practices/rules/animations.md`
- Sequencing: `.agents/skills/remotion-best-practices/rules/sequencing.md`
- Timing: `.agents/skills/remotion-best-practices/rules/timing.md`
- Transitions: `.agents/skills/remotion-best-practices/rules/transitions.md`
- Text animations: `.agents/skills/remotion-best-practices/rules/text-animations.md`
- Tailwind: `.agents/skills/remotion-best-practices/rules/tailwind.md`
- Fonts: `.agents/skills/remotion-best-practices/rules/fonts.md`
- Parameters: `.agents/skills/remotion-best-practices/rules/parameters.md`

### External References

- Remotion documentation: https://www.remotion.dev/docs
- Remotion GitHub: https://github.com/remotion-dev/remotion
- Remotion blank template: https://github.com/remotion-dev/remotion/tree/main/packages/template-blank
- @remotion/tailwind-v4: https://www.remotion.dev/docs/tailwind-v4/overview
- @remotion/transitions: https://www.remotion.dev/docs/transitions
- Remotion render CLI: https://www.remotion.dev/docs/cli/render
