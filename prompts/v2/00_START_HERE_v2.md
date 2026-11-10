# Prompt v2-00: rebuild Joto Mjini Nairobi as a NASA-style story dashboard

You are running unattended, overnight, on Stephane's laptop. Follow `CLAUDE.md` exactly: never stop to ask, log questions in `QUESTIONS.md` and choices in `DECISIONS.md`, fail soft, commit locally after each milestone, never push, never delete (move to `_trash/`).

## What happened so far

Version 1 is built and committed: a data pipeline, 15 findings in `analysis/FINDINGS.md`, and a story site in `site/`. Stephane reviewed it this morning. The analysis is careful, but the site does not look the way she wants: the maps look blocky and too red, place and ward names are hard to read, and the map sits in half the screen. She wants the site rebuilt to look and behave like NASA Earthdata's "Fanning the Flames" story dashboard, with crisp maps, satellite and vegetation views, animated maps, heatmap tables, and a full explorer. A reviewer also found data problems that must be fixed first.

## Read first (about 20 minutes)

1. `CLAUDE.md`, `DESIGN_RULES.md`, `MORNING_REPORT.md`, `DECISIONS.md`, `QUESTIONS.md`, `analysis/FINDINGS.md`.
2. `reference/screenshots/README.md`, then **open and look at every image** in `reference/screenshots/nasa/` and `reference/screenshots/ours_v1/`.
3. `prompts/v2/DESIGN_BRIEF_v2.md` in full. It overrides the look and layout parts of `prompts/03_story_site.md`.
4. All six chunk prompts in `prompts/v2/`, before writing code.
5. Add one line to `CLAUDE.md` under "Design rules": "From v2 on, `prompts/v2/DESIGN_BRIEF_v2.md` defines the look and layout; where it conflicts with `prompts/03_story_site.md`, the v2 brief wins." Commit "v2: start".

## Build, do not write

Stephane's instruction: **focus on building, not on writing the article.** Use existing FINDINGS sentences in cards and mark other text `[[COPY: ...]]`. Spend the time on maps, layers, animations, charts and interaction.

## The chunks, in order

Each chunk ends in a working site, screenshots in `outputs/screenshots/v2/<chunk>/`, a `PROGRESS.md` entry and a commit "v2 chunk N: ...". Do them in this order. If a chunk runs far over its budget, finish its "must" list, log the rest as not done, and move on, so every chunk gets attention.

| Chunk | Prompt | Budget | Must produce |
|---|---|---|---|
| 1 | `chunk1_data_fixes.md` | 1.5 h | Official ward boundaries, fixed comparison areas, roof emissivity check, analysis re-run |
| 2 | `chunk2_map_engine_and_layers.md` | 2.5 h | Mapbox engine, Sentinel-2 true and false colour, new heat, land cover, population, growth and building layers as XYZ tiles, a layer test page |
| 3 | `chunk3_scrollytelling_story.md` | 2.5 h | The intro and the full-screen, card-over-map story with chapters and transitions |
| 4 | `chunk4_animations_and_heatmaps.md` | 2.5 h | Animated maps (MP4, WebM, GIF, poster), heatmap tables, the highlighted-period chart, wired into the page |
| 5 | `chunk5_explorer_dashboard.md` | 2 h | The explorer at the bottom: layer panel, legend cards, date selector, swipe compare, ward search and panel |
| 6 | `chunk6_qa_and_handover.md` | 1 h | QA against the NASA screenshots, fixes, `MORNING_REPORT_v2.md` |

## If the Mapbox token is missing

Check whether `site/.env.local` exists and defines `VITE_MAPBOX_TOKEN` (check that the variable is set without printing its value, for example with a small script that prints only "set" or "missing"). If it is missing, do chunk 1, the data and tile-building parts of chunk 2, and all of chunk 4 (animations and heatmaps do not need the token). Then write `MORNING_REPORT_v2.md` explaining that the map chunks wait for the token, and stop. Do not switch to another map provider on your own.

## Tools note

`ffmpeg` is not on the approved command list. Make videos and GIFs from Python (`imageio` with `imageio-ffmpeg`, or matplotlib's animation writer), which runs under the approved `python` and `uv` commands.

## Stop condition

Stop when `MORNING_REPORT_v2.md` is complete (chunk 6) and committed.

## Project name change (do this in chunk 2, before building pages)

Stephane renamed the project to **Joto Mjini Nairobi**. Use that name everywhere a reader sees it: the masthead, page titles, credits and source lines ("analysis: Joto Mjini Nairobi"), animation credits, the manifest, slides and reports. Set Vite's `base` to `/joto-mjini-nairobi/` (this will also be the GitHub repository name). Keep the folder name `joto-mjini` on disk. If any `.venv` command fails with a bad path, run `uv sync` to repair it.
