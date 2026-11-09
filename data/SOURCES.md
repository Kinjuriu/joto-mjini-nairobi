# Data sources

Every dataset used by Joto Mjini. All were accessed on 10 November 2026 (Africa/Nairobi) unless noted. Licences are as stated by the provider on that date; check them again before publishing.

## Boundaries and places

### Nairobi County boundary
- **Name:** geoBoundaries gbOpen, Kenya ADM1 (Counties), boundary ID KEN-ADM1-32016919
- **Provider:** geoBoundaries (William & Mary geoLab); underlying source RCMRD GeoPortal / Africa GeoPortal
- **URL:** https://www.geoboundaries.org/api/current/gbOpen/KEN/ADM1/
- **Licence:** Public Domain (as stated in the geoBoundaries metadata; prompt 01 expected CC BY 4.0, see DECISIONS.md D3)
- **Resolution:** vector; boundary year represented 2020
- **File:** `data/processed/nairobi_boundary.geojson` (area 705.3 km² in UTM 37S)
- **Citation:** Runfola, D. et al. (2020). geoBoundaries: A global database of political administrative boundaries. PLoS ONE 15(4): e0231866. https://doi.org/10.1371/journal.pone.0231866

### Wards
- **Name:** geoBoundaries gbOpen, Kenya ADM3 (Ward), boundary ID KEN-ADM3-90231094
- **Provider:** geoBoundaries; underlying source Benedict Aboki Omare and George Omare, "Kenya County Assembly Boundaries", https://github.com/benaboki/Kenya-County-Assembly-Boundaries
- **URL:** https://www.geoboundaries.org/api/current/gbOpen/KEN/ADM3/
- **Licence:** CC BY 4.0
- **Resolution:** vector; 85 wards selected inside Nairobi County (matches the official count of 85)
- **File:** `data/processed/nairobi_wards.geojson`. Wards were clipped to the county outline; the clipped wards cover 674.6 km², 4 % less than the county outline, because the two sources do not share exactly the same edges.
- **Citation:** Omare, B. A. and Omare, G., Kenya County Assembly Boundaries, via geoBoundaries (Runfola et al. 2020), CC BY 4.0.

### Place names, parks and forests
- **Name:** OpenStreetMap, via the Overpass API
- **Provider:** OpenStreetMap contributors
- **URL:** https://overpass-api.de/api/interpreter
- **Licence:** Open Database License (ODbL) 1.0
- **Resolution:** vector; 539 named features (places, parks, forests, protected areas, water, industrial land)
- **File:** `data/processed/nairobi_places.geojson`
- **Citation:** © OpenStreetMap contributors

## Satellite surface temperature and vegetation

### Landsat 8 and 9 Collection 2 Level-2 surface temperature and surface reflectance
- **Name:** USGS Landsat Collection 2 Level-2 Science Products (ST_B10 surface temperature as asset `lwir11`; `red`, `nir08` surface reflectance; `qa_pixel`)
- **Provider:** U.S. Geological Survey; served by Microsoft Planetary Computer, collection `landsat-c2-l2`
- **URL:** https://planetarycomputer.microsoft.com/dataset/landsat-c2-l2 (STAC: https://planetarycomputer.microsoft.com/api/stac/v1)
- **Licence:** Public domain (USGS); no restrictions
- **Resolution:** thermal band measured at 100 m, delivered on a 30 m grid; reflectance 30 m
- **Dates covered:** 205 daytime scenes with scene cloud cover under 40 %, 7 April 2013 to 26 October 2026, all WRS-2 path 168 row 061; 68 are usable (at least 80 % clear pixels inside the county)
- **Scaling verified from STAC `raster:bands`:** surface temperature K = DN × 0.00341802 + 149.0; reflectance = DN × 0.0000275 − 0.2; DN 0 is no-data
- **Files:** `data/processed/landsat_scene_catalogue.csv`, `data/processed/rasters/lst_*.tif`, `ndvi_hot_season_median.tif`
- **Citation:** Landsat-8 and Landsat-9 images courtesy of the U.S. Geological Survey. Earth Resources Observation and Science (EROS) Center (2020). Landsat 8-9 Operational Land Imager / Thermal Infrared Sensor Level-2, Collection 2. https://doi.org/10.5066/P9OGBGM6

## Land cover, buildings, population and growth

