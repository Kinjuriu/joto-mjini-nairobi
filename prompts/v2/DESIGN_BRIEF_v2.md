# Design brief v2: a NASA-style story dashboard for Nairobi heat

This brief replaces the "Look and feel" and "Page structure" sections of `prompts/03_story_site.md`. Where they conflict, this brief wins. `DESIGN_RULES.md` (Stephane's no-vibe-coding rules) still applies, except where this brief makes a stated exception.

Before reading on, open every image in `reference/screenshots/nasa/` and `reference/screenshots/ours_v1/`, and read `reference/screenshots/README.md`.

## The goal in one paragraph

Stephane wants Joto Mjini Nairobi to look and behave like NASA's "Fanning the Flames" story dashboard: a short intro, then a full-screen map that flies from place to place as the reader scrolls, with small cards floating over it, layers that change from satellite imagery to a vegetation view to heat, animated maps, heatmap tables and charts between the map sections, and a full interactive explorer at the bottom. The maps must be crisp, the colours must make hot and cool places clearly different, and place names must always be readable. Building comes first; the written article comes last and is not part of this work.

## 1. Map engine and basemaps

**Engine: Mapbox GL JS v3** (the engine NASA's dashboard uses). Pin the exact version at install time.

- The access token comes from `site/.env.local` as `VITE_MAPBOX_TOKEN`. Never hard-code it, never print it, never commit `.env.local` (add `*.local` to `.gitignore`).
- Free tier: 50,000 map loads a month, far beyond what this site needs. Keep one map instance per section where possible (the scrollytelling block uses one sticky map, not one map per chapter).
- Mapbox GL JS cannot read PMTiles. Serve our layers as **static XYZ tile folders** (`site/public/tiles/<layer>/{z}/{x}/{y}.webp` for rasters, `.pbf` for vectors built with tippecanoe's directory output and `--no-tile-compression`), which GitHub Pages can host. Keep the PMTiles files from v1 as the source; convert them.

**Basemaps** (all Mapbox styles; check the current style IDs in Mapbox's documentation):

| Use | Style |
|---|---|
| Satellite chapters | Mapbox Satellite Streets (imagery with roads and labels) |
| Data chapters (heat, land cover, wards) | A light, low-detail Mapbox style (Light, or Standard with a light preset and most features hidden) so data colours stay true; labels on top |
| Optional dark variant | Mapbox Dark, only if testing shows it makes the heat colours easier to read |

Test the heat layer over each candidate basemap at zooms 10, 12 and 14, save the screenshots to `outputs/screenshots/v2/basemap_tests/`, choose by the rules in section 3, and record the choice in `DECISIONS.md`.

**Our own Sentinel-2 images** (needed because Mapbox has no false-colour view and no fixed date): build a cloud-free dry-season composite of Nairobi at 10 m from Sentinel-2 Level-2A (Planetary Computer collection `sentinel-2-l2a`), January to March 2026 (or the most recent clear months), median of clear pixels using the scene classification layer. Make two layers:
- **True colour** (bands B04, B03, B02), for the "Nairobi from space" chapter.
- **False colour** (bands B12, B8A, B04, the Sentinel-2 equivalent of NASA's Landsat 7-5-4), where vegetation is bright green and built-up land is purple-grey, for the "where the trees are" chapter (see `nasa/07_...png`).
Credit: "Contains modified Copernicus Sentinel data 2026, processed by Joto Mjini Nairobi."

## 2. Colour and layers

**The heat problem in v1:** one red ramp with fixed breaks put most of Nairobi in the top classes, so everything looked red. Fix it this way:

- **Default heat view: difference from the city median** (°C), diverging, so about half the city is blue and half is orange or red:

  | Difference from city median (°C) | Colour |
  |---|---|
  | −6 or cooler | `#1D4E6F` |
  | −6 to −4 | `#3B7CA6` |
  | −4 to −2 | `#8DBAD6` |
  | −2 to −0.5 | `#C9DDE9` |
  | −0.5 to +0.5 (about the same as the city) | `#F2EFE9` |
  | +0.5 to +2 | `#F6CBA6` |
  | +2 to +4 | `#F4A26B` |
  | +4 to +6 | `#D9542B` |
  | +6 or hotter | `#A1201A` |

  Check this ramp with the dataviz palette validator approach (colour-blind separation, neutral midpoint) and adjust steps only if a check fails; record the result.
- **Absolute surface temperature** (secondary layer): ColorBrewer YlOrBr, seven classes, `#FFF7D6`, `#FEE391`, `#FEC44F`, `#FB9A29`, `#EC7014`, `#CC4C02`, `#8C2D04`, with **breaks at the county's deciles** (computed from the data and written into the legend), so the colours spread across the city.
- **Smooth, not blocky:** the thermal data is measured at about 100 m. Build heat tiles with bilinear (or cubic) resampling and set `raster-resampling: 'linear'` in the map, so it reads as a smooth field. Categorical layers (land cover) keep nearest-neighbour resampling and crisp edges.
- **Opacity:** heat layers at about 0.75 over imagery, 0.9 over the light basemap. Test both.
- **Labels on top, always:** insert every data layer **before the first symbol layer** of the basemap style (find it at runtime with `map.getStyle().layers`), so road and place names draw above the data. Strengthen label legibility over data: dark text, white halo of 1.5 to 2 px.
- **Ward names:** add our own ward label layer (ward names at a point inside each ward, from zoom 11) and thin white ward outlines over imagery, thin dark outlines over the light basemap.
- **Land cover** (ESA WorldCover classes): distinct categorical colours in the spirit of NASA's NLCD map: tree cover `#2E6B3F`, shrubland `#8FB573`, grassland `#E3D9A0`, cropland `#D8A657`, built-up `#C8423A`, bare or sparse `#B9B0A2`, water `#3E6FA8`, wetland `#6FA9A8`. Legend lists every class shown.
- **Buildings by heat:** footprints filled with the diverging ramp (difference from city median), shown from zoom 14 over satellite imagery, with a 0.5 px darker outline. They are the crispest heat view; use them in the zoomed chapters.
- **Population:** ColorBrewer single-hue purple ramp (`#F2F0F7` to `#54278F`), five classes with quantile breaks, smoothed like heat, so it no longer looks like grey blocks.
- **Growth (GHSL):** show only the cells that became built-up between the two epochs in a strong colour (`#C8423A`) over the earlier built-up area in a neutral (`#6B6B6B`), so change is obvious.

**Legends:** a legend card at the bottom right of every map (see `nasa/05_...png`): layer name, a short "i" button that opens a two-sentence description and source, class swatches with labels that never collide (test at 375 px), units.

**Date chip:** a small white chip at the top centre of every map saying what time the layer shows ("January to March mornings, 2023 to 2026", "29 September 2022, 10:43", "1990" or "2020", "Sentinel-2, February 2026").

## 3. Legibility rules for every map (test and screenshot)

1. At zoom 12, a reader can read at least five place or ward names without zooming.
2. Hot places and cool places are clearly different colours (for the difference layer, at least a third of the county should be blue and a third orange or red).
3. No visible square pixels at zoom 13 on the heat, difference and population layers.
4. No legend labels collide at 375 px or 1440 px.
5. Nothing important is hidden under a card at 1440 px or at 375 px.

## 4. Layout (copy NASA's structure)

1. **Short intro** on the paper background: kicker, headline, one-sentence subtitle, byline placeholder, and two or three sentences that set up the story (taken from `analysis/FINDINGS.md`). Nothing else.
2. **Scrollytelling block:** a full-width, full-height sticky map (`100vw` by `100vh`, no page margins) with chapter cards scrolling over it on the left (cards about 440 px wide on desktop; on phones, cards take the bottom of the screen over the map). The map flies to each chapter's centre and zoom and changes layer when a card reaches the middle of the screen.
3. **Interludes** between scrollytelling blocks, laid out like NASA's: an animated map beside text (`nasa/01`), a chart with a highlighted period (`nasa/02`), heatmap tables (`nasa/03`), a before-and-after pair (`nasa/12`), a wide swipe-compare map.
4. **Explorer dashboard** near the end: the full interactive map (see chunk 5).
5. **Methods and credits.**

**Chapter cards:** white background, 2 px corner radius, a short 32 by 3 px accent rule at the top in `#1D4E6F`, a title in Source Sans 3 semibold, then either two or three short sentences or a bullet list of three to five key numbers (`nasa/05`). Every number comes from `analysis/results.json` through the existing build-time placeholder system, so text cannot drift from the findings.

**Transitions:** `flyTo` of about 1.5 to 2 s between chapters; layer changes cross-fade over about 400 ms by animating raster opacity; under `prefers-reduced-motion`, use `jumpTo` and instant layer changes. This motion shows the reader where they are going and what changed, so it passes the hand-coding test.

## 5. Animations (stated exception to "no autoplay")

Stephane has asked for moving maps like NASA's wind animation. Animated maps play automatically, muted and looping, **only while they are on screen**, and pause when scrolled away; each has a visible pause and play button; under `prefers-reduced-motion` they show the poster frame and wait for the reader to press play. Record this exception in `DECISIONS.md`. Export each animation as MP4 (H.264) for the site, WebM as a lighter alternative, a GIF of 8 MB or less for LinkedIn, and a poster PNG.

## 6. Typography and colour outside the maps

Unchanged from v1: page background `#F7F4EE`, text `#1C1B19`, secondary text `#4A4740`, Source Serif 4 for headlines and body, Source Sans 3 for cards, labels, legends and controls, tabular numbers. No purple gradients, glassmorphism, stock icons or emoji.

## 7. Writing

Do not write the article. Use the existing sentences from `analysis/FINDINGS.md` as the text in cards and interludes, and mark anything else as `[[COPY: short description of what goes here]]`. Stephane will write the article with Claude later.
