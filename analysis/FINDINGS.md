# Findings

Every number that may appear in the story, with where it came from. Generated 2026-11-10 03:47 (Africa/Nairobi) by `src/analysis/findings.py` from `analysis/results.json` (written by `src/analysis/core.py`). Do not edit numbers by hand; change the code and re-run.

**Hot-season composite:** median of 12 clear Landsat 8 and 9 scenes, January to March, 2023 to 2026 (2023-01-19, 2023-02-04, 2023-02-12, 2023-02-20, 2023-03-08, 2024-02-15, 2025-01-08, 2025-02-09, 2026-01-03, 2026-01-11, 2026-01-27, 2026-02-12). **Cool-season composite:** 4 scenes, June to August, 2018 to 2026 (2018-08-25, 2020-08-30, 2024-06-14, 2026-07-14). All temperatures below are land surface temperature unless the finding says air temperature.

### F1. On hot mornings, half of Nairobi's ground was hotter than 38.7 °C

- **Sentence for the story:** On clear January to March mornings, half of Nairobi County's ground was hotter than 38.7 °C at the surface. The hottest tenth of the land averaged 44.9 °C; the coolest tenth averaged 29.3 °C.
- **Number(s):** county median 38.7 °C; 10th percentile 31.6 °C; 90th percentile 43.3 °C; mean of hottest 10 % 44.9 °C; mean of coolest 10 % 29.3 °C; 99.6 % of county cells have a value
- **Method:** Median and percentiles of all 30 m cells whose centre is in the county, hot-season composite
- **Data:** data/processed/rasters/lst_hot_season_median.tif, data/processed/nairobi_boundary.geojson
- **Script:** src/analysis/core.py, q1_where_hottest
- **Caveats:** Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15).
- **Confidence:** High. Recomputed independently with a rioxarray clip: 38.7 °C.

### F2. The hottest wards were 7.2 °C hotter than the coolest

- **Sentence for the story:** Ruai was the hottest ward at the surface (42.4 °C) and Karen the coolest (32.3 °C). The 8 hottest wards averaged 41.8 °C, 7.2 °C more than the 8 coolest (34.6 °C).
- **Number(s):** hottest wards: Ruai 42.4, Embakasi 42.1, Kangemi 42.0, Viwandani 41.9, Mwiki 41.8, Kawangware 41.6, Dandora Area I 41.4, Babadogo 41.4; coolest wards: Karen 32.3, Karura 33.0, Kitisuru 33.6, Uthiru/Ruthimitu 34.7, Mutuini 35.1, Kileleshwa 35.7, Parklands/Highridge 36.1, Roysambu 36.2 (°C, ward medians)
- **Method:** Median of 30 m cells whose centre lies in each ward; mean of the top and bottom tenth of wards (8 each)
- **Data:** data/processed/rasters/lst_hot_season_median.tif, data/processed/nairobi_wards.geojson
- **Script:** src/analysis/core.py, ward_table and q1_where_hottest
- **Caveats:** Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15). Ward medians include all land in the ward (homes, roads, open ground, forest). Ruai and Embakasi contain large open and bare areas (and the airport in Embakasi) as well as homes.
- **Confidence:** High for the numbers (exactextract coverage-weighted medians give the same ranking, Spearman 1.0). Medium for interpretation, because ward medians mix land uses.

### F3. The city centre and Industrial Area were 12.8 °C hotter than Karura and the Arboretum

