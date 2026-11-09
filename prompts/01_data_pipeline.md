# Prompt 01: data pipeline

## Goal

Build a reproducible Python pipeline in `src/` that downloads, cleans and prepares every dataset the Nairobi heat story needs, plus a narrative notebook `notebooks/01_data_pipeline.ipynb` that runs it step by step with short explanations Stephane can read. Every script must be re-runnable: skip work already done (check for output files) unless called with `--force`.

## Ground rules for this phase

- All source URLs, collection IDs and band scaling factors below are what we believe to be correct. **Verify each one against the provider's own documentation or STAC metadata before relying on it**, and if something differs, follow the provider and record the difference in `DECISIONS.md`.
- Clip everything to the Nairobi study area (plus a 2 km buffer) as early as possible, so files stay small.
- Write every dataset to `data/SOURCES.md` the moment you use it: name, provider, URL, licence, resolution, dates covered, date accessed, required citation.
- Reproject analysis rasters to EPSG:32737 (UTM 37S) on a shared 30 m grid aligned to the Landsat grid. Keep one reference grid file, `data/interim/grid_30m.tif`, and align everything to it.
- Prefer sources that need no login, so the run cannot stall on credentials.

## Setup

Create the `uv` project and install at least: `pystac-client`, `planetary-computer`, `odc-stac` (or `stackstac`), `rioxarray`, `xarray`, `rasterio`, `geopandas`, `shapely`, `pyproj`, `numpy`, `pandas`, `pyarrow`, `requests`, `matplotlib`, `jupyter`, `ipykernel`, `tqdm`, `python-dotenv`, `rio-cogeo`, `overturemaps`. Optional, if needed later: `rio-pmtiles` for raster tiles, `osmnx`, `exactextract` or `rasterstats` for zonal statistics, `sentinelhub` for Copernicus. For command-line tools, use Homebrew: `brew install tippecanoe pmtiles gdal` (GDAL 3.8 or newer has a PMTiles driver). Record the installed versions in `PROGRESS.md`.

## Step 1: study area, wards and place names

1. **Nairobi County boundary.** Primary: geoBoundaries gbOpen, Kenya ADM1 (licence CC BY 4.0). The API at `https://www.geoboundaries.org/api/current/gbOpen/KEN/ADM1/` returns JSON with a `gjDownloadURL`; select the feature named Nairobi. Fallback: the OpenStreetMap boundary relation for Nairobi County through the Overpass API. Save `data/processed/nairobi_boundary.geojson` (EPSG:4326).
2. **Wards.** Nairobi has 17 constituencies (sub-counties) and 85 wards. Find a ward boundary layer with about 85 polygons. Try, in order: the Humanitarian Data Exchange (HDX) Kenya administrative boundaries; geoBoundaries KEN ADM3 if it holds wards; OpenStreetMap administrative boundaries inside the county (check which `admin_level` gives about 85 units). Record which you used and its licence. If you cannot find wards, use the 17 constituencies and note it. Save `data/processed/nairobi_wards.geojson` with a stable `ward_id` and `ward_name`.
3. **Place names for map labels.** From OpenStreetMap (Overpass), get `place=suburb`, `place=neighbourhood` and `place=quarter` points inside the county, plus named parks and forests (`leisure=park`, `landuse=forest`, `boundary=protected_area`) such as Karura Forest, the Nairobi Arboretum, City Park, Uhuru Park and Nairobi National Park. Save `data/processed/nairobi_places.geojson`. Licence: ODbL, attribution "© OpenStreetMap contributors".

## Step 2: Landsat surface temperature (the core dataset)

**Primary source: Microsoft Planetary Computer**, STAC API `https://planetarycomputer.microsoft.com/api/stac/v1`, collection `landsat-c2-l2` (USGS Landsat Collection 2 Level-2, Landsat 8 and 9). No account needed; sign item assets with `planetary_computer.sign_inplace`.