### ESA WorldCover 2021
- **Name:** ESA WorldCover 10 m 2021 v200 (tile S03E036)
- **Provider:** European Space Agency, WorldCover consortium; served by Microsoft Planetary Computer, collection `esa-worldcover`
- **URL:** https://esa-worldcover.org/ ; https://planetarycomputer.microsoft.com/dataset/esa-worldcover
- **Licence:** CC BY 4.0
- **Resolution:** 10 m; year 2021
- **Files:** `worldcover_2021.tif` (10 m), `worldcover_majority_30m.tif`, `tree_fraction_30m.tif`, `built_fraction_30m.tif`, `grass_fraction_30m.tif`, `bare_fraction_30m.tif`, `water_fraction_30m.tif`
- **Citation:** Zanaga, D., Van De Kerchove, R., Daems, D., et al. (2022). ESA WorldCover 10 m 2021 v200. https://doi.org/10.5281/zenodo.7254221. "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium."

### Buildings
- **Name:** Overture Maps buildings theme, release 2026-10-21.0
- **Provider:** Overture Maps Foundation; footprints from OpenStreetMap (534,383 in the county), Google Open Buildings (178,165) and Microsoft ML Buildings (33,951)
- **URL:** https://docs.overturemaps.org/guides/buildings/ (downloaded with the `overturemaps` Python CLI 2.1.0)
- **Licence:** ODbL 1.0 (Overture buildings theme). Google Open Buildings content is also available under CC BY 4.0; Microsoft footprints under ODbL.
- **Resolution:** vector footprints; 746,499 buildings whose representative point is inside the county
- **File:** `data/processed/nairobi_buildings.parquet` (92 MB, not committed; rebuild with `src/pipeline/s3_context.py`)
- **Citation:** © OpenStreetMap contributors, Overture Maps Foundation; includes Google Open Buildings and Microsoft Building Footprints.