- **Sentence for the story:** On hot mornings, the ground in the city centre and Industrial Area (40.5 °C) was 12.8 °C hotter than Karura Forest and the Nairobi Arboretum (27.6 °C).
- **Number(s):** CBD 38.8 °C; Industrial Area 41.3 °C; Karura Forest 27.5 °C; Nairobi Arboretum 28.8 °C; combined gap 12.8 °C; Industrial Area minus Karura 13.8 °C; CBD minus Arboretum 10.0 °C. Cool season: CBD 36.7 °C, Karura 24.8 °C
- **Method:** Median of 30 m cells in each area. Areas: CBD = 750 m circle around -1.284, 36.824; Industrial Area = 1000 m circle around the OSM place 'Industrial Area' (-1.3045, 36.8442); Karura = OSM polygon 'Karura Forest' (landuse=forest); Arboretum = OSM polygon 'Nairobi Arboretum' (landuse=forest). Combined values pool the cells of the two areas in each group.
- **Data:** data/processed/rasters/lst_hot_season_median.tif, data/processed/comparison_areas.geojson (the exact shapes used)
- **Script:** src/analysis/core.py, q2_gap
- **Caveats:** Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15). Under a forest canopy the satellite sees the top of the trees, not the ground below.
- **Confidence:** High. Karura recomputed by a windowed read: 27.5 °C.

### F4. Built-up cells were 7.8 °C hotter than tree-covered cells

- **Sentence for the story:** On hot mornings, mostly built-up ground was on average 7.8 °C hotter at the surface than ground mostly under trees. Areas with more trees were cooler: the hot-season surface temperature fell from 39.9 °C where tree cover was under 10 % to 31.5 °C where it was over 90 %.
- **Number(s):** cells at least 75 % built-up: median 39.8 °C (212,215 cells); cells at least 75 % tree cover: median 31.9 °C (134,784 cells); tree band 0 to 10 % mean 39.9 °C, 90 to 100 % mean 31.5 °C (difference 8.4 °C); Spearman correlation with NDVI -0.75, with tree share -0.63
- **Method:** WorldCover 10 m classes counted inside each 30 m cell; medians of hot-season surface temperature; means for each 10 % band of tree cover (table analysis/tables/lst_by_tree_band.csv)
- **Data:** data/processed/rasters/lst_hot_season_median.tif, data/processed/rasters/tree_fraction_30m.tif, built_fraction_30m.tif, ndvi_hot_season_median.tif
- **Script:** src/analysis/core.py, q3_landcover
- **Caveats:** Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15). WorldCover is from 2021; the composite is 2023 to 2026. This is an association: places with trees differ in other ways too (height, slope, soil moisture, how they are used). It does not show how much planting trees would cool a place.
- **Confidence:** High for the association; the method does not support a causal number.

### F5. Dry grass and bare ground were as hot as roofs and roads

- **Sentence for the story:** In the dry months, open ground heated up as much as built-up land: grassland (40.1 °C), farmland (41.0 °C) and bare ground (41.4 °C) were as hot as or hotter than built-up land (39.7 °C). Only trees (32.6 °C) and water (28.3 °C) were clearly cooler.
- **Number(s):** Bare or sparse vegetation 41.4 °C (1.0 % of county); Cropland 41.0 °C (4.9 % of county); Grassland 40.1 °C (30.2 % of county); Built-up 39.7 °C (31.7 % of county); Shrubland 36.8 °C (10.5 % of county); Tree cover 32.6 °C (21.0 % of county); Water 28.3 °C (0.6 % of county)
- **Method:** Median hot-season surface temperature of 30 m cells by their majority WorldCover class
- **Data:** data/processed/rasters/lst_hot_season_median.tif, data/processed/rasters/worldcover_majority_30m.tif
- **Script:** src/analysis/core.py, q3_landcover
- **Caveats:** Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15). Dry grass is hot at the surface in January to March; in the wet season it is cooler. This is why Nairobi National Park (mostly grassland) is not among the coolest places on these maps.
- **Confidence:** High.

### F6. About 827,000 people live on the hottest fifth of the county's ground

