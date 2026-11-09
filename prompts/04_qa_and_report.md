# Prompt 04: QA and the morning report

## Goal

Check the work like a careful human reviewer, fix what you can, and leave Stephane a short, honest report she can read with her morning coffee.

## 1. Automated checks

1. Install Playwright for Node in `site/` (`npm i -D @playwright/test`, then `npx playwright install chromium`).
2. With the built site served by `npx vite preview`, take full-page screenshots at 375 px and 1440 px wide, plus screenshots of each scrollytelling chapter and the explorer with one ward selected. Save them to `outputs/screenshots/` with clear names.
3. Record any browser console errors and failed network requests (especially PMTiles range requests). Fix them.
4. Run every notebook top to bottom with `jupyter nbconvert --execute` and fix failures.
5. Run a link check on every external link in the site and in `data/SOURCES.md`.

## 2. Human-eye checks (look at your screenshots; do not skip this)

- Does the first screen show the headline finding, the subtitle and the start of the hero map at both widths?
- Are labels colliding, cut off or overlapping the data? Are legends readable?
- Do the cool places look cool and the hot places look hot? If not, the data or the colour breaks are wrong.
- Is any text low contrast or too small on the phone width?
- Does anything move that should not, or appear twice (headers, captions)?
- Read every sentence of the copy aloud in your head. Remove em dashes, "not X, but Y" constructions, hype words and anything that sounds like a template. Check that each number matches `analysis/FINDINGS.md` exactly.

## 3. Pre-ship checklist (from Stephane's full guide)

Copy this list into `site/SITE_REPORT.md` and tick each item honestly, with a note for any item that fails:

- [ ] Palette and typefaces are exactly those set in prompt 03, and nothing else
- [ ] Every effect passes the hand-coding test, with a one-line reason
- [ ] Nothing from the banned list remains
- [ ] Hover only makes clickable things more inviting; nothing disappears on hover
- [ ] Nothing important is reachable only by hover
- [ ] Native scrolling; no reveal animations; one header state at a time
- [ ] Body text meets WCAG AA contrast
- [ ] No stock icons or emoji in the interface
- [ ] All images are sharp and match their content
- [ ] The first screen states the key finding, defines the measure and shows the hero map
- [ ] Every chart and map has a title, subtitle, source and date
- [ ] Works at 360, 768, 1280 and 1600 px
- [ ] Keyboard-only use and reduced motion both work
- [ ] Works with JavaScript off at its default state

Note in the report that the final item on Stephane's list, "a human has QA'd every page and every interaction", is hers to do.

## 4. Presentation outline

Write `docs/presentation_outline.md`: a 10-minute talk for the workshop in Stephane's preferred Context, Action, Metric, Impact structure:

- **Context:** what heat means for Nairobi and who carries it (one slide).
- **Action:** what she built, with which open data, and how (two slides).
- **Metric:** the three strongest findings from `analysis/FINDINGS.md`, one per slide, with the chart or map for each.
- **Impact:** what a county planner, an NGO or a school could do with the explorer, and what comes next (rainfall, flooding and El Niño).
- A closing slide with the link placeholder and data credits.

Use only numbers from FINDINGS. Plain English, no em dashes.

## 5. `MORNING_REPORT.md`

Keep it under two screens. Use these headings:

1. **Status in one paragraph.** What works, and how to open it (`cd site && npm run dev`, then the local URL).
2. **What got done,** phase by phase, with the key files.
3. **The findings,** listed with their numbers and confidence, copied from FINDINGS.
4. **What failed or was cut,** with the exact errors and the commands to retry.
5. **Decisions I made for you,** the short list from `DECISIONS.md` that matters most.
6. **Questions for you,** from `QUESTIONS.md`, most important first.
7. **Suggested next run,** the three most valuable things to do next.
8. **Time used** per phase.

Then update `PROGRESS.md`, commit "Phase 4: QA and morning report", and stop.
