# Morning report v2: Joto Mjini Nairobi as a NASA-style story dashboard, 10 November 2026

## 1. Status

All six chunks are done and committed. The site now works like NASA's "Fanning the Flames" dashboard: a short intro, a full-screen map story with cards floating over it (15 chapters), animated maps, heatmap tables and a highlighted chart between the map sections, and a full explorer at the bottom. Automated checks found no console errors, no failed requests and no missing tiles at 360, 375, 768, 1280, 1440 and 1600 px. The page creates four Mapbox maps.

To open it: `cd site && npm run dev`, then **http://localhost:5173/joto-mjini-nairobi/** (layer test page: `/joto-mjini-nairobi/layers.html`). Built version: `npm run build && npx vite preview`, then http://localhost:4173/joto-mjini-nairobi/. The story text is still mostly `[[COPY: ...]]` placeholders plus FINDINGS sentences, as you asked.

**One thing to check first:** Mapbox refuses satellite imagery for your token (HTTP 429 "Too Many Requests"), while its maps and labels work. "Satellite" therefore shows our own Sentinel-2 image under Mapbox's roads and labels (D33, QUESTIONS 9). If the account starts serving imagery, set `VITE_SATELLITE=mapbox` in `site/.env.local`.

## 2. What changed since v1

1. **Data fixes:** IEBC ward boundaries, checkable comparison areas, a roof emissivity check, and the analysis re-run (section 3).
2. **Map engine and layers:** Mapbox GL JS 3.34.2 replaces MapLibre. Every layer is now a static XYZ tile folder (173 MB): heat as a difference from the city median (45 % of the county blue, 44 % orange or red), absolute heat with decile breaks, hottest morning, cool season, land cover, trees, purple population, growth, six GHSL epochs, buildings, and new Sentinel-2 true and false colour images (January to March 2026, 10 m). Values are smoothed between cells, so there are no square pixels. Labels sit above the data with white halos, and our own ward names show from zoom 10. Legend card and date chip on every map.
3. **Map story:** one shared full-screen map, flyTo and cross-fades, cards on the left (at the bottom on phones). Numbers are filled from `results.json` at build time.
4. **Animations and heatmaps:** every clear hot-season morning 2014 to 2026 (35 frames); Nairobi grows 1975 to 2025; a day of heat on 27 January 2026 from Copernicus hourly land surface temperature sharpened with Landsat (D38). Each comes as MP4, WebM, GIF (8 MB or less) and poster. Also three heatmap tables (built-up share by sub-county, land cover in the hottest and coolest wards, a calendar of daily highs) and the El Niño chart.
5. **Explorer:** layer panel, opacity, info buttons, year player, swipe compare, ward search, ward panel with ranks in words and the roof caveat, building popups, a shareable link, and a bottom sheet on phones.
6. **QA and handover:** NASA comparisons, a walkthrough video, this report. The project is renamed Joto Mjini Nairobi everywhere a reader sees it, and Vite's `base` is `/joto-mjini-nairobi/`.

## 3. Data fixes and changed numbers

- **Wards:** "Administrative Wards in Kenya 1450" (American Red Cross on HDX, IEBC boundaries, CC BY). It has 85 wards in 17 sub-counties, and the names match the IEBC list. **The Kibra problem is only partly solved:** WorldPop still puts 133,937 people (68 % of Kibra) in Woodley/Kenyatta Golf Course, against 35,355 in the 2009 census. Under these lines a large part of Kibera's dense housing falls inside Woodley, so the gap comes mostly from how WorldPop spreads people (D29, QUESTIONS 7).
- **F3:** the city centre is now the Nairobi Central ward and the Industrial Area is 10 merged OpenStreetMap industrial polygons. Gap 12.8 → **13.1 °C** (city centre 38.8 → 39.1 °C, Industrial Area 41.3 → 41.5 °C, Karura and Arboretum 27.6 °C) (D30).
- **Roof check (F16):** the emissivity the satellite product uses in dense, almost treeless wards (0.966) is the same as elsewhere (county 0.965). It does not account for metal roofs, so **these wards may be hotter than shown**. By my estimate, each 0.01 of overestimated emissivity hides about 0.7 °C; Nichol et al. (2025) found that corrected metal-roof emissivity raised Landsat city surface temperatures by 3 to 8 °C in other African cities. The caveat appears on the rooftops card and for 32 wards in the explorer.
- **Moved more than 0.3 °C or 5 %:** hottest ward Ruai 42.4 °C → **Embakasi 42.8 °C**; F7 ten hottest wards by where people live 348,000 → **412,000** people, now led by Kangemi, with most tree cover 12.5 → 14.1 %; F8 hottest fifth of wards 1,105,000 → 655,000 people, tree cover 3.3 → 5.0 %, gap 4.4 → 4.7 °C, tree ratio 10.9 → 7.2 (title now "about one seventh"); F14 Kawangware 41.6 → 40.9 °C, 9.9 → 14.1 % trees, gap with Kileleshwa 5.9 → **5.1 °C**. Full list in PROGRESS.md.