- **Sentence for the story:** About 827,000 people, 14.6 % of the county's estimated population, live on the hottest fifth of Nairobi's land (surface above 41.6 °C on hot mornings). The ground under the average resident was 39.4 °C, warmer than the average for all county land (38.1 °C).
- **Number(s):** 827,000 people (rounded to the nearest 1,000); 14.6 % of 5,657,304; threshold 41.6 °C; population-weighted mean 39.4 °C; area mean 38.1 °C
- **Method:** Hottest 20 % of county 30 m cells by hot-season surface temperature; WorldPop 2025 people summed in those cells; population-weighted mean over all county cells
- **Data:** data/processed/rasters/lst_hot_season_median.tif, data/processed/rasters/population_30m.tif
- **Script:** src/analysis/core.py, q4_exposure
- **Caveats:** Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15). WorldPop is a modelled estimate (2025, constrained to mapped buildings). It may undercount the densest informal settlements. The hottest fifth of land also includes the airport and open plains in the east, where few people live, so the share of people (under 20 %) is lower than the share of land.
- **Confidence:** High for the arithmetic (recomputed with xarray: 827,000); medium for the population estimate itself.

### F7. Ten wards where people live on the hottest ground

- **Sentence for the story:** Weighted by where people live, the hottest wards were Viwandani, Kangemi, Kawangware, Dandora Area I, Babadogo, Kayole South, Kiamaiko, Kariobangi North, Dandora Area II and Upper Savannah. Together they are home to about 348,000 people. None of them has more than 12.5 % of its land under trees.
- **Number(s):** Viwandani 42.2 °C, 49,100 people; Kangemi 42.2 °C, 11,700 people; Kawangware 41.9 °C, 56,500 people; Dandora Area I 41.7 °C, 12,900 people; Babadogo 41.4 °C, 42,500 people; Kayole South 41.4 °C, 38,200 people; Kiamaiko 41.3 °C, 45,700 people; Kariobangi North 41.3 °C, 39,100 people; Dandora Area II 41.2 °C, 28,600 people; Upper Savannah 41.2 °C, 23,200 people
- **Method:** Population-weighted mean of hot-season surface temperature over the 30 m cells of each ward (weights: WorldPop 2025 people per cell); populations rounded to the nearest 100
- **Data:** data/processed/rasters/lst_hot_season_median.tif, data/processed/rasters/population_30m.tif, data/processed/nairobi_wards.geojson
- **Script:** src/analysis/core.py, q4_exposure (table analysis/tables/top_wards.csv)
- **Caveats:** Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15). Several of these wards are small; the ward boundaries come from a community-made layer (geoBoundaries ADM3), not from the IEBC directly. Ward populations are modelled, not census counts.
- **Confidence:** Medium: the ranking is robust (ward totals add to within 2.4 % of the county total) but small differences (0.1 °C) between neighbouring ranks are not meaningful.

### F8. People in the hottest fifth of wards lived on ground 4.4 °C hotter, with a tenth of the tree cover

- **Sentence for the story:** Residents of the hottest fifth of wards lived, on average, on ground 4.4 °C hotter than residents of the coolest fifth (41.1 °C against 36.7 °C). Those hotter wards had 3.3 % tree cover; the cooler wards had 36.1 %.
- **Number(s):** hottest fifth: 17 wards, about 1,105,000 people, 41.1 °C, tree cover 3.3 %, built-up 34.7 %, 8,700 people per km²; coolest fifth: 17 wards, about 1,333,000 people, 36.7 °C, tree cover 36.1 %, built-up 18.7 %, 3,900 people per km²; gap 4.4 °C; tree cover ratio 10.9
- **Method:** Wards ranked by population-weighted surface temperature; top and bottom 17 wards; group temperature weighted by population, tree and built-up shares weighted by ward area
- **Data:** data/processed/rasters/lst_hot_season_median.tif, tree_fraction_30m.tif, built_fraction_30m.tif, population_30m.tif
- **Script:** src/analysis/core.py, q7_inequality
- **Caveats:** Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15). This compares places and the exposure of the people who live there. It says nothing about income or wealth; no open ward-level income data was used. The coolest fifth includes large leafy wards (Karen, Karura, Kitisuru) and some dense central wards. No settlement-level comparison: no open informal-settlement layer could be downloaded (DECISIONS D9). Hottest fifth: Viwandani, Kangemi, Kawangware, Dandora Area I, Babadogo, Kayole South, Kiamaiko, Kariobangi North, Dandora Area II, Upper Savannah, Landimawe, Imara Daima, Kayole Central, Dandora Area III, Harambee, Ruai, Lindi. Coolest fifth: Pangani, Mugumo-Ini, California, Woodley/Kenyatta Golf, Mlango Kubwa, Zimmerman, Eastleigh North, Waithaka, Uthiru/Ruthimitu, Roysambu, Kilimani, Kileleshwa, Parklands/Highridge, Mutuini, Karura, Kitisuru, Karen.
- **Confidence:** Medium: the direction is clear; the size depends on how wards are grouped.

