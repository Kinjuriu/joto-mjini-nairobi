# Morning report: overnight run 1, 10 November 2026

## 1. Status in one paragraph

All four phases finished, and every number on the site comes from real data. The pipeline downloads and processes all the core datasets. The analysis produced 15 findings in `analysis/FINDINGS.md`; I recomputed the headline ones a second way and they matched. The story site builds and runs locally: hero swipe map, charts, a nine-chapter scrolling map tour, a second swipe map and the ward explorer. To open it, run `cd site && npm run dev` and go to **http://localhost:5173/joto-mjini/**. For the built version, run `npm run build && npx vite preview` and go to http://localhost:4173/joto-mjini/. The site works offline once it is served from your laptop. It still needs your own human QA, your surname and dates in the byline, and a decision on the headline.

## 2. What got done

- **Phase 1, data pipeline** (`src/pipeline/`, `notebooks/01_data_pipeline.ipynb`):
  - Nairobi boundary, 85 wards and 539 OSM places.
  - 205 Landsat 8 and 9 scenes catalogued, 68 usable.
  - Hot-season (12 scenes, 2023 to 2026) and cool-season (4 scenes, 2018 to 2026) surface temperature composites.
  - WorldCover 2021, WorldPop 2025, GHSL 1975 to 2025, 746,499 Overture buildings.
  - Daily air temperature 1991 to 9 November 2026, RONI, and a Protomaps basemap.
  - Everything is listed in `data/SOURCES.md` and `data/processed/MANIFEST.md`.
- **Phase 2, analysis** (`src/analysis/`, `notebooks/02_analysis.ipynb`):
  - `analysis/FINDINGS.md`, generated from `analysis/results.json`, with checks in `analysis/checks.json`.
  - Web layers in `site/public/data/`.
  - Static figures in `outputs/figures/`.
- **Phase 3, story site** (`site/`):
  - Vite with vanilla JavaScript, MapLibre, PMTiles, Scrollama and D3, with fonts self-hosted.
  - Numbers enter the copy only through build-time placeholders filled from `results.json`.
  - Design notes are in `site/SITE_REPORT.md`.
- **Phase 4, QA** (`outputs/screenshots/`, `outputs/qa/link_check.md`, `docs/presentation_outline.md`):
  - Screenshots at 360, 375, 768, 1280, 1440 and 1600 px.
  - No console errors, and PMTiles range requests return 206.
  - First load is about 1.5 MB before map tiles.
  - Works with JavaScript off, by keyboard alone, and with reduced motion.

## 3. The findings

All temperatures are land surface temperature on clear January to March mornings unless the finding says otherwise.

| # | Finding | Confidence |
|---|---|---|
| F1 | Half of the county's ground was hotter than 38.7 °C; hottest tenth 44.9 °C, coolest tenth 29.3 °C | High |
| F2 | Hottest ward Ruai 42.4 °C, coolest Karen 32.3 °C; 8 hottest wards 7.2 °C hotter than 8 coolest | High (numbers), medium (meaning) |
| F3 | City centre and Industrial Area 40.5 °C against Karura and the Arboretum 27.6 °C: a gap of 12.8 °C | High |
| F4 | Mostly built-up ground 7.8 °C hotter than mostly tree-covered ground; 39.9 °C under 10 % trees vs 31.5 °C over 90 % | High (association only) |
| F5 | Dry grassland 40.1 °C, farmland 41.0 °C and bare ground 41.4 °C were as hot as or hotter than built-up land 39.7 °C | High |
| F6 | About 827,000 people (14.6 %) live on the hottest fifth of the ground; residents average 39.4 °C vs 38.1 °C for all land | High (arithmetic), medium (WorldPop) |
| F7 | Ten hottest wards by where people live (Viwandani first) are home to about 348,000 people; none has more than 12.5 % tree cover | Medium |
| F8 | Hottest fifth of wards 41.1 °C vs coolest fifth 36.7 °C (gap 4.4 °C); tree cover 3.3 % vs 36.1 % | Medium |
| F9 | Built-up land within 100 m of Karura 2.1 °C cooler than 700 to 1,000 m away, fading by about 500 m; about 1 °C at the Arboretum and City Park | Low to medium |
| F10 | Built-up area grew from about 66 km² (1990) to 101 km² (2020); yearly surface temperature shows no clear trend (Mann-Kendall p = 1.0) | High |
| F11 | Cool season median 34.9 °C; places kept their order (ward rank correlation 0.75) | Medium |
| F12 | Air temperature: daily high changes 1.1 °C a day on average, 3 °C or more on 68 days since 2023; since May 2026 highs averaged 25.0 °C, 1.7 °C above 1991 to 2020 for those months | High (arithmetic) |
| F13 | Hottest clear morning: 29 September 2022, county median 46.6 °C | High |
| F14 | Kawangware 41.6 °C with 10 % trees; Kileleshwa 35.7 °C with 48 %; 1.3 km apart | High (illustrative pair) |
| F15 | 205 passes checked, 68 usable; overpass about 10:43 Nairobi time | High |

## 4. What failed or was cut

