# Report: census tables, school locations and heat at schools (14 November 2026)

All five tasks and both of your decisions are done. Nothing on the site changes until the page text is updated: I did not touch `site/index.html`, `site/src/`, `site/public/media/`, `site/public/figures/` or `src/animations/`.

## Your decisions

### Headline: the two areas reported separately (D52)

The page can now read these keys in `analysis/results.json`:

| Key | Value |
|---|---|
| `q2.CBD.median_c` | 37.8 °C (downtown grid, D51) |
| `q2.Industrial Area.median_c` | 41.5 °C |
| `q2.cool_areas_median_c` | 27.6 °C (Karura Forest and the Nairobi Arboretum, cells pooled) |
| `q2.cbd_gap_c` (new) | 10.2 °C |
| `q2.industrial_gap_c` (new) | 13.9 °C |
| `q2.gap_c` (kept) | 13.5 °C (pooled) |

F3 in `analysis/FINDINGS.md` now reads "The Industrial Area was 13.9 °C and the city centre 10.2 °C hotter than Karura and the Arboretum". No other value in `results.json` changed.

**Page text that still uses `q2.gap_c`** (Claude's files, not changed by me):

1. `site/index.html` line 7, the meta description: "the ground in central Nairobi is {{q2.gap_c|c}} hotter than in its forests".
2. `site/index.html` line 32, the H1: "On hot mornings, central Nairobi's ground is {{q2.gap_c|c}} hotter than its forests".
3. `site/src/story/chapters.js` line 118, the "Difference" row of the city centre card.
4. `site/src/story/chapters.js` line 120, the card note, which also uses `q2.hot_areas_median_c` (41.1 °C, pooled).

Suggested change: replace the "Difference" row with two rows, "City centre: {{q2.cbd_gap_c|c}} hotter" and "Industrial Area: {{q2.industrial_gap_c|c}} hotter". For the H1, "the Industrial Area's ground is {{q2.industrial_gap_c|c}} hotter than its forests" keeps the larger figure honestly. Then `q2.gap_c` and `q2.hot_areas_median_c` can be retired.

### The failing check (D52)

The old check asked every listed "cool place" to be cooler than the city centre, and failed on Nairobi National Park (37.8 °C). The new check, `forests_cooler_than_hot_areas` in `analysis/checks.json`, compares Karura Forest (27.5 °C) and the Arboretum (28.8 °C), read independently, with both hot areas. It passes. The National Park, Nairobi Dam (34.1 °C) and City Park (31.4 °C) are still recorded, for information. All analysis checks pass.

## Task 1: Volume IV census tables

Committed in `~/Desktop/kenya-2019-census-csv` as **89a4594**, not pushed.

| Table | File in `data/csv/` | Rows |
|---|---|---|
| 2.2 school attendance (at school, left school, never attended) | `kenya_2019_census_school_attendance_by_county_subcounty.csv` | 1,182 |
| 2.3 attending now, by level | `kenya_2019_census_school_attendance_by_education_level_county_subcounty.csv` | 1,182 |
| 2.6b attendance by special age groups (county only) | `kenya_2019_census_school_attendance_by_age_group_county.csv` | 376 |
| 2.12 households by roofing material (per cent) | `kenya_2019_census_roofing_material_by_county_subcounty.csv` | 395 |
| Volume IV against Volume III, people aged 3 and over | `volume4_vs_volume3_aged_3_plus.csv` | |

Each area has rows for all, male and female (Kenya also rural, urban and intersex), for 47 counties and 345 sub-counties.

**Checks that pass:** statuses and levels add up to their totals; printed per cents match the counts; every county equals the sum of its sub-counties; table 2.6b county rows equal table 2.2; roofing households equal Volume II conventional households; roofing per cents sum to 100 within 0.5. The independent plain-text test finds all 3,135 Volume IV rows. README, data dictionary and `data/raw/README.md` are updated.

**Problems found** (left as printed, in `known_issues.csv`; no new errata were needed):

- Table 2.2 "at school" and table 2.3 "total attending" differ by 1 person in Butere, Limuru, Thika West and Buna, in their counties, and in Kenya's rural and urban rows.
- Two rows on pages 61 and 62 (Mandera) print "- 0 -" with no label; they are left out.
- Volume IV has 338,960 fewer people aged 3 and over than Volume III (0.77 %). Volume IV page 16 says the special population (travellers, outdoor sleepers, people in hotels, lodges, schools and hospitals) was counted on short questionnaires, so Volume IV most likely covers only the main questionnaire. That is our reading; KNBS does not state it outright. In Nairobi the gap is largest in Starehe (15,497 people).

## Task 2: iron sheet roofs from the census

File: `site/public/data/roofs_by_subcounty.csv` (Nairobi and its 11 census sub-counties; conventional households and all 13 roofing materials, iron sheets first; source and page columns). Script: `src/analysis/roofs_census.py`. Finding R1.

In 2019, 51.3 % of Nairobi's 1,494,676 conventional households had iron sheet roofs, from 38.0 % in Embakasi to 80.6 % in Dagoretti.

**Does it support the roof caveat (F16)?** The census neither supports nor refutes it. The sub-counties with the most iron sheet roofs, Dagoretti (80.6 %) and Kibra (79.4 %), average 37.1 °C and 38.4 °C across their wards, while the hottest, Embakasi (42.2 °C) and Njiru (42.0 °C), have more concrete roofs and large areas of open dry ground; across the 11 sub-counties there is no relationship (Spearman rho −0.12, p 0.73). Census sub-counties are too large and mixed to test a ward-level caveat, so F16 stands as written.

## Task 3: where Nairobi's schools are

**Sources** (details and licences in `data/SOURCES.md`, method in D53):

| Source | Licence | Date | Nairobi count | Used? |
|---|---|---|---|---|
| Ministry of Education list via the World Bank (energydata.info) | CC BY 4.0 | records from 2016 and 2007 | 2,156 in the county | Yes, read from the public vector tiles (the file download is behind a bot check) |
| OpenStreetMap via Overpass | ODbL | 14 November 2026 | 2,406 | Yes |
| HOT education export (HDX) | ODbL | 2 November 2026 | 2,405 | No: the same OSM data |
| Open Schools Kenya (open.africa) | ODbL | 2023 | 1,138 | No: an older OSM extract |
| opendata.go.ke primary schools 2007 | | 2007 | | Failed: dead link |
| UNICEF Giga | | | | Failed: needs an API key |

**Result:** 3,797 places in `data/processed/nairobi_schools.geojson`, of which 3,714 are schools for children (in `site/public/data/schools.geojson`, 797 kB). By level: primary 2,058, pre-primary 769, secondary 536, mixed 15, unknown 336, other (adult, vocational, tertiary) 83.

**One problem worth knowing:** part of both official lists is in the old Arc 1960 datum, so some points are about 300 m off. 1,480 schools found only in an official list are flagged "may be up to about 300 m off".

**How complete is it?** The only published count I found (The Eastleigh Voice, March 2024, source not named) gives 991 primary, 314 secondary and 1,168 ECDE centres. Our primary and secondary counts are higher, because OSM includes informal and low-cost schools not on registers, some 2007-list schools may have closed, and up to about 142 duplicates remain. Our pre-primary count is lower, because ECDE units inside primary schools are rarely mapped separately. It is a broad map of school sites, not a register.

## Task 4: heat at schools

Finding S1: of 3,712 schools for children with a value, **567 (15.3 %) sit on the hottest fifth of the county's land** (41.6 °C or more), and **72.6 % are on ground hotter than the county median** (38.7 °C). Using only OSM-placed schools, the share is 17.2 %.

Finding S2, wards with the most schools on the hottest fifth:

| Ward | On hottest fifth | All schools | Share |
|---|---|---|---|
| Kangemi | 92 | 127 | 72.4 % |
| Baba Dogo | 47 | 78 | 60.3 % |
| Mountain View | 43 | 123 | 35.0 % |
| Imara Daima | 35 | 59 | 59.3 % |
| Korogocho | 34 | 79 | 43.0 % |
| Viwandani | 33 | 40 | 82.5 % |
| Kiamaiko | 26 | 57 | 45.6 % |
| Kariobangi North | 19 | 39 | 48.7 % |
| Hospital | 17 | 72 | 23.6 % |
| Lindi | 16 | 89 | 18.0 % |

Landsat passes at about 10:43, during the school day. These are temperatures of the ground, roofs and roads in the 100 m around each school, not classroom air temperatures. A random 300 schools were recomputed by a different method and all agree within 0.03 °C. Check figure: `outputs/figures/check_schools_hottest_fifth.png`.

## Task 5: WorldPop scaled to the census (D55, finding P1)

File: `analysis/tables/ward_population_scaled.csv` (both numbers side by side, with each ward's census sub-county, confidence and basis). Script: `src/analysis/census_scaling.py`. Growth rate: 3.43 % a year, Nairobi's intercensal rate from KNBS counts (3,138,369 in 2009; 4,397,073 in 2019). Mid-2025 county total: 5,356,025, against WorldPop's ward sum of 5,588,514.

**Woodley/Kenyatta Golf Course:** 133,937 → 154,593, so scaling makes it worse. The census itself is clear: Woodley division, covering almost exactly the ward's area (9.6 against 9.5 km²), had 36,115 people in 2019. WorldPop has put Kibera's residents in Woodley: Laini Saba census 29,605 against WorldPop 6,032; Lindi 35,618 against 11,920; Sarang'ombe 55,303 against 25,109. Kangemi looks similar: census Kangemi location (4.6 km², 116,710 people) against Kangemi and Mountain View wards together (4.7 km², WorldPop 30,571).

**Ten hottest wards where people live (F7):** 411,659 → 433,510 in total. The largest changes are Imara Daima 102,879 → 127,291, Viwandani 57,070 → 45,187 and Dandora Area I 16,191 → 9,526. Kangemi barely moves (11,503 → 12,077), even though the census suggests it holds far more people.

**Recommendation:** scale at census location level, not sub-county. In Nairobi, census locations and sub-locations line up closely with wards, so this would fix Woodley and Kangemi. Site numbers are not replaced.

## Every new or changed file

**joto-mjini, new:** `src/pipeline/s10_schools.py`, `src/analysis/schools.py`, `src/analysis/roofs_census.py`, `src/analysis/census_scaling.py`, `data/processed/nairobi_schools.geojson`, `site/public/data/schools.geojson`, `site/public/data/schools_heat_by_ward.csv`, `site/public/data/roofs_by_subcounty.csv`, `analysis/tables/schools_heat.csv`, `analysis/tables/ward_census_subcounty_match.csv`, `analysis/tables/roofs_vs_ward_heat.csv`, `analysis/tables/ward_population_scaled.csv`, `analysis/schools_results.json`, `analysis/census_scaling_results.json`, `outputs/figures/check_schools_hottest_fifth.png`, this report; logs in `logs/` (`d52_headline_*`, `s10_schools.log`, `schools_heat*.log`, `census_scaling_*`, `findings_v3_*`). Raw downloads (git-ignored) in `data/raw/schools/`.

**joto-mjini, changed:** `src/analysis/core.py`, `src/analysis/checks.py`, `src/analysis/findings.py`, `analysis/results.json` (two new keys), `analysis/results_extra.json` (new `schools` key; nothing else changed), `analysis/checks.json`, `analysis/FINDINGS.md` (F3 rewritten; new S1, S2, R1, P1), `DECISIONS.md` (D52 to D55), `data/SOURCES.md` (census and schools), `QUESTIONS.md` (10 to 13), `PROGRESS.md`, `pyproject.toml` and `uv.lock` (added `mapbox-vector-tile`).

**Census repo:** Volume IV module, checks, tests, README and the five new CSVs (commit 89a4594).

## What failed

- UNICEF Giga (needs an API key) and opendata.go.ke 2007 (dead link).
- The energydata.info file downloads (bot check), worked around through the public tiles.
- No open boundary map of census sub-counties or sub-locations, so every census-to-ward link is by name.

## Questions for you (also in QUESTIONS.md, 10 to 13)

1. Shall I scale WorldPop to census locations, and then switch the site's ward populations?
2. Which gap should the H1 use: Industrial Area 13.9 °C, or both?
3. Push Volume IV to the public census repo once you have checked it?
4. Can you get the current school register (KEMIS or NEMIS) to check the school map against?