### F9. Built-up land next to Karura Forest was a little cooler; the difference faded within about 500 m

- **Sentence for the story:** Built-up land within 100 m of Karura Forest was 2.1 °C cooler at the surface than built-up land 700 to 1,000 m away (35.5 °C against 37.6 °C). Around the Arboretum and City Park the difference was about 1 °C and faded within about 200 m.
- **Number(s):** Karura: 0 to 100 m 35.5 °C, 700 to 1,000 m 37.6 °C, difference -2.1 °C, within 0.5 °C of the far band by 500 m. Arboretum: 35.7 °C vs 36.8 °C (-1.1 °C), by 200 m. City Park: 37.4 °C vs 38.3 °C (-0.9 °C), by 200 m
- **Method:** Built-up cells (WorldCover built-up share >= 50 %, tree share < 30 %) outside all OSM parks and forests, in 100 m rings out to 1,000 m from the park edge; medians of hot-season surface temperature; 'reach' is the first ring within 0.5 C of the 700 to 1,000 m band.
- **Data:** data/processed/rasters/lst_hot_season_median.tif, built_fraction_30m.tif, tree_fraction_30m.tif, data/processed/nairobi_places.geojson
- **Script:** src/analysis/core.py, q5_park_rings (table analysis/tables/park_rings.csv)
- **Caveats:** Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15). The 100 m sensor footprint blurs the first ring, so part of the edge effect may be the park itself showing through. Neighbourhoods next to these parks also differ in other ways (larger plots, more garden trees). The rings around Karura do not rise smoothly. Treat as indicative.
- **Confidence:** Low to medium: a consistent sign at all three parks, but small and noisy; do not quote as a cooling distance.

### F10. Nairobi's built-up area grew by half between 1990 and 2020; the surface temperature record shows no clear trend

- **Sentence for the story:** Between 1990 and 2020, built-up surface in Nairobi County grew from about 66 km² to about 101 km², around 1.5 times as much. The yearly satellite readings of hot-season surface temperature jump up and down with the weather and do not show a clear trend.
- **Number(s):** GHSL built-up surface in the county: 1975 48.1 km², 1990 65.8 km², 2000 82.2 km², 2010 91.1 km², 2020 100.8 km², 2025 103.0 km² (2025 is a JRC projection); growth 1990 to 2020 35.0 km²; share of county 9.3 % in 1990, 14.3 % in 2020. Yearly county medians: 2015 38.5 (2 scenes), 2016 36.8 (2 scenes), 2017 37.9 (3 scenes), 2018 39.4 (2 scenes), 2019 41.8 (2 scenes), 2020 35.8 (3 scenes), 2021 38.7 (3 scenes), 2022 40.0 (5 scenes), 2023 43.0 (5 scenes), 2025 35.1 (2 scenes), 2026 35.6 (4 scenes). Mann-Kendall: no trend, p = 1.0; Theil-Sen slope -0.3 °C per decade (95 % range -6.0 to 8.2)
- **Method:** GHSL built-up surface summed over 90 m cells in the county; January to March composites per year with at least 2 usable scenes; Mann-Kendall test and Theil-Sen slope on the yearly county medians
- **Data:** data/processed/rasters/ghsl_built_<year>.tif, data/processed/rasters/lst_hot_season_by_year/<year>.tif
- **Script:** src/analysis/core.py, q6_trend (tables hot_season_by_year.csv, ghsl_built_by_epoch.csv)
- **Caveats:** Each year rests on 2 to 5 scenes, so weather on those days dominates. 2024 has no composite (one usable scene). GHSL is a modelled product at 100 m; it counts built surface, not buildings. Do not compare yearly surface temperature medians as if they were a climate record.
- **Confidence:** High for the built-up growth; high that the satellite series shows no clear trend (and that this is not evidence of no warming).

