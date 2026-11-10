# v2 chunk 4: animated maps, heatmaps and the highlighted chart (budget about 2.5 hours)

Make the moving maps and the heatmap tables Stephane asked for, in the spirit of NASA's wind animation (`nasa/01`), highlighted rainfall chart (`nasa/02`) and land cover change table (`nasa/03`). The animations are made in Python and do not need the Mapbox token.

## 1. Animation style (applies to all)

- Made with matplotlib (and rasterio or xarray), saved through `imageio` with `imageio-ffmpeg` (do not call `ffmpeg` directly; it is not on the approved list).
- 1600 by 1000 px frames. Background: the Sentinel-2 true-colour composite from chunk 2, faded to about 40 %, with the county outline, faint ward lines and five to eight place labels (Source Sans 3 from `assets/fonts/`).
- Baked into every frame, as in NASA's wind animation: a title at the top left, a large time stamp at the top right, a colour bar with units at the bottom, and a credit line ("Data: USGS Landsat via Microsoft Planetary Computer; analysis: Joto Mjini Nairobi" or the right sources).
- Colours: the ramps from `DESIGN_BRIEF_v2.md` (diverging for differences).
- Outputs for each animation in `outputs/animations/` and copied to `site/public/media/`: `<name>.mp4` (H.264), `<name>.webm`, `<name>.gif` (8 MB or less, for LinkedIn; reduce size or frame count if needed) and `<name>_poster.png` (the most telling frame).

## 2. The animations (do in this order)

1. **Every clear hot-season morning, 2014 to 2026** (must). One frame per usable January to March Landsat scene from the scene catalogue: the difference from that morning's county median, with the date as the time stamp. About 2 frames per second, with the last frame held for 2 seconds. Shows that the same places are hot morning after morning.
2. **Nairobi grows, 1975 to 2025** (must). GHSL built-up surface for each epoch, with a short cross-fade between epochs (render four or five in-between frames), the year as the time stamp, and the built-up area in km² as a counter under the time stamp (from `analysis/tables/ghsl_built_by_epoch.csv`).
3. **A day of heat** (must try). Hour by hour, from about 06:00 to 19:00 Nairobi time, on the hottest clear day of the 2026 hot season:
   - **If** `CDSE_CLIENT_ID` and `CDSE_CLIENT_SECRET` are set in `.env` (check with a script that prints only "set" or "missing"): use hourly CLMS land surface temperature through Sentinel Hub and sharpen each hour to about 100 m with the Landsat residual method of Zlinszky (2026), "Landsat-sharpened CLMS Land Surface Temperature: method, validation and error budget", Zenodo, https://doi.org/10.5281/zenodo.22944001. Write your own implementation and cite it; do not copy the notebook's code (its licence is not confirmed). Label it "land surface temperature, CLMS hourly, sharpened with Landsat".
   - **Otherwise:** use ERA5-Land hourly 2 m air temperature from the Open-Meteo historical API for a grid of points about 0.1° apart over a box of about 1.5° around Nairobi (the API accepts many coordinates per request; respect its rate limits). Label it clearly as **air temperature from a weather model at about 9 km**, a regional view that cannot show neighbourhoods.
   Record which path you took in `DECISIONS.md`.
4. **The 2026 El Niño season over Kenya** (only if time remains). Monthly rainfall difference from normal, May to the latest month of 2026, from CHIRPS (Climate Hazards Center, UC Santa Barbara). This is a teaser for the later El Niño project; keep it simple.

## 3. Heatmap tables (must)

Hand-built SVG with D3, in the style of NASA's land cover table (`nasa/03`) but following `DESIGN_RULES.md`: squared cells, numbers printed in each cell, one colour ramp per table, a title, subtitle, source and date. Each cell's value is also readable by tap and keyboard (no hover-only).

1. **How Nairobi filled in, 1975 to 2025:** rows are the 17 constituencies (sub-counties), columns are the GHSL epochs, cells are the built-up share of the area (%), sequential neutral-to-red ramp. Mirrors NASA's "Land Cover Changes 2001 to 2021" table.
2. **What covers the hottest and coolest wards:** rows are the 10 wards with the highest and the 10 with the lowest population-weighted surface temperature (from the corrected wards in chunk 1), columns are tree cover, grassland, built-up, bare ground (%) and the ward's difference from the city median (°C, diverging colours in that column only).
3. **Every day since January 2023:** a calendar heatmap of Nairobi's daily maximum air temperature as a difference from the 1991 to 2020 normal for that day of the year. Rows are months (January 2023 to the latest month), columns are days 1 to 31, diverging colours; the El Niño months from May 2026 marked with a bracket and label. Source: Open-Meteo, ERA5.

## 4. The highlighted-period chart (must)

Rebuild the daily air temperature chart in the style of `nasa/02`: a line of daily maximum air temperature from January 2023 to yesterday, the El Niño period from May 2026 shaded and labelled "El Niño, 2026", a crosshair tooltip on hover **and** on tap, keyboard-steppable, direct labels for the record day. Source line under it.

## 5. Wire into the page (must, if chunk 3 is done)

- **Interlude after story block A:** the "Every clear hot-season morning" animation beside two short paragraphs (layout of `nasa/01`), then the land cover heatmap table (2) beside text (layout of `nasa/03`).
- **Interlude 2 (after story block B):** the "Nairobi grows" animation beside text, the built-up heatmap table (1), the "A day of heat" animation beside text, the highlighted chart, then the calendar heatmap.
- Video behaviour (an agreed exception to "no autoplay", see the brief): muted, looping, plays only while on screen, pauses off screen, has a visible pause and play button, and under reduced motion shows the poster until the reader presses play. Every video has a caption under it with the credit, as NASA does.

## Done when

At least animations 1 to 3 and all three heatmaps and the chart exist, are wired into the page (if chunk 3 is done), have screenshots in `outputs/screenshots/v2/chunk4/`, and the commit "v2 chunk 4: animations and heatmaps" is made.
