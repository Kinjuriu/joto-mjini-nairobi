# v2 chunk 1: data fixes (budget about 1.5 hours)

Fix the data problems found in review before any new visuals are built on top of them. Every fix goes through the existing pipeline in `src/`, and the findings regenerate automatically.

## 1. Official ward boundaries (must)

**Problem:** the geoBoundaries ADM3 ward layer (Omare and Omare) misplaces people around Kibera. The five Kibera wards together hold about 204,000 people in WorldPop, close to the 2019 census total for Kibera sub-county (about 186,000), but Woodley/Kenyatta Golf Course holds 140,000 of them and Laini Saba only 3,300. The people are roughly right; the lines are not. Woodley then counts among the "coolest fifth" of wards and distorts finding F8.

**Do:**
1. Find the official IEBC ward boundaries (1,450 wards nationally, 85 in Nairobi). Try, in order: Kenya's open data or IEBC publications; the Humanitarian Data Exchange (search "Kenya wards"); well-known public repositories of IEBC shapefiles on GitHub; ArcGIS Hub datasets citing IEBC. Record the source, its licence and its date in `data/SOURCES.md`.
2. Validate before using: exactly 85 Nairobi wards; names match the IEBC list for Nairobi's 17 constituencies; the Kibera wards (Laini Saba, Lindi, Makina, Woodley/Kenyatta Golf Course, Sarang'ombe) have sensible relative sizes; the ward union matches the county boundary within a small tolerance. Write the checks to `analysis/checks.json`.
3. Replace the ward layer, keep the old one in `data/processed/_old/` for comparison, and write a short table comparing old and new ward populations for the ten most changed wards to `analysis/tables/ward_boundary_change.csv`.
4. Population sanity check: no ward of under 1 km² in a dense area should have fewer than about 10,000 people, and no single ward should hold more than 60 % of its sub-county's people. List any ward that breaks these rules in `QUESTIONS.md`.

**If no official layer can be found:** keep geoBoundaries, add a visible caveat to every ward-level finding, and say so first in the morning report.

## 2. Comparison areas for the headline (must)

Replace the hand-drawn circles in `comparison_areas.geojson` with shapes anyone can check:
- **City centre:** the official Nairobi Central ward polygon.
- **Industrial Area:** OpenStreetMap `landuse=industrial` polygons within Nairobi's Industrial Area (around Enterprise Road, Lunga Lunga Road and Mombasa Road; merge the touching polygons; record the OSM IDs used).
- **Karura Forest and the Nairobi Arboretum:** keep the OSM polygons.

Re-run F3 and record the old and new numbers in `DECISIONS.md`.

## 3. Iron-sheet roof check (must, keep it short)

**Concern:** several dense wards with almost no tree cover (Mlango Kubwa, Mabatini, Eastleigh North, Pangani, Ngei) come out among the cooler wards. One possible reason: bare metal (mabati) roofs have low thermal emissivity, so a satellite surface temperature retrieval that assumes a typical emissivity can read them cooler than they are. Test this; do not assume it.

1. The Landsat Collection 2 Level-2 product includes an emissivity band (`emis` on Planetary Computer) and its uncertainty (`emsd`). For the hot-season scenes, compute the median emissivity per ward and compare dense, low-tree wards with leafy wards and with the CBD.
2. Search the literature for land surface temperature over informal settlements with metal roofs (Nairobi or similar cities), and for Landsat's emissivity method (ASTER GED with an NDVI adjustment). Cite what you find.
3. Write the result in `analysis/FINDINGS.md` as a new finding or caveat (F16), with a clear confidence level: either "emissivity looks normal, so the cool readings are probably real", or "emissivity is assumed high where roofs are metal, so these wards may be hotter than shown". If it is the second, add the caveat to the ward cards and the explorer.

## 4. Re-run and regenerate (must)

Re-run the analysis (`src/analysis/core.py` and the checks), regenerate `analysis/FINDINGS.md`, `analysis/results.json`, the ward tables and the web ward layer. List every headline number that changed by more than 0.3 °C or 5 % in `PROGRESS.md`.

## Done when

New ward layer validated and in use, comparison areas replaced, roof check written up, findings regenerated, and the commit "v2 chunk 1: data fixes" made.