### F11. The same places were hot in both seasons

- **Sentence for the story:** In the cooler June to August months the county median surface temperature was 34.9 °C, against 38.7 °C in January to March. The places that were hot in one season were mostly hot in the other (ward rank correlation 0.75).
- **Number(s):** cool season county median 34.9 °C; hot season 38.7 °C; Karura cool season 24.8 °C; CBD cool season 36.7 °C; Spearman correlation hot vs cool season: 30 m cells 0.9, ward medians 0.75
- **Method:** Median of county cells in each composite; Spearman rank correlation between the two composites over every 7th valid county cell and over the 85 ward medians
- **Data:** data/processed/rasters/lst_hot_season_median.tif, data/processed/rasters/lst_cool_season_median.tif
- **Script:** src/analysis/core.py, q1_where_hottest and q2_gap
- **Caveats:** Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15). The cool-season composite has only 4 scenes from four different years (2018 to 2026) because the cool season is cloudy. Rank correlation measures whether places keep their order, not whether the gaps stay the same size.
- **Confidence:** Medium.

### F12. Air temperature: hot one day, cooler the next

- **Sentence for the story:** Nairobi's daily high air temperature changed by 1.1 °C from one day to the next on average since January 2023, and by 3 °C or more on 68 days. Since El Niño conditions began in May 2026, daily highs averaged 25.0 °C, 1.7 °C above the 1991 to 2020 average for the same months.
- **Number(s):** mean absolute day-to-day change in daily maximum 1.1 °C; largest 6.6 °C; days with a change of 3 °C or more 68 (4.8 %); 90th percentile of daily maximum 1991 to 2020 27.2 °C; days above it: 2023 84, 2024 94, 2025 72, 2026 64 (2026 to 2026-11-09); El Niño period 2026-05-01 to 2026-11-09: mean daily maximum 25.0 °C vs 23.2 °C for the same months in 1991 to 2020; highest daily maximum since 2023 31.4 °C on 2026-01-25
- **Method:** Daily series from Open-Meteo (ERA5 reanalysis) for the grid cell over central Nairobi; El Niño period starts 1 May 2026 (RONI first at or above +0.5 °C in AMJ 2026)
- **Data:** data/processed/nairobi_daily_air_temp.csv, data/processed/roni.csv
- **Script:** src/analysis/core.py, q8_air
- **Caveats:** Air temperature from a weather model for a grid cell about 10 to 30 km across, not a station and not surface temperature. The El Niño comparison is an association for one season; it does not show that El Niño caused the warmth. The 2026 El Niño period does not yet include December.
- **Confidence:** High for the arithmetic; medium for what ERA5 says about street-level air temperature.

### F13. The hottest clear morning in the record

- **Sentence for the story:** The hottest clear Landsat morning since 2013 was 29 September 2022, when the county median surface temperature was 46.6 °C.
- **Number(s):** 2022-09-29, scene LC09_L2SP_168061_20220929_02_T1, county median 46.6 °C
- **Method:** Usable scene (at least 80 % of county clear) with the highest county median
- **Data:** data/processed/landsat_scene_catalogue.csv, data/processed/rasters/lst_hottest_clear_day.tif
- **Script:** src/pipeline/s2b_composites.py, main
- **Caveats:** Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15). One scene; a September date, so it is outside the January to March season used elsewhere.
- **Confidence:** High for the number; it is one morning.

### F14. Leafy Kileleshwa and dense Kawangware, 1.3 km apart, differed by 5.9 °C

