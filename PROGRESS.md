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
