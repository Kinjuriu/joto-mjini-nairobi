# v2 chunk 2: map engine, basemaps and layers (budget about 2.5 hours)

Build the visual foundation every later chunk uses: the Mapbox engine, the basemaps, our own Sentinel-2 images, and every data layer restyled per `DESIGN_BRIEF_v2.md`, all checked on a single test page before any story is built.

## 1. Switch the engine (must)

1. Install `mapbox-gl` (v3, exact version pinned). Remove MapLibre and the pmtiles protocol from the site (move old code to `site/_v1/`).
2. Read the token from `import.meta.env.VITE_MAPBOX_TOKEN`. Add `*.local` to `.gitignore`.
3. Write one small module, `site/src/map/createMap.js`, that every map in the site uses: creates the map with a given style, waits for the style, finds the first symbol layer id, and exposes `addDataLayer(id, source, paint, {beforeLabels: true})` so data always goes beneath labels. Also `setLayerOpacity` with a timed cross-fade, and `setChapter({center, zoom, layers, basemap})`.
4. Basemap switching between Mapbox styles drops custom layers; handle it by re-adding our sources and layers after each `style.load` (or use a single style and toggle imagery layers, if that is cleaner). Test it.

## 2. Tiles for our layers (must; no token needed)

Mapbox GL JS cannot read PMTiles, so produce static tile folders under `site/public/tiles/`:

- **Raster layers** as WebP XYZ tiles (zoom 9 to 15 for county layers, up to 16 for the Sentinel-2 images if size allows), produced in Python (for example with `rio-tiler`, or `gdal2tiles` through the GDAL Python bindings), with the colour ramps from the brief baked in and transparent no-data:
  - `heat-diff`: difference from the city median, diverging ramp, bilinear resampling.
  - `heat-abs`: absolute surface temperature, YlOrBr with decile breaks, bilinear resampling.
  - `heat-hottest-day`: the hottest clear morning (F13), same diverging ramp relative to that day's median.
  - `heat-cool-season`: cool-season composite, difference from its own median.
  - `landcover`: WorldCover classes, nearest-neighbour, categorical colours from the brief.
  - `trees`: tree cover fraction, green ramp, bilinear.
  - `population`: purple quantile ramp, bilinear.
  - `growth-1990-2020`: new built-up cells in red over 1990 built-up in neutral grey.
  - `ghsl-<year>` for each available epoch (1975 to 2025), for the animation and the date selector.
  - `s2-true` and `s2-false`: the Sentinel-2 composites (section 3).
- **Vector layers** as `.pbf` folders from tippecanoe (`--output-to-directory`, `--no-tile-compression`): `wards` (polygons with all ward stats), `ward-labels` (points), `buildings` (footprints with `diff_c` and `lst_c`), `places` (story place names).
- Write `site/public/tiles/manifest.json` listing every layer, its zoom range, legend classes and colours, units, source line and date chip text. The site reads legends and chips from this file.
- Keep total tile size reasonable for GitHub Pages (aim under 600 MB, no single file over 50 MB); record the sizes.

## 3. Sentinel-2 true and false colour (must)

Build the Nairobi dry-season composite at 10 m from Planetary Computer `sentinel-2-l2a` (January to March 2026, or the latest clear months; median of pixels the scene classification layer marks as clear). True colour: B04, B03, B02. False colour: B12, B8A, B04 (vegetation bright green). Stretch for a natural look (percentile stretch per band, slight gamma), check by eye against Mapbox satellite, and tile them. Credit: "Contains modified Copernicus Sentinel data 2026, processed by Joto Mjini Nairobi."

## 4. The layer test page (must)

Build `site/layers.html`, a plain test page with one full-screen map, a list of every layer and basemap, and buttons to jump to zoom 10, 12 and 14 over the CBD, Eastlands and Karura. Use it to check the legibility rules in section 3 of the brief for every layer. Save screenshots of every layer at zooms 10, 12 and 14 (1440 px wide) to `outputs/screenshots/v2/chunk2/`, plus the basemap tests to `outputs/screenshots/v2/basemap_tests/`. Then **open your screenshots next to `reference/screenshots/nasa/08_zoomed_in_with_clear_place_labels.png` and `ours_v1/02_heat_chapter_too_red_labels_lost.png`**, and adjust opacity, label halos and ramps until yours look clearly closer to NASA's than to v1. Write what you changed and why in `DECISIONS.md`.

## 5. Legend card and date chip components (must)

Build them once in `site/src/ui/`, driven by `manifest.json`: the legend card (bottom right, layer name, "i" button with description and source, swatches whose labels never collide, units) and the date chip (top centre). Test at 375 px and 1440 px.

## Done when

Every layer renders crisply on the test page, labels sit above data, screenshots are saved and compared, and the commit "v2 chunk 2: map engine and layers" is made.
