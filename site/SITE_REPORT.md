# Site report: Joto Mjini story, first version

Built 10 November 2026 (overnight run 1). Run with `cd site && npm run dev` (http://localhost:5173/joto-mjini/), or `npm run build && npx vite preview` (http://localhost:4173/joto-mjini/). The GitHub Pages subpath is set in one place, `BASE` in `site/vite.config.js` (override with `SITE_BASE=/`).

## How numbers get into the copy

Every number in `index.html` is a placeholder such as `{{q2.gap_c|c}}`. At build time a small Vite plugin (`findingsNumbers` in `vite.config.js`) fills it from `analysis/results.json`, the same file that `analysis/FINDINGS.md` is generated from. An unknown path or format stops the build. The top-wards table is filled the same way from `analysis/tables/top_wards.csv`. No number in the copy is typed by hand, apart from fixed method facts (80 % clear, 30 m, 100 m, 2 m above ground, 3 °C threshold for day-to-day swings, 700 to 1,000 m rings), which match the method in FINDINGS.

## Headline options

Current headline (from F3): **"On hot mornings, central Nairobi's ground is 12.8 °C hotter than its forests"**, with the kicker "Nairobi's heat divide".

Alternatives:
1. "People in Nairobi's hottest wards live on ground 4.4 °C hotter, with a tenth of the tree cover" (F8; the inequality finding, closest to the subtitle "cooling inequality").
2. "Where Nairobi has trees, its ground is up to 8.4 °C cooler on hot mornings" (F4, tree band 0 to 10 % against 90 to 100 %; association only).
3. "Nairobi's heat divide: 12.8 °C between the city centre and Karura Forest" (F3; shorter, for social media).

## 1. Every effect and interaction, with the hand-coding test

| Effect or interaction | Why a designer would spend real time building it |
|---|---|
| Hero swipe map (hot season against cool season) | The comparison is the point of the section: the same places stay hot in both seasons. Copied from NASA's compare map. Handle is a plain 2 px rule with a square grip, operable by mouse, touch (pointer events) and keyboard (arrow keys, Shift for bigger steps, Home and End), with `role="slider"` and value text. |
| Second swipe map (built-up 1990 against 2020) | Shows where the city grew; a side-by-side pair would halve the map size. |
| Scrollytelling map with nine chapters | Moves the reader through specific places, as in NASA's story. Native scrolling; Scrollama only reports which card is under the trigger line, with a scroll-position fallback so a fast jump never leaves the wrong layer showing. Each card carries its key number as text. |
| `flyTo` between chapters (1.5 s) | Keeps the reader oriented between places; replaced by an instant `jumpTo` under `prefers-reduced-motion`. |
| Raster layer change | Instant switch. MapLibre's raster opacity transition is set to 200 ms or 0 under reduced motion; in practice, layers swap as tiles arrive. |
| Explorer layer buttons (segmented control) | Standard radio group with visible text labels; arrow keys move between options. Needed to compare heat, trees and people on one map. |
| Searchable ward list (combobox) | 85 wards are too many for a plain list; type to filter, arrow keys, Enter, Escape closes. |
| Ward panel | All numbers for the chosen ward as text; never depends on hover. Shows the county overview and five hottest wards before any interaction. |
| Click or tap on the map selects a ward | Direct and expected on a map. |
| Hover tooltip on the explorer map (ward name and median) | Convenience only; the same values are in the panel after a click or tap, and in the list. |
| URL hash with layer and ward | Lets Stephane share a specific view during the workshop. |
| Chart tooltips (tree bands, daily air temperature) | Read exact values. Reachable by hover, tap and keyboard (tree bands are focusable; the air temperature chart takes arrow keys). Key numbers are already in the text and direct labels. |
| Reading progress bar (3 px, static) | Allowed by DESIGN_RULES for long stories; shows how far through the story the reader is. |
| Hover on links, buttons and the swipe grip | Only makes the element more inviting (darker link, thicker underline, white button, thicker grip border). Nothing fades or hides. |
| Lazy loading of maps and charts near the screen | Keeps the first load at about 1.5 MB before map tiles. Not visible to the reader. |

Removed or never built: fade or slide reveals, parallax, sticky header, animated arrows, icons, emoji, gradients, map pitch and rotation, autoplay.

## 2. Package versions (exact, from `site/package.json`)

- maplibre-gl 6.17.0, pmtiles 4.5.0, @protomaps/basemaps 5.7.2, scrollama 3.2.0, d3 7.9.2
- @fontsource/source-serif-4 5.3.1, @fontsource/source-sans-3 5.3.1
- vite 8.3.7, @playwright/test 1.65.0 (dev)
- Node 26.13.0, npm 11.20.0
- Basemap: Protomaps build 20261109 (basemap schema 4.15.2), with self-hosted glyphs (Noto Sans, SIL OFL) and sprites (light, MIT-derived) from `protomaps/basemaps-assets` in `public/basemap-assets/`, so the maps work offline once the site is loaded locally.

## 3. Contrast and colour-blind checks

WCAG 2 contrast ratios (computed, not estimated):

| Pair | Ratio | Result |
|---|---|---|
| Main text #1C1B19 on paper #F7F4EE | 15.68:1 | pass AA |
| Secondary text #4A4740 on paper | 8.44:1 | pass AA |
| Links #1F4E6B on paper | 8.10:1 | pass AA |
| Secondary text on note box #EFEBE3 | 7.79:1 | pass AA |
| Selected button text #F7F4EE on #1C1B19 | 15.68:1 | pass AA |
| Main text on white input #FFFFFF | 17.21:1 | pass AA |
| Text on El Niño shading #ECE8E1 | 14.09:1 | pass AA |
| Hairline rules #D8D2C6 on paper | 1.37:1 | decorative only; never the sole carrier of meaning |

Colour ramps, run through the dataviz skill's palette validator (`validate_palette.js`, light mode, surface #F7F4EE). Its categorical checks (lightness band, chroma floor) do not apply to sequential ramps; the relevant result is the separation between neighbouring steps for colour-blind readers:

| Ramp | Worst adjacent colour-blind ΔE | Notes |
|---|---|---|
| Surface temperature (7 steps) | 8.4 (deutan), between #FFF5E6 and #FDD9A8 | Passes the target of 8, just. The two lightest steps are close for everyone (normal-vision ΔE 8.7). The lightest step is almost the page colour (1.02:1), so legend swatches have hairline borders and the map sits on a grey basemap. |
| Difference from median (5 steps) | 16.2 (protan) | Good. |
| Tree cover (4 steps) | 12.4 (protan) | Good; lightest step close to paper. |
| Neutral / population (4 steps) | 13.3 (deutan) | Good; the grey basemap reduces contrast for the lightest steps, so the built-up maps use only the three darker steps. |

The palette is fixed by prompt 03, so I did not change it. For a second run, Stephane may want to drop or darken `#FFF5E6`.

## 4. `[[NUMBER PENDING]]` markers

None. Every number resolved from `analysis/results.json`. The byline, publication date, last-updated date, citation URL and repository link are deliberate placeholders in square brackets for Stephane: "Stephane [surname]", "Published [date]", "Last updated [date]", "[URL]", "[repository link]".

## 5. Things I am unsure about

- **Narrow-screen scrollytelling.** Prompt 03 asks for the map "above each card in normal flow" on narrow screens. I kept one map, sticky at the top 46 % of the screen, with the cards scrolling underneath it (it is not a header and nothing else is sticky). Moving one live map into each card would reload it each time; nine separate maps would be heavy on a phone. Please check this on a real phone.
- **Swipe maps on phones.** Both swipe maps use MapLibre's cooperative gestures (two fingers to move the map, Ctrl or Cmd and scroll to zoom on desktop) so the page scrolls normally with one finger. This shows a short MapLibre hint when someone tries one finger. Standard, but check that it does not annoy.
- **Building colours.** Each footprint has the surface temperature of the 30 m cell at its centre, and the sensor sees about 100 m, so neighbouring buildings share a value. The legend says "land surface temperature of the area around each building". At zoom 12 and 13 only the larger footprints are kept (tippecanoe); all footprints appear from zoom 14.
- **"Leafy and dense, a short walk apart".** Kileleshwa and Kawangware do not share a boundary; they are 1.3 km apart at the nearest point, which the card says. Lavington and Kawangware do touch, but Lavington is inside Kileleshwa ward, so ward numbers cannot separate it.
- **Basemap labels** come from OpenStreetMap and include some estate names in capitals (Protomaps style). The place names are the residents' own, but a few are small or overlap at mid zooms.
- **The surface temperature colour scale clamps** values below 24 °C and above 48 °C to the end colours (legend shows boundaries 28 to 44). This keeps every surface temperature map comparable.
- **The El Niño shading** uses #ECE8E1, the neutral midpoint of the diverging ramp, so it reads as background, not data.
- **Hosts' names** appear once, in Acknowledgements, with "The hosts did not commission or review this work."

## 6. QA results (Phase 4)

Automated checks with Playwright 1.65.0 against `npx vite preview` (scripts `site/qa/shoot.mjs` and `site/qa/widths.mjs`; screenshots in `outputs/screenshots/`, raw report `outputs/screenshots/qa_report.json`):

- Browser console: no errors and no warnings other than Chromium's headless "GPU stall due to ReadPixels" performance notice.
- Failed requests: none apart from `net::ERR_ABORTED` on PMTiles requests, which is MapLibre cancelling tiles that are no longer needed after the map moves.
- PMTiles range requests: the preview server answers `Range: bytes=0-16383` with `206 Partial Content` for every archive.
- First load before map tiles: about 1.5 MB (fonts, scripts, styles, GeoJSON, CSV), under the 3 MB budget.
- No horizontal overflow at 360, 768, 1280 and 1600 px (one overflow at 360 px from the top-wards table was fixed).
- Keyboard: the hero swipe handle moved from 50 to 30 with ten Left Arrow presses at both widths; typing "Viwand" and Enter in the ward list selected Viwandani; the URL hash became `#layer=buildings&ward=NBO-081` after choosing the buildings layer.
- Reduced motion: the page scrolls through every chapter with `reducedMotion: 'reduce'` with no errors; chapter moves use `jumpTo`, layer fades are 0 ms.
- JavaScript off: title, prose, static hero map, static charts and the top-wards table all show; explorer controls and JavaScript-only instructions are hidden.
- Both notebooks re-executed top to bottom with `jupyter nbconvert --execute` (log `logs/notebooks_phase4.log`).
- Links: 39 external links checked (`outputs/qa/link_check.md`); 34 respond, the 5 others are explained there (publishers blocking bots, one checker artefact, one API endpoint).
- Copy: no em dashes, no "not X, but Y", no hype words in the site, FINDINGS, SOURCES or reports. Every number in the built page (61 distinct values) appears in `analysis/FINDINGS.md`, apart from a licence version (4.0) and a DOI fragment.

Human-eye review of the screenshots (by me; Stephane should repeat it):

- The first screen shows the headline, the subtitle and the top of the hero map at 360, 375, 768, 1280, 1440 and 1600 px.
- Cool places look cool (Karura, the Arboretum, Karen, Ngong Road Forest) and hot places look hot (Industrial Area, Embakasi, Ruai).
- Fixed during review: legend labels ran together ("under 2828"); built-up maps were too faint; chapters 2 and 7 could keep the previous layer after a fast jump; the "June to August" label covered the zoom buttons on phones; a table overflowed at 360 px.
- Remaining: on phones the first lines of a chapter card pass under the sticky map before the card becomes active; basemap labels sometimes crowd at mid zooms; in the no-JavaScript view the static hero image repeats its own title under the page headline.

## 7. Pre-ship checklist (from Stephane's full guide)

- [x] Palette and typefaces are exactly those set in prompt 03, and nothing else. Note: the basemap uses Protomaps' grayscale flavour with Noto Sans labels inside the map tiles, and the note box background #EFEBE3 is a tint between the paper and the hairline colour. Chart and map data colours are only the fixed ramps.
- [x] Every effect passes the hand-coding test, with a one-line reason (section 1).
- [x] Nothing from the banned list remains (no gradients, glows, reveals, parallax, scroll-jacking, cursor effects, icon sets, emoji, bento grids, pie or donut charts, dual axes, hover-only information). MapLibre's own zoom buttons are drawn by the library, not an icon set.
- [x] Hover only makes clickable things more inviting; nothing disappears on hover.
- [x] Nothing important is reachable only by hover (ward panel after click or tap; chart values by tap and keyboard; key numbers in text).
- [x] Native scrolling; no reveal animations; one header state at a time (the masthead is not sticky; only the scrollytelling map is sticky).
- [x] Body text meets WCAG AA contrast (section 3).
- [x] No stock icons or emoji in the interface.
- [x] All images are sharp and match their content (static figures rendered at 200 dpi from the same data).
- [x] The first screen states the key finding, defines the measure and shows the hero map.
- [x] Every chart and map has a title, subtitle, source and date. Note: the two swipe maps and the scrollytelling map carry title and date in the caption rather than above the map.
- [x] Works at 360, 768, 1280 and 1600 px (screenshots `width_*`).
- [x] Keyboard-only use and reduced motion both work (see QA results). Not tested with a screen reader.
- [x] Works with JavaScript off at its default state (`no_javascript_1440.png`).
- [ ] A human has QA'd every page and every interaction. **This one is Stephane's to do.**

---

# v2 (10 November 2026): NASA-style story dashboard

Sections 1 to 7 above describe v1 (kept in `site/_v1/`). This part describes v2. Look and layout: `prompts/v2/DESIGN_BRIEF_v2.md`.

## v2 effects and the hand-coding test

| Effect | Kept? | Reason |
|---|---|---|
| Full-screen sticky map with cards scrolling over it | Yes | The map gets the whole screen, as in NASA's story; native scrolling, nothing is hijacked. |
| flyTo between neighbouring chapters (1.8 s), cross-fade of layers (400 ms) | Yes | Shows the reader where they are going and what changed; jumps and reduced motion move instantly. |
| Animated maps that play by themselves | Yes, agreed exception (D37) | Moving satellite mornings show "the same places, morning after morning" faster than any static figure; muted, on-screen only, Pause/Play, poster under reduced motion. |
| Swipe compare | Yes | Direct comparison of two seasons or layers in the same place; mouse, touch and arrow keys. |
| Built-up year player in the explorer | Yes, paused by default | Steps through six real epochs; the reader starts it. |
| Legend "i" buttons, calendar and table read-outs | Yes | Tap, click and keyboard; nothing is hover-only. |
| Reading progress bar | Yes | Allowed exception in DESIGN_RULES.md. |

## v2 QA results (chunk 6)

- **Build:** `npm run build` works. The only warning was Mapbox GL's own bundle (1.9 MB minified, 528 kB gzipped); the warning limit is now 2,000 kB. Built site 302 MB, of which tiles are 245 MB (about 37,000 files, none over 500 kB) and media 35 MB.
- **Whole page, scrolled slowly at 375 and 1440 px** (`site/qa/v2_full.mjs`): no console errors, no failed requests, 0 tile 404s (368 and 1,020 tile requests). Map instances created: **4** (story, two for the season swipe, explorer); Compare mode in the explorer adds two more only when opened.
- **Widths 360, 768, 1280, 1600 px** (`site/qa/v2_widths.mjs`): no horizontal overflow, no errors. Fixed: at 768 px cards hid the place they describe (narrower tablet cards and a lower zoom).
- **Story** (`site/qa/v2_story.mjs`): all 15 chapters show the right map state at 375 and 1440 px; End key and jumps land correctly.
- **Interludes** (`site/qa/v2_interludes.mjs`): videos play on screen, pause off screen and by button; under reduced motion they wait for Play; tables and chart answer the keyboard.
- **Explorer** (`site/qa/v2_explorer.mjs`): combobox by keyboard, roof caveat, compare by keys, building popup, year player, shared link restored, phone bottom sheet; no errors.
- **Without JavaScript:** intro, all 15 cards, figures and methods are present; maps, tables and the chart show a note with a CSV link.
- **Walkthrough video:** `outputs/demo/joto-mjini-walkthrough.webm` (1440 × 900, 64 MB, git-ignored because it is over 50 MB).

## v2 pre-ship checklist

- [x] Palette and typefaces are those of prompt 03 and the v2 brief (paper `#F7F4EE`, ink `#1C1B19`, Source Serif 4 and Source Sans 3, the brief's map ramps). Purple appears only as the brief's population ramp and in the Sentinel-2 false-colour image, where it is data.
- [x] Every effect passes the hand-coding test (table above).
- [x] Nothing from the banned list remains. Autoplay is the stated exception (D37).
- [x] Hover only darkens or strengthens buttons; nothing disappears.
- [x] Nothing important is hover-only (legends, tables, chart and calendar all work by tap and keyboard).
- [x] Native scrolling; no reveal animations; one header.
- [x] Body text meets WCAG AA (ink `#1C1B19` and secondary `#4A4740` on paper and white, unchanged from v1 checks).
- [x] No stock icons or emoji; the "i" is a typed letter.
- [x] Images and posters are sharp and match their videos (posters are frames of their own video).
- [ ] The first screen states the key finding and defines the measure, but the hero map is no longer on it: the v2 brief asks for a short intro, then the full-screen map. At 1440 × 900 the top of the map shows at the bottom of the first screen.
- [x] Every chart and map has a title or chip, subtitle or legend, source and date.
- [x] Works at 360, 768, 1280 and 1600 px (automated; not yet on a real phone).
- [x] Keyboard-only use and reduced motion work (automated checks on the controls listed above).
- [x] Works with JavaScript off at its default state (cards, figures and methods; interactive parts show notes).
- [ ] **A human has QA'd every page and every interaction:** this is Stephane's to do.