- **Sentence for the story:** Kawangware, where about 30,300 people live per square kilometre, had a median surface temperature of 41.6 °C on hot mornings and 10 % tree cover. Kileleshwa, 1.3 km away at the nearest point, had 35.7 °C and 48 % tree cover.
- **Number(s):** Kawangware: 41.6 °C, tree cover 9.9 %, built-up 86.4 %, about 56,500 people on 1.9 km² (30,300 per km²), rank 6 of 85. Kileleshwa: 35.7 °C, tree cover 48.4 %, built-up 46.8 %, about 41,800 people on 9.3 km² (4,500 per km²), rank 80. Gap 5.9 °C; nearest distance between ward boundaries 1.3 km
- **Method:** Ward medians and shares as in F2 and F4; distance between ward polygons in UTM 37S
- **Data:** data/processed/rasters/lst_hot_season_median.tif, tree_fraction_30m.tif, built_fraction_30m.tif, population_30m.tif, nairobi_wards.geojson
- **Script:** src/analysis/core.py, q9_pair
- **Caveats:** Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15). Two wards chosen to illustrate a contrast (Kileleshwa includes Lavington); they are not a random sample. Ward populations are modelled.
- **Confidence:** High for the numbers; the pair was chosen, so it illustrates F4 and F8 rather than proving them.

### F15. What the satellite record contains

- **Sentence for the story:** We checked 205 Landsat 8 and 9 passes over Nairobi between 7 April 2013 and 26 October 2026; 68 were clear enough to use. The satellites pass at about 10:43 in the morning, Nairobi time.
- **Number(s):** 205 scenes with under 40 % cloud for the whole scene; 68 with at least 80 % of the county clear; 51.5 % of usable scenes fall in January to March; mean local overpass time of the hot-season scenes 10:43; hot-season composite 12 scenes; cool-season composite 4 scenes from 2018
- **Method:** STAC search of landsat-c2-l2 on Planetary Computer, cloud mask from qa_pixel
- **Data:** data/processed/landsat_scene_catalogue.csv, data/processed/composites_meta.json
- **Script:** src/pipeline/s2_landsat.py, src/pipeline/s2b_composites.py, src/analysis/core.py q0_data
- **Caveats:** Scenes with more than 40 % cloud over the whole scene were not searched.
- **Confidence:** High.

## Optional findings (prompt 02, 'if time remains')

Not used in the story yet. Written by `src/analysis/extras.py` to `analysis/results_extra.json`.

### E1. The ground was hotter in January to March almost everywhere; a few wards changed by under 1 °C

- **Sentence for the story:** Almost all of Nairobi's ground (98.9 %) was hotter on January to March mornings than on June to August mornings, by 3.6 °C at the median. The smallest change was in wards such as Ngei, Eastleigh North, Mlango Kubwa, where it was under 1 °C.
- **Number(s):** county median difference 3.6 °C; 98.9 % of cells hotter in the hot season; 64.8 % more than 3 °C hotter; largest ward differences: Kangemi 5.4 °C, Mountain View 5.2 °C, Ruai 5.0 °C, Uthiru/Ruthimitu 4.7 °C, Mwiki 4.4 °C; smallest: Mabatini 0.9 °C, Pumwani 0.7 °C, Mlango Kubwa 0.7 °C, Eastleigh North 0.6 °C, Ngei 0.1 °C
- **Method:** Hot-season composite minus cool-season composite, cell by cell; ward medians of the difference
- **Data:** data/processed/rasters/lst_hot_minus_cool.tif (figure outputs/figures/map_hot_minus_cool.png)
- **Script:** src/analysis/extras.py, season_difference
- **Caveats:** Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15). The cool-season composite has only 4 scenes from four different years, so differences partly reflect the weather on those days. A small seasonal change can mean a place stays hot all year, or that it was relatively cool in the hot season; read it with F2 and F8.
- **Confidence:** Medium: the direction is clear; the size per ward rests on 4 cool-season scenes.

### E2. Kisumu: half of the ground was hotter than 35.6 °C on hot-season mornings

