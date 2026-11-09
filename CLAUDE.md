# CLAUDE.md: project rules for Joto Mjini

Read this file in full at the start of every session. It overrides your defaults.

## What this project is

**Joto Mjini** (Swahili for "heat in the city"), subtitle "Mapping urban heat and cooling inequality across Nairobi", is a data story about urban heat in Nairobi, Kenya. It maps which parts of the city get hottest on hot days, who lives there, and how trees, open ground and roofs relate to that heat. It ends with an interactive map where anyone can find their own ward and compare it with cooler parts of the city.

- **Owner:** Stephane, a data analyst and researcher based in Nairobi. She writes Python and reads code, and she will review everything you produce in the morning.
- **Reviewer:** Tony Widjarnaso, a colleague with urban analysis experience, may review the work later. Never write that he has reviewed anything; that is for Stephane to add once it happens.
- **Deadline:** Stephane plans to present this at the Earthna and CIFF workshop "Land, Food and Heat Resilience in Africa's Arid Regions", Sankara Hotel, Nairobi, Thursday 26 November 2026. See `reference/workshop_brief.md`.
- **Phase 1 (now): heat only.** Rainfall, flooding and the El Niño link come in a later phase. Keep the pipeline general enough to add them, but do not build them now.
- **Model story:** NASA Earthdata's "Fanning the Flames: Unraveling the Causes of the 2025 Los Angeles Area Wildfires". Its full source is in `reference/la-fires.stories.mdx`, and `reference/README.md` explains how to read it. Our story copies its structure (author block, wide compare map, short sections with H3 headings, figure and text side by side, charts with a highlighted period, a scrollytelling map that flies between places, a full interactive map near the end, captions with attribution on every visual). We do not copy its look; our look comes from `DESIGN_RULES.md` and `prompts/03_story_site.md`.

## Audience

1. Workshop practitioners: county and city government staff, NGOs, researchers and funders working on urban heat and cooling in Africa. They know the topic and want evidence they can act on.
2. Nairobi residents and LinkedIn readers who have heard about heat but have never read a satellite image.

Write for the second group and make sure the first group finds nothing wrong.

## Golden rules for unattended work

You are often running overnight with nobody watching. So:

1. **Never stop to ask a question.** When something is unclear or blocked, write the question in `QUESTIONS.md`, choose the most reasonable option, record the choice and the reason in `DECISIONS.md`, and carry on.
2. **Keep `PROGRESS.md` current.** After every milestone, add a dated line (local time, Africa/Nairobi) saying what finished, what files it produced, and what is next. If your context is reset, read `PROGRESS.md`, `DECISIONS.md` and `QUESTIONS.md` first and resume from where they say.
3. **Commit locally after every milestone** with a clear message. Never run `git push`, never add or change a remote, never force anything, never rewrite history.
4. **Never delete files.** If something must go, move it into `data/_trash/` or `_trash/` and note it in `PROGRESS.md`.
5. **Fail soft.** If one dataset or step fails after two honest attempts, use the documented fallback, log it in `DECISIONS.md`, and move on. One broken source must not stop the night.
6. **Log long jobs** to `logs/` with timestamps, so Stephane can see what ran.
7. **Secrets:** read credentials only from `.env` through code. Never print, log, commit or echo them.

## Data honesty rules (non-negotiable)

- Satellites measure **land surface temperature**: how hot the ground, roofs and roads are. That is different from the air temperature people feel. Always label it "surface temperature" or "land surface temperature" and explain the difference once in the story. Never call it air temperature.
- Landsat's thermal sensor measures at about 100 m and the product is delivered on a 30 m grid. Never imply detail finer than 100 m. Building-level values are the surface temperature of the 100 m area around the building, and the story must say so.
- **Every number in the story must trace back to a script, a file and a source.** Record each one in `analysis/FINDINGS.md` with the file and script that produced it.
- **Never invent, simulate or "illustrate" data.** If a dataset cannot be fetched, the site shows a clearly marked placeholder ("Data pending: [dataset]"), never fake values.
- Do not overclaim. Correlation is not cause; say "areas with more trees were cooler" and do not say "trees cooled the area by X" unless the method supports it.
- Record every dataset in `data/SOURCES.md`: name, provider, URL, licence, resolution, dates covered, date accessed, and the exact citation the provider asks for.

## Ethics

- Dense and informal settlements (for example Kibera, Mathare, Mukuru) may show up as hot and highly exposed. Frame this as exposure and lack of cooling infrastructure, never as the residents' fault. Use neutral names and the residents' own place names. No individual-level or household data.
- Aggregate to wards, 100 m cells or buildings. Never single out an individual property owner.

## Writing rules (for every word a reader sees, and for reports to Stephane)

- Plain, simple English. Tell the story in one clear order and finish one idea before starting the next; do not jump between time periods or mix ideas inside one sentence.
- No em dashes anywhere. Use commas, semicolons, colons or full stops instead.
- No "not X, but Y" constructions.
- No hype words (revolutionary, groundbreaking, unlock, game-changing, harness, delve, tapestry).
- Short headings that state a finding or a question, in sentence case.
- Numbers: one decimal place for temperatures in °C, thousands separators for people counts, and always the unit.

## Design rules

`DESIGN_RULES.md` is mandatory for any UI. Read it before writing UI code. The palette, typefaces and layout for this project are fixed in `prompts/03_story_site.md`; do not substitute your own.

## Environment

- macOS on Apple Silicon, VS Code, Claude Code. Stephane's local time zone is Africa/Nairobi (UTC+3).
- Python: use `uv` (install with `brew install uv` if missing) with a project `.venv` and a `pyproject.toml`. Pin versions in the lock file.
- Node: use npm for the site in `site/`. Pin exact versions.
- Projection for analysis: UTM zone 37S (EPSG:32737). Web output: EPSG:3857 tiles, EPSG:4326 GeoJSON.

## Folder layout

```
CLAUDE.md               these rules
DESIGN_RULES.md         Stephane's no-vibe-coding rules (mandatory for UI)
README.md               human overview and how to run
PROGRESS.md             running log (you create and update it)
DECISIONS.md            choices you made and why
QUESTIONS.md            questions for Stephane
MORNING_REPORT.md       end-of-run summary (prompt 04)
prompts/                the task prompts, run in order 00 to 04
reference/              NASA story source, workshop brief, notes
docs/                   application draft, naming, presentation outline
src/                    Python pipeline (source of truth)
notebooks/              narrative notebooks that import from src/
data/raw/               downloads (git-ignored)
data/interim/           clipped and cleaned rasters (git-ignored)
data/processed/         small final outputs used by the site (committed if < 50 MB each)
data/SOURCES.md         every dataset with licence and citation
analysis/FINDINGS.md    every number used in the story, with provenance
outputs/figures/        static figures for slides and fallbacks
site/                   the story website (Vite, vanilla JS)
logs/                   long-job logs
```
