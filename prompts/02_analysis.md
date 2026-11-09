# Prompt 02: analysis

## Goal

Turn the prepared data into a small set of honest, checked findings about heat in Nairobi, plus the exact data files the website needs. Code lives in `src/analysis/`, with a narrative notebook `notebooks/02_analysis.ipynb` that imports from it. Every number that may appear in the story goes into `analysis/FINDINGS.md` with its provenance.

## The questions, in story order

The story answers these in this order. Each question gets one chart or map, and one finding written as a plain sentence.

1. **Where is Nairobi hottest on a hot day?** Map the hot-season median surface temperature. Report the county median, the hottest and coolest 10 % of land, and the gap between the hottest wards and the coolest wards.
2. **How big is the gap between the hottest and the coolest places?** Compare the surface temperature of the CBD and Industrial Area with Karura Forest and the Arboretum. Report the difference in °C, computed over the actual polygons (from OSM or a clearly defined buffer), and name the exact areas used.
3. **What do the hottest places have in common?** Compare surface temperature by land cover class (WorldCover: tree cover, grassland, built-up, bare ground, water) and against tree fraction and NDVI. Show this as a binned chart (average surface temperature for each 10 % band of tree cover, with the spread), never a pie chart. Report the difference between mostly built-up cells and mostly tree-covered cells.
4. **Who lives in the hottest places?** Combine WorldPop population with surface temperature. Report how many people live in the hottest 20 % of the city's surface (by temperature), the population-weighted mean surface temperature for each ward, and the ten wards with the highest population-weighted surface temperature, with their populations.
5. **How does a park cool its neighbours?** Around Karura Forest, the Arboretum and City Park, compute average surface temperature in rings 0 to 100 m, 100 to 200 m, up to 1,000 m outside the park edge, built-up cells only. Report how far the cooler band reaches and by how much it is cooler, if the data shows it. If the signal is weak or noisy, say so plainly.
6. **Is it getting hotter as the city grows?** Using the January to March composites by year and GHSL built-up growth, show the county median hot-season surface temperature per year and the growth in built-up area. Be careful: Landsat surface temperature varies a lot between years because of weather on the day, so treat the yearly series as indicative, report the number of scenes behind each year, and do not claim a trend unless it is clear and you state the method (Theil-Sen slope with a Mann-Kendall test is a good choice). If there is no clear trend, say "the data does not show a clear trend" and keep the built-up growth as the finding.
7. **How unequal is the heat?** The project's subtitle is "Mapping urban heat and cooling inequality across Nairobi", so measure the inequality the data can actually support: the spread in population-weighted surface temperature between the hottest and coolest fifth of wards; tree cover share in the hottest fifth of wards against the coolest fifth; and, only if you can obtain an open layer of irregular or informal settlements (for example WRI's Global Intra-Urban Land Use dataset, Guzder-Williams et al. 2023), the difference in surface temperature and tree cover between settlement and non-settlement areas. Without income or poverty data, describe differences between places and their people's exposure; do not make claims about income or wealth. Record any ward-level poverty data you find in `QUESTIONS.md` for Stephane to decide on, rather than using it tonight.
8. **Hot one day, cool the next.** From the Open-Meteo daily air temperature series, compute for 2023 to now: the average day-to-day change in daily maximum, the number of days above the 1991 to 2020 90th percentile per year, and mark the months since El Niño began (May 2026). This is city-scale air temperature; label it so and keep it separate from surface temperature.

## Outputs for the website (`site/public/data/`)

1. **Ward layer** `wards.geojson` (EPSG:4326, simplified to keep it under 2 MB): `ward_id`, `ward_name`, `lst_median_c`, `lst_p90_c`, `lst_anomaly_c` (ward median minus county median), `pop_total`, `pop_weighted_lst_c`, `tree_pct`, `built_pct`, `ndvi_median`, `rank_hottest`, `n_buildings`. Round temperatures to one decimal.
2. **Buildings** `buildings.pmtiles`: vector tiles built with `tippecanoe` from the Overture footprints, with attributes `lst_c` (surface temperature sampled at the building centroid from the hot-season composite) and `lst_anomaly_c`. Zoom range about 12 to 16. Keep the file under 100 MB (GitHub's limit); if it is larger, drop small footprints at low zoom with tippecanoe's options and record what you did.
3. **Raster layers** as raster PMTiles (WebP or PNG tiles, zoom about 9 to 15) with the colour ramps from `prompts/03_story_site.md` baked in, plus a matching legend JSON with the value breaks:
   - `lst_hot_season.pmtiles` (sequential heat ramp, fixed breaks, the same breaks for every surface temperature layer so maps can be compared);
   - `lst_cool_season.pmtiles` (same ramp and breaks);
   - `lst_anomaly.pmtiles` (diverging ramp, centred on the county median);
   - `tree_fraction.pmtiles` (green sequential ramp);
   - `ghsl_built_<year>.pmtiles` for two epochs used in the compare map (for example 1990 and 2020);
   - `population.pmtiles` (sequential ramp).
   Use `rio-pmtiles` or GDAL's PMTiles driver. Keep transparent no-data.
4. **Chart data** as small CSVs: `lst_by_landcover.csv`, `lst_by_tree_band.csv`, `park_rings.csv`, `hot_season_by_year.csv`, `daily_air_temp_2023_now.csv` (with an `el_nino` flag column), `top_wards.csv`.
5. **Static fallbacks** (for the no-JavaScript view and for slides): `outputs/figures/` PNG and SVG of the hero map, the land-cover chart and the top-wards table, drawn with matplotlib using the project palette and typefaces from prompt 03.
6. **Places** `places.geojson` copied from `data/processed/nairobi_places.geojson`, filtered to the names used in the story plus labels for the explorer.

## `analysis/FINDINGS.md` format

Number each finding. For each one:

```
### F3. Built-up ground was much hotter than tree cover
Sentence for the story: On hot days, built-up ground in Nairobi was on average X.X °C hotter at the surface than land under tree cover.
Number(s): X.X °C (built-up median 41.2 °C; tree cover median 33.9 °C)
Method: median of hot-season composite pixels by WorldCover class, county only, 30 m grid
Data: data/processed/rasters/lst_hot_season_median.tif, worldcover_2021.tif
Script: src/analysis/landcover.py, function lst_by_class
Caveats: surface temperature, not air temperature; 100 m sensor resolution; WorldCover 2021 vs composite years 2023 to 2026
Confidence: high / medium / low, with one line why
```

(The numbers above are a format example only. Never copy them into the story.)

Also add a short "What the data cannot tell us" section: air temperature at street level, night-time heat (Landsat passes in the morning), indoor heat, and anything else you notice.

## Checks before you finish

- Recompute three headline numbers with an independent method (for example, numpy directly versus your zonal-statistics function) and record that they match.
- Spot-check: the cool places (Karura, Arboretum, Nairobi National Park, the dams) must come out cooler than the CBD and Industrial Area. If they do not, something is wrong with the mask, the scaling or the alignment; find it before moving on.
- Confirm the ward population totals add up to within 5 % of the county total and note the county total and its WorldPop year.
- Notebook `notebooks/02_analysis.ipynb` executes top to bottom.
- Update `PROGRESS.md` and commit "Phase 2: analysis".

## If time remains (optional, in this order)

1. If a Cool Cities Lab layer was downloadable, compare its Nairobi surface temperature or heat risk index with ours, ward by ward, and report the correlation.
2. A cool-season versus hot-season difference map.
3. Kisumu, if prompt 01 fetched it.
