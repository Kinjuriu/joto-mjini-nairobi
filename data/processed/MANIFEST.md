# Processed data manifest

Generated 2026-11-10 02:13 (Africa/Nairobi) by `src/pipeline/manifest.py`.

| File | Size | Grid | Purpose |
|---|---|---|---|
| `data/processed/composites_meta.json` | 3 kB |  | Which scenes and years went into each composite |
| `data/processed/landsat_scene_catalogue.csv` | 29 kB |  | Every Landsat 8/9 scene 2013 to now with clear fraction and county stats |
| `data/processed/lst_2026_el_nino_period.csv` | 0 kB |  | Usable scenes since May 2026 (for the later El Nino phase) |
| `data/processed/nairobi_boundary.geojson` | 66 kB |  | Nairobi County outline (geoBoundaries ADM1) |
| `data/processed/nairobi_buildings.parquet` | 92.1 MB |  | Overture building footprints inside the county |
| `data/processed/nairobi_daily_air_temp.csv` | 0.3 MB |  | Open-Meteo ERA5 daily 2 m air temperature, Nairobi CBD grid cell, 1991 to yesterday |
| `data/processed/nairobi_places.geojson` | 0.3 MB |  | OSM place names, parks, forests, water, industrial areas |
| `data/processed/nairobi_wards.geojson` | 0.1 MB |  | 85 county assembly wards with ward_id, ward_name |
| `data/processed/rasters/bare_fraction_30m.tif` | 0.6 MB | EPSG:32737, 30 m | Share of each 30 m cell that is bare or sparse vegetation |
| `data/processed/rasters/built_fraction_30m.tif` | 2.3 MB | EPSG:32737, 30 m | Share of each 30 m cell that WorldCover calls built-up |
| `data/processed/rasters/ghsl_built_1975.tif` | 0.5 MB | EPSG:32737, 90 m | GHSL built-up surface fraction, epoch 1975, regridded to 90 m |
| `data/processed/rasters/ghsl_built_1990.tif` | 0.6 MB | EPSG:32737, 90 m | GHSL built-up surface fraction, epoch 1990, regridded to 90 m |
| `data/processed/rasters/ghsl_built_2000.tif` | 0.6 MB | EPSG:32737, 90 m | GHSL built-up surface fraction, epoch 2000, regridded to 90 m |
| `data/processed/rasters/ghsl_built_2010.tif` | 0.8 MB | EPSG:32737, 90 m | GHSL built-up surface fraction, epoch 2010, regridded to 90 m |
| `data/processed/rasters/ghsl_built_2020.tif` | 0.9 MB | EPSG:32737, 90 m | GHSL built-up surface fraction, epoch 2020, regridded to 90 m |
| `data/processed/rasters/ghsl_built_2025.tif` | 0.9 MB | EPSG:32737, 90 m | GHSL built-up surface fraction, epoch 2025, regridded to 90 m |
| `data/processed/rasters/grass_fraction_30m.tif` | 2.5 MB | EPSG:32737, 30 m | Share of each 30 m cell that is grassland |
| `data/processed/rasters/lst_cool_season_count.tif` | 69 kB | EPSG:32737, 30 m | Clear observations per pixel in the cool-season composite |
| `data/processed/rasters/lst_cool_season_median.tif` | 6.5 MB | EPSG:32737, 30 m | Median Jun to Aug land surface temperature, deg C |
| `data/processed/rasters/lst_hot_season_by_year/2015.tif` | 6.4 MB | EPSG:32737, 30 m | Jan to Mar median land surface temperature for 2015 |
| `data/processed/rasters/lst_hot_season_by_year/2016.tif` | 6.5 MB | EPSG:32737, 30 m | Jan to Mar median land surface temperature for 2016 |
| `data/processed/rasters/lst_hot_season_by_year/2017.tif` | 6.0 MB | EPSG:32737, 30 m | Jan to Mar median land surface temperature for 2017 |
| `data/processed/rasters/lst_hot_season_by_year/2018.tif` | 6.5 MB | EPSG:32737, 30 m | Jan to Mar median land surface temperature for 2018 |
| `data/processed/rasters/lst_hot_season_by_year/2019.tif` | 6.4 MB | EPSG:32737, 30 m | Jan to Mar median land surface temperature for 2019 |
| `data/processed/rasters/lst_hot_season_by_year/2020.tif` | 6.3 MB | EPSG:32737, 30 m | Jan to Mar median land surface temperature for 2020 |
| `data/processed/rasters/lst_hot_season_by_year/2021.tif` | 6.1 MB | EPSG:32737, 30 m | Jan to Mar median land surface temperature for 2021 |
| `data/processed/rasters/lst_hot_season_by_year/2022.tif` | 5.9 MB | EPSG:32737, 30 m | Jan to Mar median land surface temperature for 2022 |
| `data/processed/rasters/lst_hot_season_by_year/2023.tif` | 5.9 MB | EPSG:32737, 30 m | Jan to Mar median land surface temperature for 2023 |
| `data/processed/rasters/lst_hot_season_by_year/2025.tif` | 6.5 MB | EPSG:32737, 30 m | Jan to Mar median land surface temperature for 2025 |
| `data/processed/rasters/lst_hot_season_by_year/2026.tif` | 6.5 MB | EPSG:32737, 30 m | Jan to Mar median land surface temperature for 2026 |
| `data/processed/rasters/lst_hot_season_count.tif` | 0.1 MB | EPSG:32737, 30 m | Clear observations per pixel in the hot-season composite |
| `data/processed/rasters/lst_hot_season_median.tif` | 6.5 MB | EPSG:32737, 30 m | Median Jan to Mar land surface temperature, deg C |
| `data/processed/rasters/lst_hottest_clear_day.tif` | 5.9 MB | EPSG:32737, 30 m | Single usable scene with the highest county median |
| `data/processed/rasters/ndvi_hot_season_median.tif` | 8.5 MB | EPSG:32737, 30 m | Median NDVI of the hot-season scenes |
| `data/processed/rasters/population_100m.tif` | 0.9 MB | EPSG:4326, 601x408 | WorldPop 2025 constrained people per 100 m cell (native grid, EPSG:4326) |
| `data/processed/rasters/population_30m.tif` | 6.3 MB | EPSG:32737, 30 m | WorldPop 2025 people per 30 m cell, totals preserved |
| `data/processed/rasters/tree_fraction_30m.tif` | 2.1 MB | EPSG:32737, 30 m | Share of each 30 m cell that WorldCover calls tree cover |
| `data/processed/rasters/water_fraction_30m.tif` | 83 kB | EPSG:32737, 30 m | Share of each 30 m cell that is permanent water |
| `data/processed/rasters/worldcover_2021.tif` | 4.3 MB | EPSG:32737, 10 m | ESA WorldCover 2021 classes, 10 m, nested in the 30 m grid |
| `data/processed/rasters/worldcover_majority_30m.tif` | 0.7 MB | EPSG:32737, 30 m | Majority WorldCover class per 30 m cell |
| `data/processed/roni.csv` | 15 kB |  | NOAA CPC Relative Oceanic Nino Index, 3-month running mean |
| `site/public/data/nairobi_basemap.pmtiles` | 26.5 MB |  |  |