## 4. Screenshots to look at first

1. `outputs/screenshots/v2/chunk3/07_centre-heat_1440.png`: heat over the city centre and Industrial Area
2. `outputs/screenshots/v2/chunk3/02_trees_1440.png`: false colour, vegetation in green
3. `outputs/screenshots/v2/chunk3/08_rooftops_1440.png`: buildings by heat over imagery
4. `outputs/screenshots/v2/chunk3/11_pair_1440.png`: Kawangware and Kileleshwa
5. `outputs/screenshots/v2/chunk3/15_wards_1440.png`: wards with names
6. `outputs/screenshots/v2/chunk3/11_pair_375.png`: the phone layout
7. `outputs/animations/hot_mornings_poster.png` and `day_of_heat_poster.png`
8. `outputs/screenshots/v2/chunk4/landcover-table_1440.png`
9. `outputs/screenshots/v2/chunk5/02_ward_selected_1440.png` and `03_compare_1440.png`
10. `outputs/screenshots/v2/compare_with_nasa/` (seven pairs)

## 5. What still falls short of NASA's look

- **Land cover card (`nasa/05`):** card, chip and legend now match. NASA's map runs edge to edge, while ours stops at the county line on a pale basemap, so the screen feels emptier.
- **True colour (`nasa/06`):** the layout matches. Without Mapbox imagery, our 10 m image is a rectangle with plain grey outside it; NASA's imagery is seamless and sharper.
- **False colour (`nasa/07`):** close, with vegetation bright green and the city purple. The same rectangle edge applies.
- **Zoomed labels (`nasa/08`):** labels are readable over the data and the colours are clearly different. Our diverging field is busier than NASA's categorical map, and some ward names drop out where labels collide.
- **Animation beside text (`nasa/01`):** same layout, with title, time stamp, colour bar and credit baked in. At page size the baked-in labels and credit are small; a 1200 × 900 crop would read better.
- **Heatmap table (`nasa/03`):** numbers in squared cells, as in NASA's table. NASA puts its table beside a full-bleed map, while ours sits beside text.
- **Highlighted chart (`nasa/02`):** shaded period, crosshair and direct label all match. Ours has no second series or toggle.

## 6. Decisions I made for you, and questions for you

**Decisions (D29 to D41 in DECISIONS.md):** HDX/IEBC wards (D29); ward and OSM comparison areas (D30); the roof caveat applies (D31); Light and Satellite basemaps and no dark variant (D32); Sentinel-2 in place of Mapbox imagery (D33); tile method (D34); ramp check passed unchanged (D35); one shared story map (D36); autoplay exception (D37); the CLMS path for the day of heat, with my own sharpening (D38); calendar values by tap instead of printed in each cell (D39); Sentinel-2 composite (D40); the look changes compared with v1 (D41).

**Questions (QUESTIONS.md 7 to 9):**
1. Mapbox satellite imagery: can you check the account and token?
2. Woodley/Kenyatta Golf Course population: use 2019 census ward totals, or add a note?
3. Is the Nairobi Central ward the city centre you want for the headline?

I could not retrieve the Zlinszky (2026) Zenodo record, so the sharpening follows only the idea named in the prompt (D38). Please check it before you cite it.

## 7. Suggested next run

1. Write the article with Claude, filling the 13 `[[COPY]]` markers (8 in `site/index.html`, 5 in `site/src/story/chapters.js`), then do your own human QA on a real phone.
2. Fix Mapbox imagery, or extend the Sentinel-2 image to a wider box so its edge leaves the screen.
3. Bring in 2019 census ward populations and the WRI informal-settlement layer, then re-run (the site updates itself).
4. Optional items not done: the CHIRPS El Niño rainfall teaser animation; tighter animation crops for LinkedIn.

## 8. Time used (Africa/Nairobi, 10 November 2026)

| Chunk | Start | End | Time | Budget |
|---|---|---|---|---|
| Reading | before 12:03 | 12:03 | about 10 min | 20 min |
| 1. Data fixes | 12:03 | 12:12 | 9 min | 1.5 h |
| 2. Map engine and layers (with drafts of 3 to 5) | 12:12 | 13:35 | 83 min | 2.5 h |
| 3. Map story | 13:35 | 13:44 | 9 min (QA and fixes) | 2.5 h |
| 4. Animations and heatmaps | 13:44 | 13:47 | 3 min (QA and fixes) | 2.5 h |
| 5. Explorer | 13:47 | 13:52 | 5 min (QA and fixes) | 2 h |
| 6. QA and handover | 13:52 | 14:10 | 18 min | 1 h |

Most of the code for chunks 3 to 5 was written during chunk 2 while the Sentinel-2 download ran, so the times for 3 to 5 cover QA and fixes only.
