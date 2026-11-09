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
