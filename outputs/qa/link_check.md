# Link check, 10 November 2026

| Status | URL |
|---|---|
| 200 | https://archive-api.open-meteo.com/v1/archive |
| 200 | https://climate.esa.int/en/supporting-the-paris-agreement/climate-analysis-in-african-cities/data |
| 200 | https://coolcities.wri.org/ |
| 200 | https://coolcities.wri.org/data-and-methods |
| 200 | https://data.worldpop.org/GIS/Population/Global_2015_2030/R2025A/2025/KEN/v1/100m/constrained/ken_pop_2025_CN_100m_R2025A_v1.tif |
| 200 | https://doi.org/10.1371/journal.pone.0231866 |
| 200 | https://doi.org/10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA |
| 200 | https://doi.org/10.5258/SOTON/WP00839 |
| 200 | https://doi.org/10.5281/zenodo.22944001 |
| 200 | https://doi.org/10.5281/zenodo.7254221 |
| 200 | https://doi.org/10.5281/zenodo.7970649 |
| 200 | https://doi.org/10.7927/H4H70CRF |
| 200 | https://esa-worldcover.org/ |
| 200 | https://hub.worldpop.org/ |
| 200 | https://planetarycomputer.microsoft.com/api/stac/v1 |
| 200 | https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/ |
| 200 | https://www.earthdata.nasa.gov/dashboard/data-catalog/nlcd-annual-conus: |
| 200 | https://www.earthdata.nasa.gov/dashboard/stories/la-fires |
| 200 | https://www.earthdata.nasa.gov/dashboard/stories/nldas: |
| 206 | https://build.protomaps.com/20261109.pmtiles |
| 206 | https://docs.overturemaps.org/guides/buildings/ |
| 206 | https://doi.org/10.5066/P9OGBGM6 |
| 206 | https://ghsl.jrc.ec.europa.eu/download.php |
| 206 | https://github.com/benaboki/Kenya-County-Assembly-Boundaries |
| 206 | https://github.com/eu-cdse/notebook-samples/blob/main/sentinelhub/use_cases/clms_lst_landsat_sharpening.ipynb |
| 206 | https://hub.worldpop.org/data/licence.txt |
| 206 | https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/ |
| 206 | https://maps.protomaps.com/builds/ |
| 206 | https://planetarycomputer.microsoft.com/dataset/esa-worldcover |
| 206 | https://planetarycomputer.microsoft.com/dataset/landsat-c2-l2 |
| 206 | https://preparecenter.org/wp-content/uploads/2022/12/Kenya-Heat-Tresholds-Research-by-J.Kimutai-2022.pdf |
| 206 | https://www.geoboundaries.org/api/current/gbOpen/KEN/ADM1/ |
| 206 | https://www.geoboundaries.org/api/current/gbOpen/KEN/ADM3/ |
| 206 | https://www.iied.org/sites/default/files/pdfs/2026-02/22697iied.pdf |
| 403 | https://doi.org/10.1002/qj.3803 |
| 403 | https://journals.ametsoc.org/view/journals/clim/38/4/JCLI-D-23-0707.1.xml |
| 403 | https://journals.ametsoc.org/view/journals/clim/38/4/JCLI-D-24-0185.1.xml |
| 404 | https://climate.esa.int/en/supporting-the-paris-agreement/climate-analysis-in-african-cities/data: |
| 406 | https://overpass-api.de/api/interpreter |

Notes: the three 403 responses (doi.org to Wiley for Hersbach et al. 2020, and two AMS journal pages) come from publishers that block automated requests; open them in a browser. The ESA "404" is a checker artefact: the URL was read with a trailing colon from `reference/README.md`; the real page loaded during the partner-data search. `overpass-api.de/api/interpreter` returns 406 to a plain GET because it expects a query; it worked in the pipeline.