- **Sentence for the story:** In Kisumu, half of the land was hotter than 35.6 °C at the surface on clear January to March mornings. Mostly built-up ground was 39.0 °C and ground mostly under trees 33.9 °C.
- **Number(s):** median 35.6 °C; 10th percentile 31.7 °C; 90th 39.9 °C; 54 scenes from 2023; 100.0 % of cells with a value; population about 1,327,000; people-weighted 36.7 °C; hottest wards: Kondele 41.4 °C, Manyatta 'B' 40.6 °C, East Kano/Wawidhi 39.7 °C, Migosi 39.4 °C, Kobura 39.3 °C; coolest: Nyalenda 'A' 33.0 °C, Kajulu 32.9 °C, Kabonyo/Kanyagwal 32.2 °C, North West Kisumu 31.6 °C, Kisumu North 31.5 °C
- **Method:** Same pipeline as Nairobi with JOTO_CITY=kisumu (DECISIONS D28); medians over the land area of the 35 wards
- **Data:** data/processed/kisumu/rasters/*.tif, data/processed/kisumu/kisumu_wards.geojson
- **Script:** src/pipeline/*.py with JOTO_CITY=kisumu; src/analysis/extras.py, kisumu_summary
- **Caveats:** Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15). Kisumu is mostly rural outside the city, so county-wide numbers are not comparable with Nairobi's directly; scenes come from three Landsat paths on different days.
- **Confidence:** Medium: first pass, not yet checked by an independent method.

## Checks

Recorded in `analysis/checks.json` by `src/analysis/checks.py`:

- **county_median:** {"core": 38.7, "independent": 38.7, "method": "rioxarray clip of the composite vs rasterio rasterize mask", "match": true}
- **hottest_ward:** {"ward": "Ruai", "core": 42.4, "independent": 42.4, "method": "exactextract coverage-weighted median vs cell-centre median", "match": true}
- **coolest_ward:** {"ward": "Karen", "core": 32.3, "independent": 32.3, "method": "exactextract coverage-weighted median vs cell-centre median", "match": true}
- **ward_rank_agreement_spearman:** 1.0
- **karura_median:** {"core": 27.5, "independent": 27.5, "method": "windowed numpy read with geometry_mask vs full-grid mask", "match": true}
- **pop_hottest20:** {"core": 827000, "independent": 827000, "method": "xarray clip and threshold vs numpy mask", "match": true}
- **spot_cool_places:** {"values": {"Karura Forest": 27.5, "Nairobi Arboretum": 28.8, "Nairobi National Park": 37.8, "Nairobi Dam": 34.1, "City Park": 31.4}, "cbd": 38.8, "industrial": 41.3, "all_cooler": true}
- **ward_pop_sum:** {"ward_sum": 5521712, "county": 5657304, "diff_pct": -2.4, "within_5pct": true, "worldpop_year": 2025}

## What the data cannot tell us

- **The air people breathe and feel.** Landsat measures how hot surfaces are (roofs, roads, soil, tree tops), not the air temperature at head height. On a sunny morning the two can differ by more than 10 °C. Shade, wind and humidity also change how heat feels.
- **Night-time heat.** Landsat passes over Nairobi at about 10:43 in the morning (F15). It says nothing about how slowly places cool down at night, which matters for sleep and health.
- **Afternoon peaks.** Surfaces are usually hotter in the early afternoon than at the time of the overpass.
- **Indoor heat.** Temperature inside homes, especially under iron sheet roofs, is not measured here.
- **Detail finer than about 100 m.** The thermal sensor sees areas of about 100 m; a value at a single building describes the area around it.
- **Why a place is hot.** These are associations with land cover, trees and buildings, not measured causes.
- **Who is most at risk.** Heat risk also depends on age, health, work, housing and access to water and cooling. This analysis has none of these.
- **Exact populations.** WorldPop numbers are modelled estimates and may undercount the densest settlements.
- **Change over time in surface temperature.** Too few clear scenes per year to separate a warming trend from day-to-day weather.
- **Rainfall, flooding and El Niño impacts.** Planned for a later phase.