### Population
- **Name:** WorldPop Global2 R2025A v1, constrained, Kenya, 100 m, year 2025 (`ken_pop_2025_CN_100m_R2025A_v1.tif`)
- **Provider:** WorldPop, University of Southampton
- **URL:** https://hub.worldpop.org/ ; file https://data.worldpop.org/GIS/Population/Global_2015_2030/R2025A/2025/KEN/v1/100m/constrained/ken_pop_2025_CN_100m_R2025A_v1.tif
- **Licence:** CC BY 4.0 (https://hub.worldpop.org/data/licence.txt)
- **Resolution:** 3 arc-seconds (about 100 m); modelled estimate for 2025
- **County total:** 5,653,421 people (native grid); 5,657,304 after regridding to 30 m (0.07 % difference)
- **Files:** `population_100m.tif` (native grid, clipped), `population_30m.tif` (people per 30 m cell, density-preserving)
- **Citation:** Bondarenko M., Priyatikanto R., Tejedor-Garavito N., Zhang W., McKeen T., Cunningham A., Woods T., Hilton J., Cihan D., Nosatiuk B., Brinkhoff T., Tatem A., Sorichetta A. (2025). Constrained estimates of 2015-2030 total number of people per grid square at a resolution of 3 arc (approximately 100m at the equator) R2025A version v1. Global Demographic Data Project, funded by The Bill and Melinda Gates Foundation (INV-045237). WorldPop, School of Geography and Environmental Science, University of Southampton. https://doi.org/10.5258/SOTON/WP00839

### Growth of the built-up area
- **Name:** GHS-BUILT-S R2023A, built-up surface, Mollweide 100 m, tile R10_C22, epochs 1975, 1990, 2000, 2010, 2020, 2025
- **Provider:** European Commission, Joint Research Centre (JRC), Global Human Settlement Layer
- **URL:** https://ghsl.jrc.ec.europa.eu/download.php ; https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/
- **Licence:** CC BY 4.0
- **Resolution:** 100 m; R2023A is the newest global built-surface release on the JRC server on the access date. Epochs after 2020 (2025) are model projections by the JRC, not observations.
- **Files:** `ghsl_built_<year>.tif` (share of each cell built, regridded to a 90 m grid nested in the 30 m grid)
- **Citation:** Pesaresi, M. and Politis, P. (2023). GHS-BUILT-S R2023A: GHS built-up surface grid, derived from Sentinel-2 composite and Landsat, multitemporal (1975-2030). European Commission, Joint Research Centre. https://doi.org/10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA

## Weather and climate

### Daily air temperature, Nairobi
- **Name:** Open-Meteo Historical Weather API (ERA5 and ERA5-Land reanalysis), daily `temperature_2m_max`, `temperature_2m_min`, `temperature_2m_mean`
- **Provider:** Open-Meteo; underlying data Copernicus Climate Change Service (ECMWF)
- **URL:** https://archive-api.open-meteo.com/v1/archive (requested at -1.286, 36.817; the API returned the grid cell centred at -1.3005, 36.8246, elevation 1,671 m)
- **Licence:** CC BY 4.0
- **Dates covered:** 1 January 1991 to 9 November 2026 (13,097 days)
- **File:** `data/processed/nairobi_daily_air_temp.csv`
- **Important:** this is a gridded model value for an area around the city centre, not a weather station reading. It is air temperature 2 m above the ground and is not comparable with Landsat land surface temperature.
- **Citation:** Zippenfenig, P. (2023). Open-Meteo.com Weather API. Zenodo. https://doi.org/10.5281/zenodo.7970649 ; Hersbach, H. et al. (2020). The ERA5 global reanalysis. Q J R Meteorol Soc 146: 1999-2049. https://doi.org/10.1002/qj.3803

### El Niño index
- **Name:** Relative Oceanic Niño Index (RONI), 3-month running mean, ERSST.v6, 1991-2020 base
- **Provider:** NOAA Climate Prediction Center
- **URL:** https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/
- **Licence:** U.S. Government work, public domain
- **Dates covered:** DJF 1950 to ASO 2026. RONI first reached +0.5 °C in AMJ 2026 (centred on May) and was +2.0 °C in ASO 2026. NOAA notes the latest values are estimates and can change for two months.
- **File:** `data/processed/roni.csv`
- **Citation:** NOAA Climate Prediction Center, Relative Oceanic Niño Index (RONI), https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/. The page cites the ERSST.v6 papers (Huang et al. 2025, J. Climate 38(4)): https://journals.ametsoc.org/view/journals/clim/38/4/JCLI-D-23-0707.1.xml and https://journals.ametsoc.org/view/journals/clim/38/4/JCLI-D-24-0185.1.xml. Confirm the preferred RONI citation on the CPC page before publishing.

## Basemap

### Protomaps basemap extract
- **Name:** Protomaps daily build 20261109 (planetiler basemap schema version 4.15.2), extracted for bbox 36.55, -1.52, 37.22, -1.08, max zoom 15
- **Provider:** Protomaps; data from OpenStreetMap
- **URL:** https://maps.protomaps.com/builds/ ; https://build.protomaps.com/20261109.pmtiles
- **Licence:** ODbL 1.0 for the OpenStreetMap data; Protomaps basemap tiles and styles under their own open licences (styles BSD-3-Clause)
- **File:** `site/public/data/nairobi_basemap.pmtiles` (26.5 MB)
- **Citation:** © OpenStreetMap contributors; Protomaps

## Partner data

Searched 10 November 2026.

- **Earthna Center for a Sustainable Future (Qatar Foundation):** no open dataset, data portal or map on urban heat, cooling or Nairobi was found by web search. None used. Stephane may ask the organisers.
- **Children's Investment Fund Foundation (CIFF):** no open dataset on urban heat, cooling or Nairobi was found. None used.
- **WRI Cool Cities Lab** (https://coolcities.wri.org/, methods at https://coolcities.wri.org/data-and-methods): lists Nairobi layers for land surface temperature (Landsat), UTCI, reflectivity, tree cover, shade, irregular settlements, WorldPop population and heat-risk indices. The methods page shows no direct downloads, API or licence text; the layer detail page for surface temperature said "Dataset information unavailable"; the site links only to the WRI data platforms Terms of Service. Used as a reference only. Not scraped.
- **WRI Global Intra-Urban Land Use (GIULU), irregular settlements** (Guzder-Williams et al. 2023, CC BY 4.0): available as a Google Earth Engine asset (`projects/wri-datalab/cities/urban_land_use/V1`), which needs an Earth Engine account. No direct download found, so not used tonight. See QUESTIONS.md.
- **ESA "Climate analysis in African cities"** (https://climate.esa.int/en/supporting-the-paris-agreement/climate-analysis-in-african-cities/data): about 300 m indicators for more than 50 African cities; the public page does not list the cities, a licence or download links. Nairobi not confirmed. Reference only.
- **Other relevant work found** (reference only, not data inputs): IIED issue paper on heat in informal settlements in Nairobi, Dar es Salaam and Kariba (2026), https://www.iied.org/sites/default/files/pdfs/2026-02/22697iied.pdf ; Kimutai, J. (2022), heat thresholds for Nairobi, Mombasa and Kisumu, https://preparecenter.org/wp-content/uploads/2022/12/Kenya-Heat-Tresholds-Research-by-J.Kimutai-2022.pdf ; NASA SEDAC Global Urban Heat Island data set 2013, https://doi.org/10.7927/H4H70CRF
