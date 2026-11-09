# Reference notes

## The NASA story we are modelling

**"Fanning the Flames: Unraveling the Causes of the 2025 Los Angeles Area Wildfires"**, NASA Earthdata dashboard story, published 10 April 2025, by Maheshwari Neelam (USRA), Andrew Blackford and Nidhi Jha (University of Alabama in Huntsville) and Brian Freitag (NASA).

- Live page: https://www.earthdata.nasa.gov/dashboard/stories/la-fires
- Source file in this folder: `la-fires.stories.mdx`, copied from NASA's public repository `NASA-IMPACT/veda-config` (`stories/la-fires.stories.mdx`).

The dashboard (NASA's VEDA platform) builds stories from MDX: Markdown plus a few components. Here is what each component does, so you can map it to our vanilla JavaScript build.

| VEDA component | What it does in the LA story | Our equivalent |
|---|---|---|
| Frontmatter `name`, `description`, `media` | Title, subtitle, feature image with photo credit | Title block with headline finding and subtitle defining the measure |
| `Block` with `Prose` author list | Authors and affiliations, numbered | Byline and affiliation placeholder |
| `Block type='wide'` + `Map` with `compareDateTime` | Wide map with a swipe between two dates (parcel damage vs satellite image) | Hero swipe map: hot season vs cool season surface temperature |
| `Prose` with `###` headings | Short sections, 1 to 3 paragraphs each | Same |
| `Block` with `Figure` + `Prose` | Image or chart beside text | Tree cover chart beside text |
| `Chart` with `highlightStart`, `highlightEnd`, `highlightLabel` | Daily rainfall with the fire period shaded | Daily air temperature with El Niño 2026 shaded |
| `ScrollytellingBlock` with `Chapter center zoom datasetId datetime` | Sticky map flies to each place and switches layer as text scrolls past | Seven chapters across Nairobi |
| Second wide compare `Map` | Before and after satellite imagery | Built-up area, earliest vs latest epoch |
| Explainer `Prose` sections on HLS, TEMPO, GEDI | Plain explanation of each instrument | "How a satellite reads heat" |
| `Caption` with `attrAuthor` and `attrUrl` | Credit under every visual | Source line and date under every map and chart |

What makes the NASA story work, and what we keep: one clear question per section; real data on every map; a compare slider used where the comparison is the point; a scrollytelling section that moves through specific places; numbers stated in the text; credits everywhere.

What we do differently: our look follows `DESIGN_RULES.md` (the NASA story uses justified text, default chart colours and mixed font sizes, which we avoid); every number comes from our own `analysis/FINDINGS.md`; every chapter card states its key number, so the map is never the only way to get it.

## Datasets Stephane flagged, and their African equivalents

- **NLCD Annual (CONUS)**, https://www.earthdata.nasa.gov/dashboard/data-catalog/nlcd-annual-conus: the National Land Cover Database covers only the contiguous United States, so it has no data for Nairobi. Equivalents: ESA WorldCover 10 m (2020 and 2021), Google Dynamic World (10 m, near real time, for land cover change), and the Global Human Settlement Layer (built-up area every five years since 1975).
- **NLDAS**, https://www.earthdata.nasa.gov/dashboard/stories/nldas: the North American Land Data Assimilation System, also US only. Its African counterpart is **FLDAS**, the Famine Early Warning Systems Network Land Data Assimilation System, which covers Africa with soil moisture, rainfall and temperature. FLDAS and CHIRPS rainfall are the strongest candidates for the later rainfall and El Niño phase.

## Other relevant work found

- **WRI Cool Cities Lab** (launched 18 March 2026), https://coolcities.wri.org/, maps heat risk block by block for Nairobi and Kisumu, with land surface temperature, tree cover, shade, a heat-feeling index (UTCI) and WorldPop population layers. Methods: https://coolcities.wri.org/data-and-methods. Use as a reference and check whether layers can be downloaded.
- **ESA "Climate analysis in African cities"**, https://climate.esa.int/en/supporting-the-paris-agreement/climate-analysis-in-african-cities/data: urban climate indicators for more than 50 African cities at about 300 m. Nairobi is not confirmed on the public page.
- **Copernicus notebook** by András Zlinszky (2026), "Landsat-sharpened CLMS Land Surface Temperature: method, validation and error budget", Zenodo, https://doi.org/10.5281/zenodo.22944001; code at https://github.com/eu-cdse/notebook-samples/blob/main/sentinelhub/use_cases/clms_lst_landsat_sharpening.ipynb. Combines Landsat's 100 m pattern with hourly 3 km CLMS surface temperature. Cite it if the method is used; check the licence on the Zenodo record before copying any code, because the GitHub repository has no licence file.
- **Earthna**: no open Earthna dataset on urban heat was found during planning. Earthna signed a memorandum of understanding with UN-Habitat in December 2025. Prompt 01 searches again; Stephane may also ask the organisers.
