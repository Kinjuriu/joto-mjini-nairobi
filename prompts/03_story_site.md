# Prompt 03: the story website

## Goal

Build the first full version of the Joto Mjini story site in `site/`, using the real data and findings from prompts 01 and 02. It follows the structure of NASA Earthdata's "Fanning the Flames" story (`reference/la-fires.stories.mdx`) and the look and rules defined here and in `DESIGN_RULES.md`. It must run locally with `npm run dev`, build to static files with `npm run build`, and be ready for GitHub Pages (do not deploy; do not push).

Read `DESIGN_RULES.md` again now, before writing UI code.

## Copy that comes from the findings

Every sentence with a number must come from `analysis/FINDINGS.md`. Where a finding is missing or low confidence, write the sentence without the number or mark it `[[NUMBER PENDING: F#]]` in the text and list it in `QUESTIONS.md`. Never fill in a number from your own knowledge.

## Tech stack

- **Vite** with vanilla JavaScript (ES modules). No React, no UI framework, no CSS framework, no icon library.
- **MapLibre GL JS** for all maps, with the **pmtiles** protocol for the basemap, raster layers and buildings.
- **Scrollama** for the scrollytelling section (it uses IntersectionObserver and does not take over scrolling).
- **D3** for charts, drawn as hand-built SVG.
- Fonts self-hosted through `@fontsource` packages.
- Pin exact versions of every package at install time and record them in `PROGRESS.md`.
- Vite's dev server supports the HTTP range requests that PMTiles needs. Check the built site with `npx vite preview` as well, and confirm the range requests work.
- Set Vite's `base` so the build works from a GitHub Pages project subpath (for example `/joto-mjini/`), configurable in one place.

## Look and feel (fixed; do not substitute)

**References and why:** NASA Earthdata stories for structure; the Financial Times and New York Times climate graphics for restraint, direct labels and calm typography; AP for plain, factual captions.

**Palette**

- Page background `#F7F4EE` (warm paper), main text `#1C1B19`, secondary text `#4A4740`, hairline rules `#D8D2C6`, links `#1F4E6B` underlined. UI chrome stays neutral; colour belongs to the data.
- Surface temperature (sequential, light to dark): `#FFF5E6`, `#FDD9A8`, `#F9B06A`, `#EE7D3B`, `#D2481E`, `#A3200F`, `#6B0F0A`. Use the same fixed breaks on every surface temperature map.
- Difference from the city median (diverging, neutral midpoint): `#2F6B8F`, `#8CB7CF`, `#ECE8E1`, `#F1A66B`, `#C2401A`.
- Tree cover (sequential green): `#EEF3E6`, `#B9D3A0`, `#6FA36A`, `#2E6B3F`.
- Population (sequential neutral to ink): `#F1EEE8`, `#C9C2B5`, `#8C8475`, `#3E3A33`.
- Check every text and background pair against WCAG AA (4.5:1 for body text), and check the data ramps for colour-blind separation. Record the results.

**Typefaces:** Source Serif 4 for headlines and body text; Source Sans 3 for captions, labels, chart text and controls; tabular numbers for every figure. No Inter, Poppins, Montserrat or system-ui as the primary face.

**Geometry:** square corners (0 to 2 px radius), hairline rules, generous white space, a single reading column of about 680 px for prose, and wide blocks up to about 1200 px for maps.

**Banned:** everything in the banned list in `DESIGN_RULES.md`, including fade-in on scroll, parallax, scroll-jacking, cursor effects, gradients as decoration, stock icons, emoji, bento grids, pie and donut charts, dual axes, and hover-only information.

## Page structure (mirrors the NASA story, in this order)

Each item lists the NASA component it copies and what ours shows.

