# v2 chunk 3: the scrolling map story (budget about 2.5 hours)

Rebuild the story page (`site/index.html`) around full-screen maps with cards floating over them, following `DESIGN_BRIEF_v2.md` sections 4 and 5 and the NASA screenshots `nasa/03`, `04`, `05`, `06`, `07`, `08`, `09` and `13`. Move the v1 page to `site/_v1/` first.

## 1. Page skeleton (must)

1. **Short intro** (paper background, reading column): kicker "Nairobi's heat divide", headline (keep the current F3 headline for now), subtitle defining the measure, byline placeholder, two or three sentences from FINDINGS. Nothing else above the first map.
2. **Story block A** (scrollytelling, full screen).
3. **Interlude 1** (normal page flow): a before-and-after pair of maps, hot season and cool season, beside bullet points (layout of `nasa/12`), then a wide swipe-compare map of the same two layers.
4. **Story block B** (scrollytelling, full screen).
5. **Interlude 2**: placeholders for the animations, heatmaps and chart that chunk 4 fills.
6. **Explorer**: placeholder section for chunk 5.
7. **Methods and credits**: keep the v1 content, updated for the new sources.

## 2. The scrollytelling component (must)

- One sticky map per story block, full width and full height, no page margins. Cards scroll over it on the left (about 440 px wide, 40 px from the left edge, vertically spaced so one card is in view at a time). On phones (under 768 px) the map fills the screen and each card sits in the lower part of the screen over it.
- Chapters are defined as data, in `site/src/story/chapters.js`: `{id, basemap, layers: [{id, opacity}], center: [lon, lat], zoom, chip, legendLayer, card: {title, bullets or text}}`. Card numbers use the existing `{{path|format}}` placeholders from `analysis/results.json`.
- When a card's middle crosses the middle of the screen: `flyTo` (about 1.5 to 2 s), cross-fade layers (about 400 ms), update the date chip and legend card. Under reduced motion: `jumpTo` and instant changes. Scrolling back up restores the previous chapter.
- Keep the chapter state correct when the reader jumps fast (keyboard End, scrollbar drag): always apply the chapter whose card is nearest the middle.
- Disable scroll-zoom on story maps (so the page scrolls normally) but keep drag-pan and the zoom buttons.

## 3. Chapters (must)

Check each centre against the ward and place layers, and adjust so the place named in the card is in view and not hidden behind the card (on desktop, offset the centre to the right with `padding: {left: 480}`).

**Story block A: from space to heat**

1. **Nairobi from space.** Basemap: satellite streets; layer `s2-true`; county outline. Centre about [36.86, -1.29], zoom 10.3 (9.4 on phones). Chip: "Sentinel-2, January to March 2026". Card: one sentence on what the reader is looking at.
2. **Where the trees are.** Layer `s2-false` (vegetation glows green, as in `nasa/07`). Same view, then a gentle move north-west to show Karura Forest, the Arboretum and Ngong Road Forest. Card: tree cover share of the county and the names of the main green areas.
3. **What covers the ground.** Light basemap, layer `landcover`. Card: bullet list of the land cover shares and their hot-season surface temperatures (F5).
4. **The heat divide.** Light basemap, layer `heat-diff`, ward outlines and ward names. Chip: "January to March mornings, 2023 to 2026". Card: bullets from F1 and F2.

**Story block B: a closer look**

5. **City centre and Industrial Area.** Satellite streets first (about zoom 13.5, centre between the two areas), then the same view with `heat-diff` at 0.75 opacity. Card: bullets from F3 (with the new comparison areas from chunk 1).
6. **Rooftops of Eastlands.** Satellite streets, layer `buildings` coloured by difference from the city median, zoom about 15 over a dense Eastlands neighbourhood. Card: bullets from F7, and the roof caveat from chunk 1 if it applies.
7. **Islands of cool.** Karura Forest edge, satellite, then `heat-diff`. Card: F9 (say clearly that the signal is small).
8. **Leafy and dense, a short walk apart.** Kileleshwa and Kawangware side by side, `heat-diff` with both ward outlines highlighted and labelled. Card: F14.
9. **Who lives on the hottest ground.** `population`, then `heat-diff`, same view (two steps). Card: F6.
10. **A growing city.** `growth-1990-2020`. Chip: "1990 to 2020". Card: F10.
11. **The whole city, ward by ward.** Wards filled by population-weighted difference from the city median, ward names on. Card: F8. A last line: "Find your own ward below", linking to the explorer.

## 4. Check and compare (must)

Save screenshots of every chapter at 1440 px and 375 px to `outputs/screenshots/v2/chunk3/`. Open them next to the NASA screenshots and check: map fills the screen, card does not hide the place it describes, labels readable, colours clearly different between hot and cool places, chip and legend present. Fix and re-screenshot until all pass. Record a short self-review in `PROGRESS.md`.

## Done when

Both story blocks work by scroll, keyboard and touch, every chapter passes the checks, and the commit "v2 chunk 3: scrolling map story" is made.