- **No informal-settlement comparison (prompt 02, question 7).** WRI's irregular-settlement layer is only on Google Earth Engine. To retry: export `projects/wri-datalab/cities/urban_land_use/V1` for Nairobi to `data/raw/`. I can then add the comparison to `src/analysis/core.py`.
- **No WRI Cool Cities Lab comparison.** Its layers cannot be downloaded from the site, and the layer page says "Dataset information unavailable".
- **Kisumu and CLMS hourly sharpening skipped** (both optional). CLMS needs Copernicus credentials in `.env`, and there was none.
- **tippecanoe** exited with status 101 on FlatGeobuf input and with `--extend-zooms-if-still-dropping`. It works on GeoJSONSeq with `--drop-smallest-as-needed` (D18). At zooms 12 and 13 only the larger buildings show.
- **GDAL PMTiles driver** is vector-only in Homebrew GDAL 3.13.3. Raster tiles go through MBTiles and `pmtiles convert` instead (D10).
- **Node broke during setup.** `brew install gdal` upgraded `simdjson` and broke Node (missing `libsimdjson.33.dylib`). I fixed it with `brew upgrade node`, so your global Node is now 26.13.0 (D19).
- **Links:** 5 of 39 failed automated checks, all explained in `outputs/qa/link_check.md` (publishers blocking bots).

## 5. Decisions I made for you (full list in DECISIONS.md)

1. **Wards come from geoBoundaries ADM3** (Omare and Omare, CC BY 4.0): exactly 85 wards (D4).
2. **The hot-season map is January to March 2023 to 2026** (12 scenes). The cool season had to reach back to 2018 to get 4 scenes (D5).
3. **WorldPop 2025 constrained** for population. Ward totals add to 97.6 % of the county total (D6).
4. **The CBD and Industrial Area are defined as circles** (750 m and 1 km), because OpenStreetMap has no single polygon for either (D12).
5. **The site is grey basemap plus data colours only, self-hosted for offline use.** Web layers stop at the county edge (D21, D25).
6. **Numbers are filled at build time from `results.json`**, so the copy cannot drift from FINDINGS (D23).
7. **On phones, the tour uses one sticky map** with the cards scrolling under it (D24).

## 6. Questions for you (most important first)

1. **Headline.** Keep "On hot mornings, central Nairobi's ground is 12.8 °C hotter than its forests", or use one of the three alternatives in `site/SITE_REPORT.md`?
2. **Informal settlements.** Can you export the WRI layer from Earth Engine, so the settlement comparison can be added?
3. **Population in dense wards.** WorldPop gives Laini Saba about 3,300 people and Kangemi about 11,700, which may be undercounts. Should we use the 2019 census ward totals if you can get them?
4. **CBD and Industrial Area shapes.** Do you have preferred boundaries?
5. **Ward boundary source.** Is there an official IEBC layer you prefer?
6. **Partner data.** No Earthna or CIFF data was found. Do you want to ask the organisers, or WRI for the Cool Cities layers?

## 7. Suggested next run

1. **Your human QA on a real phone,** then a writing pass. Focus on the tour on a phone (D24), the swipe gestures, and the headline choice.
2. **Strengthen the people side.** Bring in census ward populations and the informal-settlement layer if you can get them. Re-run the analysis, and the site updates itself.
3. **Prepare for the talk and for publishing.** Make slides from `docs/presentation_outline.md`, publish to GitHub Pages (set `BASE` in `site/vite.config.js`), and send the work to Tony for review.

## Optional work done after the main run

These were done after the main run, in the order of the "if time remains" lists in the prompts. None of it is in the story yet.

- **Season difference (prompt 02):** `outputs/figures/map_hot_minus_cool.png` and finding E1. 98.9 % of the county's ground was hotter in January to March than in June to August, by 3.6 °C at the median. A few wards changed by less than 1 °C.
- **Kisumu (prompts 01 and 02):** the same pipeline run with `JOTO_CITY=kisumu` (D28). Outputs are in `data/processed/kisumu/` and the summary is finding E2. Half of Kisumu's land was hotter than 35.6 °C; built-up ground was 39.0 °C against 33.9 °C under trees. Nyalenda 'A' comes out among the coolest wards, probably because it sits next to the lake and wetland. Check this before using it. Nairobi's results were re-run after the change and are identical.
- **Print and slides (prompt 03):** the story now prints cleanly, with maps replaced by a note. `site/slides.html` has eight static slides; open it at http://localhost:5173/joto-mjini/slides.html. A PDF is at `outputs/slides.pdf`.
- **Not possible:** the Cool Cities Lab comparison (no downloadable layer) and CLMS sharpening (no credentials).

## 8. Time used (Africa/Nairobi)

| Phase | Start | End | Time |
|---|---|---|---|
| Reading and setup | 01:48 | 01:53 | 5 min |
| 1. Data pipeline | 01:53 | 02:14 | 21 min |
| 2. Analysis | 02:14 | 02:25 | 11 min (refined during Phase 3) |
| 3. Story site | 02:25 | 02:46 | 21 min |
| 4. QA and report | 02:46 | 02:58 | 12 min |

Optional work ran from 02:58 to about 03:50; most of it was waiting for the Kisumu Landsat run (838 scenes). The whole night took much less than the 9.5 hours budgeted. Disk use: `data/raw` 497 MB, `data/interim` 909 MB, `site/public/data` 74 MB, `.git` 283 MB.