1. **Masthead.** Project name "Joto Mjini" set as a text wordmark, with the tagline "Mapping urban heat and cooling inequality across Nairobi" in small type beside or below it, and nothing else. One header only; it may stay at the top of the page and must never duplicate.
2. **Title block** (NASA: frontmatter `name` and `description`). Headline that states the main finding in plain English (from FINDINGS F1, F2 or the inequality finding; for example the gap in °C between the hottest and coolest places on hot days). Working frame for the headline: "Nairobi's heat divide". Offer three alternative headlines in `site/SITE_REPORT.md` for Stephane to choose from. Subtitle that defines the measure ("Land surface temperature measured by the Landsat 8 and 9 satellites on clear mornings, January to March, 2023 to 2026"). Byline: "By Stephane [surname], data analyst, Nairobi" as a placeholder Stephane will edit; a line "Published [date]" and "Last updated [date]".
3. **Hero compare map** (NASA: wide `Map` with `compareDateTime`). A wide swipe map of Nairobi with streets and labels: the left side shows hot-season surface temperature, the right side shows cool-season surface temperature on the same scale. The swipe handle is a plain vertical rule with a square grip, operable by mouse, touch and keyboard (arrow keys). Caption with sources underneath. On the first screen, without scrolling, the reader must see the headline, the subtitle and at least the top of this map.
4. **Section: "Nairobi's hottest ground"** (NASA: `Prose` with H3). Two or three short paragraphs: what the map shows, where the hottest and coolest places are, the size of the gap. Then a short boxed note "Surface temperature or air temperature?" explaining the difference in four sentences.
5. **Figure and text side by side** (NASA: `Block` with `Figure` and `Prose`). Chart: average surface temperature for each band of tree cover (from `lst_by_tree_band.csv`), with the spread shown, direct labels, title, subtitle, source and date. Text beside it explains the finding.
6. **Chart with a highlighted period** (NASA: `Chart` with `highlightStart` and `highlightEnd`). Daily maximum air temperature for Nairobi from 2023 to now, from `daily_air_temp_2023_now.csv`, with the El Niño months since May 2026 shaded and labelled "El Niño, 2026". Explain in two paragraphs that this is a city-wide air temperature from a weather model, how much it swings from day to day, and that this phase of the story focuses on heat; rainfall and El Niño come later.
7. **Scrollytelling map** (NASA: `ScrollytellingBlock` with `Chapter`s, each setting `center`, `zoom` and a layer). One sticky map with text chapters scrolling past it. When a chapter becomes active, the map moves to its place and shows its layer. Movement is a short `flyTo` (about 1.5 s); under `prefers-reduced-motion` use `jumpTo`. Chapters, in order:
   1. **The whole city.** County view, hot-season surface temperature, ward outlines.
   2. **The centre and Industrial Area.** Zoom in, hot-season layer, key numbers from the findings.
   3. **Where most people live.** Eastlands and the dense settlements, population layer, then surface temperature, with the exposure finding (F4). Neutral, respectful wording; see the ethics rules in `CLAUDE.md`.
   4. **Islands of cool.** Karura Forest and the Arboretum, tree cover layer, then the park-ring finding (F5) if it is solid.
   5. **Leafy and dense, side by side.** Two neighbourhoods with contrasting tree cover, for example Kileleshwa or Lavington against a nearby dense area; anomaly layer.
   6. **A growing city.** GHSL built-up area in two epochs (switch layers between two steps), with the growth finding (F6).
   7. **Back to the whole city.** Wards coloured by population-weighted surface temperature, leading into the explorer.
   Every chapter card carries the key number as text, so nothing depends on the map alone. On narrow screens the map sits above each card in normal flow, so the page stays readable.
8. **Wide compare map** (NASA: second wide `Map` with `compareDateTime`). Built-up area in the earliest and latest GHSL epochs, same swipe control as the hero.
9. **Section: "How a satellite reads heat"** (NASA: the HLS and TEMPO explainer sections). Plain explanation of the Landsat thermal sensor, the morning overpass, clouds, the 100 m resolution, and why we chose January to March. One small static diagram drawn in SVG if it truly helps; otherwise none.
10. **The explorer: "Find your ward"** (NASA: the interactive maps near the end). A wide interactive map with:
    - layer buttons (a standard segmented control with visible text labels): Surface temperature (hot season), Difference from the city median, Tree cover, People, Buildings by surface temperature;
    - a ward selector: a searchable, keyboard-accessible list of all wards; choosing one zooms to it and fills the ward panel;
    - a ward panel that always shows the selected ward's numbers as text: median surface temperature, difference from the city median, rank out of all wards, population, tree cover share, built-up share;
    - click or tap on the map selects the ward under the pointer; hover may show a small tooltip as a convenience only;
    - a legend with value breaks and units, directly labelled;
    - the current view written into the URL hash (layer and ward) so a view can be shared.
    Before any interaction, the panel shows the county overview and the five hottest wards.
11. **What this means for cooling.** Short closing section: what the findings suggest about trees, shade and roof materials, written carefully as what the data shows and does not show, with links to WRI Cool Cities Lab and other credible cooling resources found in prompt 01. No recommendations beyond the evidence.
12. **Methods, data and credits** (NASA: author block and captions). Data sources with licences and citations from `data/SOURCES.md`; method summary; "What the data cannot tell us" from FINDINGS; how to cite this story; code repository placeholder; acknowledgements, including the workshop hosts as context only (do not imply endorsement). Every map and chart above also has its own source line and date.

## Behaviour rules

- Native scrolling throughout. Content is present on arrival; nothing fades or slides in.
- The only motion: map moves between chapters, layer changes (fade of 200 ms or less), and chart transitions when data changes. All off under reduced motion.
- A thin, static reading progress bar at the top is allowed.
- Without JavaScript, the page still reads well: the title, all prose, static PNG versions of the hero map and key charts (from `outputs/figures/`), and the top-wards table in plain HTML. JavaScript then replaces the static images with live maps.
- Keyboard: every control reachable and visibly focused; the swipe handle moves with the arrow keys; Escape closes the ward list.
- Phones: test at 375 px wide; the map controls stay usable; nothing important needs hover.
- Performance: before map tiles load, the page should be under about 3 MB. Load maps further down the page only when they come near the screen.
- Attribution on every map: "© OpenStreetMap contributors" plus each data source, in the MapLibre attribution control and the caption.

## Report

Write `site/SITE_REPORT.md` containing:

1. Every effect, animation and interaction in the site, each with one line on why a human designer would have spent real time hand-coding it (the hand-coding test). Remove anything that fails.
2. Package versions.
3. Contrast and colour-blind check results.
4. Any `[[NUMBER PENDING]]` markers left in the copy.
5. Things you are unsure about.

Update `PROGRESS.md` and commit "Phase 3: story site".

## If time remains (optional, in this order)

1. A print-friendly stylesheet so the story prints cleanly for the workshop.
2. A `slides.html` page with eight full-screen static slides (title, the gap, land cover chart, exposure, cool islands, growth, the explorer screenshot, sources) for Stephane's presentation, using the same palette and type.
