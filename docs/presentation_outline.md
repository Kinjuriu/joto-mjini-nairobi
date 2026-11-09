# Presentation outline: Joto Mjini (10 minutes)

For the workshop "Land, Food and Heat Resilience in Africa's Arid Regions", Sankara Hotel, Nairobi, 26 November 2026. Structure: Context, Action, Metric, Impact. Every number below is in `analysis/FINDINGS.md`; the finding number is in brackets. Bring the static figures in `outputs/figures/` and the screenshots in `outputs/screenshots/` in case there is no internet; the site also runs offline from a laptop with `cd site && npm run build && npx vite preview`.

Timing: about 1 minute per slide, with 1 minute spare for the live explorer.

---

## Slide 1. Context: heat in Nairobi lands unevenly (1 minute)

- **On screen:** the hero map, `outputs/figures/hero_map_hot_season.png`.
- **Say:** On a clear morning between January and March, half of Nairobi County's ground is hotter than 38.7 °C at the surface (F1). But that hides a split. The ground in the city centre and Industrial Area was 12.8 °C hotter than Karura Forest and the Arboretum (F3).
- **Say once, clearly:** This is land surface temperature, how hot roofs, roads and soil are, measured by satellite. It is different from the air temperature in a forecast.

## Slide 2. Action: what I built (1 minute)

- **On screen:** the story's first screen (`outputs/screenshots/first_screen_1440.png`) beside the explorer (`outputs/screenshots/explorer_ward_1440.png`).
- **Say:** Joto Mjini is an open data story and a ward explorer. Anyone can find their ward, see its surface temperature, tree cover and population, and compare it with the rest of the city. The structure follows NASA Earthdata's story on the 2025 Los Angeles fires.

## Slide 3. Action: which open data, and how (1 minute)

- **On screen:** a simple list of sources with logos removed: Landsat 8 and 9 (USGS), ESA WorldCover 2021, WorldPop 2025, GHSL built-up area, Overture building footprints, OpenStreetMap, ERA5 via Open-Meteo.
- **Say:** We checked 205 Landsat passes over Nairobi since April 2013; 68 were clear enough to use (F15). The main map is the middle value of 12 clear mornings, January to March 2023 to 2026. Everything is open data and open code, and every number traces back to a script.

## Slide 4. Metric 1: trees go with cooler ground (1 minute)

- **On screen:** `outputs/figures/chart_tree_cover_bands.png`.
- **Say:** Where tree cover was under a tenth of the land, the ground averaged 39.9 °C; where it was over nine tenths, 31.5 °C (F4). Mostly built-up ground was 7.8 °C hotter than ground mostly under trees.
- **Careful:** This is an association. It does not tell us how much planting trees would cool a street. Dry grass and bare ground were as hot as built-up land in these months (F5).

## Slide 5. Metric 2: who lives on the hottest ground (1 minute)

- **On screen:** `outputs/figures/table_top_wards.png`.
- **Say:** About 827,000 people live on the hottest fifth of the county's ground (F6). The ten wards where people live on the hottest ground, led by Viwandani, Kangemi and Kawangware, are home to about 348,000 people, and none has more than 12.5 % of its land under trees (F7).
- **Framing:** These residents are more exposed because their neighbourhoods have little shade. It is a gap in cooling infrastructure.

## Slide 6. Metric 3: the cooling gap between wards (1 minute)

- **On screen:** scrollytelling chapter 9, wards coloured by surface temperature under their people (`outputs/screenshots/chapter_9_1440.png`).
- **Say:** Residents of the hottest fifth of wards lived on ground 4.4 °C hotter than residents of the coolest fifth, 41.1 °C against 36.7 °C. The hotter wards had 3.3 % tree cover; the cooler wards had 36.1 % (F8).
- **Careful:** These are differences between places and the exposure of the people there. There is no income data in this analysis.

## Slide 7. Impact: what someone could do with the explorer (1.5 minutes)

- **On screen:** live explorer, or `outputs/screenshots/explorer_buildings_1440.png`.
- **Say, with one example each:**
  - A county planner can rank wards by the surface temperature under their people and their tree cover, to decide where shade and greening go first.
  - An NGO can show a ward's numbers to residents and to funders in plain language, and share the exact view by link.
  - A school or clinic can see whether its block sits in one of the hottest patches of the city (each building shows the surface temperature of the area around it, about 100 m).
- **Say what it cannot do:** it does not show street-level air temperature, night-time heat or heat inside homes.

## Slide 8. Impact: what comes next (1 minute)

- **On screen:** `outputs/figures/chart_daily_air_temp.png` (daily air temperature with El Niño 2026 shaded).
- **Say:** Since El Niño conditions began in May 2026, Nairobi's daily highs averaged 25.0 °C, 1.7 °C above the 1991 to 2020 average for those months (F12). This alone does not show El Niño caused it. The next phase adds rainfall, flooding and El Niño, using the same pipeline, wards and buildings.

## Slide 9. Close: link and credits (30 seconds)

- **On screen:** project name, link placeholder [URL], QR code placeholder, and the data credits: USGS Landsat; ESA WorldCover; WorldPop (University of Southampton); GHSL (European Commission JRC); Overture Maps Foundation; © OpenStreetMap contributors; Open-Meteo and ERA5 (Copernicus, ECMWF); NOAA CPC. Ward boundaries: Omare and Omare via geoBoundaries.
- **Say:** The data, code and methods are open. I would welcome corrections and partners, especially anyone with ward-level data on heat and health.
- **Note:** mention the workshop hosts only as the occasion; do not use their logos.
