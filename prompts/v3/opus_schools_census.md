# Opus task: census tables, school locations and heat at schools (14 November 2026)

Read CLAUDE.md, DECISIONS.md (D42 to D51) and your own last report first. Plain English in everything you write; no em dashes; no "not X, but Y"; every number traceable to a file.

## Do not touch (Claude is editing these at the same time)

`site/index.html`, everything under `site/src/`, `site/public/media/`, `site/public/figures/`, `src/animations/`. If a task below needs a change there, write what you would change in your report instead. You may add new files under `site/public/data/`.

## Decisions Stephane has made

1. **Headline:** report the two areas separately: city centre (downtown grid) and Industrial Area, each against Karura Forest and the Nairobi Arboretum. Update `analysis/results.json`, `analysis/FINDINGS.md` and the `q2` keys so the page can read `q2.CBD.median_c`, `q2.Industrial Area.median_c`, `q2.cool_areas_median_c`, and add `q2.cbd_gap_c` and `q2.industrial_gap_c`. Keep `q2.gap_c` for now, and say in your report which page text still uses it.
2. **Failing check (Nairobi National Park vs city centre):** the park is open grassland and savanna, which heats up in the dry season, so it was never a fair "cool" reference. Replace the check with one that compares the city centre with the two forests, and record why in DECISIONS.md.

## Task 1: Volume IV census tables (census repo, `kenya-2019-census-csv`)

Extract Tables 2.2 (school attendance), 2.3 (attending now, by level), 2.6b (attendance by special age groups, county only) and 2.12 (households by roofing material, by sub-county) with the same checks as Volumes II and III: totals add up, a second reading method finds every row, printing errors go to `errata.csv` with evidence. Update the README and data dictionary. Commit in the census repo; do not push.

## Task 2: Iron sheet roofs from the census (joto-mjini)

From Table 2.12, write `site/public/data/roofs_by_subcounty.csv` (Nairobi's sub-counties: share of households under iron sheets, and the other materials). In your report, say in two or three plain sentences whether it supports the roof caveat (F16): are the sub-counties with the most iron sheet roofs the ones holding the hottest wards?

## Task 3: Where Nairobi's schools are

1. Find open school locations for Nairobi County. Try, in order: the Kenya Ministry of Education or KNBS open data, the HOT OpenStreetMap "Public Facilities" / education export on HDX, OpenStreetMap (`amenity=school`, `amenity=kindergarten`, points and polygons), and UNICEF Giga school locations. Record each source, its licence, date and how many Nairobi schools it has.
2. Combine them into one de-duplicated file (schools within 50 m and with similar names are one school), keeping name, level if known (pre-primary, primary, secondary), public or private if known, and the source. Write `data/processed/nairobi_schools.geojson` and a small `site/public/data/schools.geojson`.
3. Say plainly how complete you think it is (for example, compare its count with the Ministry's published count of Nairobi schools, if you can find one).

## Task 4: Heat at schools

For each school: hot-season land surface temperature (median of the 100 m around it, from the existing hot-season composite), its difference from the city median, its ward, and whether it sits on the hottest fifth of the land. Then, by ward: number of schools, number on the hottest fifth. Write `analysis/tables/schools_heat.csv`, `site/public/data/schools_heat_by_ward.csv`, and new keys under `schools` in `analysis/results_extra.json` (total schools, schools on the hottest fifth, their share, the ten wards with the most schools on hot ground). Make one static check figure in `outputs/figures/` (not the site). Note that Landsat passes at about 10:43 in the morning, during the school day, and that this is ground temperature, not classroom temperature.

## Task 5: WorldPop scaled to the census (only if time remains)

Scale WorldPop 2025 so its total in each 2019 census sub-county matches the census total grown to 2025 with the KNBS county growth rate (state the rate and source), then recompute ward populations. Write `analysis/tables/ward_population_scaled.csv` with both numbers side by side, and say how much Woodley/Kenyatta Golf Course and the ten hottest wards change. Do not replace the numbers on the site; Stephane will decide.

## Report

Write `prompts/v3/REPORT_opus_schools_census.md`: what you did, every new file, every number that changed, sources with licences, what failed, and questions for Stephane. Commit in joto-mjini with "Census tables, schools and heat at schools"; do not push.