1. **Search** all Landsat 8 and Landsat 9 items intersecting the study area from 2013-04-01 to today, with `eo:cloud_cover` under 40 (we filter more strictly per pixel next). Keep daytime scenes only (Nairobi's Landsat overpass is mid-morning local time).
2. **Surface temperature band.** On Planetary Computer the Collection 2 Level-2 surface temperature band is the asset named `lwir11` (ST_B10). Convert to Kelvin with `ST = DN × 0.00341802 + 149.0`, then to °C by subtracting 273.15. DN 0 is no-data. Verify the scale and offset in the asset's `raster:bands` metadata.
3. **Cloud mask.** Use the `qa_pixel` asset. Mask a pixel if any of these bits is set: bit 0 fill, bit 1 dilated cloud, bit 2 cirrus, bit 3 cloud, bit 4 cloud shadow. Also mask surface temperature outside 0 to 70 °C as invalid.
4. **Scene catalogue.** For every scene, compute over the county boundary: clear-pixel fraction, median, 10th and 90th percentile surface temperature, and acquisition time in both UTC and Nairobi local time. Save `data/processed/landsat_scene_catalogue.csv`. Keep scenes with at least 80 % clear pixels inside the county as "usable".
5. **Save usable scenes** as clipped Cloud Optimized GeoTIFFs in °C: `data/interim/landsat/<scene_id>_lst_c.tif`, on the shared 30 m grid.
6. **NDVI from the same scenes.** Use `red` and `nir08` surface reflectance (scale `DN × 0.0000275 − 0.2`, verify), the same cloud mask, NDVI = (nir − red) / (nir + red). Save alongside, `<scene_id>_ndvi.tif`.
7. **Composites** (median of usable scenes, pixel by pixel, also save the count of valid observations per pixel):
   - `lst_hot_season_median.tif`: January to March scenes from 2023 onward. These are Nairobi's hottest and usually clearest months. If fewer than 4 usable scenes, extend back year by year until you have at least 4, and record the years used.
   - `lst_cool_season_median.tif`: June to August scenes, same rule.
   - `lst_hottest_clear_day.tif`: the single usable scene with the highest county median surface temperature. Record its date.
   - `ndvi_hot_season_median.tif`: matching NDVI composite.
   - `lst_hot_season_by_year/<year>.tif`: January to March composite for each year 2014 onward that has at least 2 usable scenes (for the change-over-time chart).
   - `lst_2026_el_nino_period.csv`: list of usable scenes from May 2026 onward with their statistics (for the later El Niño phase; just list them).
8. Save composites to `data/processed/rasters/` as COGs.

**Fallbacks, in order, if Planetary Computer fails:** (a) Element 84 Earth Search STAC (`https://earth-search.aws.element84.com/v1`, collection `landsat-c2-l2`); note the underlying USGS bucket may be requester-pays, in which case skip it; (b) NASA Harmonized Landsat Sentinel-2 (HLS) through NASA Earthdata, only if `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` exist in `.env` (HLS has no thermal band, so it only helps NDVI); (c) the Copernicus Data Space Ecosystem through Sentinel Hub, only if `CDSE_CLIENT_ID` and `CDSE_CLIENT_SECRET` exist in `.env`, using the Landsat 8 to 9 collection. If all fail, follow the "If something goes badly wrong" section of prompt 00.

## Step 3: land cover, buildings, population, growth

1. **Land cover.** ESA WorldCover 10 m (2021 version), Planetary Computer collection `esa-worldcover` (licence CC BY 4.0). Clip, keep the class codes (10 tree cover, 30 grassland, 50 built-up, 60 bare, 80 water, and others), and also compute on the 30 m grid the fraction of each 30 m cell that is tree cover and built-up. Save `data/processed/rasters/worldcover_2021.tif`, `tree_fraction_30m.tif`, `built_fraction_30m.tif`.
2. **Buildings.** Primary: Overture Maps buildings theme, using the `overturemaps` command-line tool, for example `overturemaps download --bbox=<minx,miny,maxx,maxy> -f geoparquet --type=building -o data/raw/overture_buildings.parquet`. Overture combines OpenStreetMap, Microsoft and Google Open Buildings footprints; licence ODbL, attribution required. Fallback: Google Open Buildings v3 polygons for the S2 cells covering Nairobi (licence CC BY 4.0 or ODbL, check), from `https://storage.googleapis.com/open-buildings-data/v3/`. Clip to the county, keep `id`, footprint area, height if present, source. Save `data/processed/nairobi_buildings.parquet`. Record the building count.
3. **Population.** WorldPop 100 m, Kenya, the most recent constrained or unconstrained population count raster (licence CC BY 4.0), from `https://hub.worldpop.org/` or `https://data.worldpop.org/`. Record the exact product and year. Clip and save `data/processed/rasters/population_100m.tif`. Do not resample population to 30 m by copying values; when you need it on a finer grid, divide counts so totals are preserved.
4. **Growth of the built-up area.** Global Human Settlement Layer GHS-BUILT-S (built-up surface), the most recent release, epochs 1975 to 2020 or later, 100 m, from the JRC open data catalogue (`https://ghsl.jrc.ec.europa.eu/download.php` and the JRC FTP linked there). Licence CC BY 4.0. Save the epochs you can get (at least 1990, 2000, 2010, 2020 or the nearest) as `data/processed/rasters/ghsl_built_<year>.tif`. Optional: drop this step if it costs more than 40 minutes.

## Step 4: air temperature series (city scale)

Surface temperature from Landsat is a snapshot every 8 to 16 days. For the day-to-day story ("hot one day, cold the next"), use a daily air temperature series for one Nairobi point, from the Open-Meteo historical weather API (`https://archive-api.open-meteo.com/v1/archive`, based on ERA5 reanalysis, licence CC BY 4.0, attribution required). Request `temperature_2m_max`, `temperature_2m_min` and `temperature_2m_mean` daily from 1991-01-01 to yesterday, at the Nairobi CBD (about -1.286, 36.817), timezone `Africa/Nairobi`. Save `data/processed/nairobi_daily_air_temp.csv`. Note in `data/SOURCES.md` that this is a gridded model value for the whole city area, not a station reading, and not comparable to surface temperature.

## Step 5: El Niño status (context only)

From NOAA's Climate Prediction Center Relative Oceanic Niño Index (RONI) page `https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/`, download the monthly (3-month running mean) table and save `data/processed/roni.csv`. This is only for one short context section and for the later El Niño phase.

## Step 6: check for Earthna and partner data

The workshop host is the Earthna Center for a Sustainable Future (Qatar Foundation), with the Children's Investment Fund Foundation (CIFF). Stephane wants to use their data if any exists.

1. Search the web for any open dataset, data portal, map or report published by Earthna, or by CIFF, on urban heat, cooling or Nairobi. Record what you find, with links, in `data/SOURCES.md` under "Partner data", including "none found" if that is the result.
2. Check WRI's Cool Cities Lab (`https://coolcities.wri.org/`, launched March 2026), which covers Nairobi and Kisumu with heat risk, tree cover, shade and population layers. Read `https://coolcities.wri.org/data-and-methods` and its layer detail pages. If any Nairobi layer is downloadable under an open licence, download it for comparison in the analysis. If not, record it as a reference only. Do not scrape the web app.
3. Check the ESA climate project "Climate analysis in African cities" (`https://climate.esa.int/en/supporting-the-paris-agreement/climate-analysis-in-african-cities/data`) for Nairobi heat indicators at about 300 m. Same rule.

## Step 7: basemap for the website

The story map needs streets and place names under the heat layer, without an API key.

1. Primary: a Protomaps basemap extract for the Nairobi area. Use the `pmtiles` CLI: `pmtiles extract <latest daily build URL from https://maps.protomaps.com/builds/> site/public/data/nairobi_basemap.pmtiles --bbox=<county bbox plus margin> --maxzoom=15`. Licence: OpenStreetMap ODbL plus Protomaps terms; record both. Also note which `@protomaps/basemaps` style package version matches the build, for prompt 03.
2. Fallback: OpenFreeMap's hosted vector tiles and styles (`https://openfreemap.org/`, no key), noting in `DECISIONS.md` that this depends on an outside server.

## Step 8: web-ready outputs (hand-off to prompts 02 and 03)

Prompt 02 creates the final web layers, but prepare the folder `site/public/data/` now and write `data/processed/MANIFEST.md` listing every processed file, its size, grid and purpose.

## Done when

- `data/SOURCES.md` lists every dataset with licence and citation, including partner data findings.
- `landsat_scene_catalogue.csv` exists and at least the hot-season composite exists.
- The notebook `notebooks/01_data_pipeline.ipynb` runs top to bottom (execute it with `jupyter nbconvert --to notebook --execute --inplace` and fix errors) and shows: the county with wards, a quick look at the hot-season surface temperature map with a fixed colour scale, the scene catalogue table, and the land cover map.
- `PROGRESS.md` is updated and the commit "Phase 1: data pipeline" is made.

## If time remains (optional, in this order)

1. A second city for comparison, Kisumu (also in Cool Cities Lab), with the same steps 1 to 3 only.
2. CLMS hourly surface temperature sharpening, following the cited method of Zlinszky (2026), "Landsat-sharpened CLMS Land Surface Temperature: method, validation and error budget", Zenodo, https://doi.org/10.5281/zenodo.22944001. Only if CDSE credentials exist in `.env`. Write your own implementation of the method, cite it, and do not copy the notebook's code until Stephane has confirmed its licence (the GitHub repository has no licence file).
