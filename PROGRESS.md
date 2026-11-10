# Progress log

Times are local, Africa/Nairobi (UTC+3).

## Run 1, overnight 10 November 2026

- 2026-11-10 01:48 Run started. Read CLAUDE.md, DESIGN_RULES.md, reference notes, workshop brief, NASA story source and prompts 00 to 04.
- 2026-11-10 01:55 Skeleton: `git init`, `pyproject.toml` with uv (Python 3.12.14, `.venv`), PROGRESS/DECISIONS/QUESTIONS created. Homebrew GDAL, tippecanoe and pmtiles installing in the background (log in `logs/`). Next: Phase 1, data pipeline.
- 2026-11-10 02:20 **Phase 1 finished: data pipeline.**
  - Tools: GDAL 3.13.3, tippecanoe 2.79.0, pmtiles CLI (Homebrew), uv 0.12.5, Python 3.12.14. Python packages: exactextract 0.3.0, geopandas 1.2.0, matplotlib 3.11.2, numpy 2.5.4, overturemaps 2.1.0, pandas 3.1.1, planetary-computer 1.0.0, pymannkendall 1.4.3, pyproj 3.8.0, pystac-client 0.9.1, rasterio 1.5.2, rioxarray 0.23.0, scipy 1.18.1, shapely 2.2.0, xarray 2026.9.0.
  - Step 1: `nairobi_boundary.geojson` (705.3 km²), `nairobi_wards.geojson` (85 wards), `nairobi_places.geojson` (539 OSM features).
  - Step 2: 205 Landsat 8/9 scenes catalogued, 68 usable (`landsat_scene_catalogue.csv`); composites `lst_hot_season_median.tif` (12 scenes, Jan to Mar 2023 to 2026), `lst_cool_season_median.tif` (4 scenes, Jun to Aug 2018 to 2026), `lst_hottest_clear_day.tif` (29 Sep 2022), `ndvi_hot_season_median.tif`, by-year composites for 2015 to 2023, 2025, 2026.
  - Step 3: WorldCover 2021 and 30 m fractions; WorldPop 2025 (county 5,653,421); GHSL 1975 to 2025; 746,499 Overture buildings.
  - Steps 4 and 5: Open-Meteo daily air temperature 1991 to 9 Nov 2026; RONI 1950 to ASO 2026.
  - Step 6: partner data search recorded in `data/SOURCES.md` (no Earthna or CIFF data found; Cool Cities Lab reference only).
  - Step 7: Protomaps basemap extract, 26.5 MB.
  - Step 8: `data/processed/MANIFEST.md`; notebook `notebooks/01_data_pipeline.ipynb` executes top to bottom.
  - Skipped (optional): Kisumu, CLMS sharpening. Next: Phase 2, analysis.
- 2026-11-10 02:27 **Phase 2 finished: analysis.**
  - Code: `src/analysis/layers.py`, `core.py` (questions 1 to 8), `checks.py`, `web.py`, `figures.py`, `findings.py`. Notebook `notebooks/02_analysis.ipynb` executes.
  - Findings: `analysis/FINDINGS.md` (F1 to F13, generated from `analysis/results.json`); tables in `analysis/tables/`; checks in `analysis/checks.json` (five independent recomputations match; cool places all cooler than CBD and Industrial Area; ward populations within 2.4 % of the county total, WorldPop 2025, 5,657,304).
  - Web data in `site/public/data/`: wards.geojson (85 kB), county.geojson, places.geojson, comparison_areas.geojson, legends.json, chart CSVs, raster PMTiles (hot, cool, anomaly, tree, population, GHSL 1990 and 2020), buildings.pmtiles (43.5 MB).
  - Static figures in `outputs/figures/` (PNG and SVG), copied to `site/public/figures/`.
  - Node repaired (D19). Next: Phase 3, story site.
- 2026-11-10 02:48 **Phase 3 finished: story site.**
  - `site/` (Vite 8.3.7, vanilla JS, MapLibre 6.17.0, PMTiles 4.5.0, Scrollama 3.2.0, D3 7.9.2, Source Serif 4 and Source Sans 3 via Fontsource 5.3.1; Playwright 1.65.0 for QA). Structure follows the NASA story: title block, hero swipe map, sections, tree chart beside text, air temperature chart with El Niño shading, nine-chapter scrollytelling map, built-up swipe map, satellite explainer, ward explorer, cooling section, methods and credits.
  - Copy numbers are filled at build time from `analysis/results.json` (D23). Added findings F14 (Kileleshwa and Kawangware) and F15 (satellite record facts) for the copy.
  - Builds with `npm run build`; preview checked with Playwright at 1440 and 375 px: no console errors, PMTiles range requests return 206, first load about 1.5 MB before map tiles.
  - `site/SITE_REPORT.md` written. Next: Phase 4, QA and morning report.
- 2026-11-10 02:58 **Phase 4 finished: QA and morning report.**
  - Screenshots in `outputs/screenshots/` (first screens, full pages, nine chapters, explorer, swipe by keyboard, no JavaScript, widths 360 to 1600); QA scripts `site/qa/shoot.mjs`, `site/qa/widths.mjs`; link check `outputs/qa/link_check.md`.
  - Fixed during QA: table overflow at 360 px; JavaScript-only controls hidden without JavaScript; swipe zoom buttons hidden on phones; overpass time aligned to 10:43 in FINDINGS.
  - Notebooks 01 and 02 re-executed cleanly. `site/SITE_REPORT.md` has QA results and the pre-ship checklist. `docs/presentation_outline.md` and `MORNING_REPORT.md` written.
  - Next: only the optional "if time remains" items, in prompt order.
- 2026-11-10 03:05 **Optional work ("if time remains").** Prompt 01: Kisumu steps 1 to 3 running with `JOTO_CITY=kisumu` (D28; logs `logs/kisumu_*`); CLMS skipped (no credentials). Prompt 02: Cool Cities comparison not possible (no download); hot minus cool season difference map done (`src/analysis/extras.py`, `outputs/figures/map_hot_minus_cool.png`, FINDINGS E1). Prompt 03: print stylesheet (maps replaced by a note in print) and `site/slides.html` (eight static slides, PDF at `outputs/slides.pdf`).
