# Questions for Stephane

Most important first. Each has the choice I made in the meantime (see DECISIONS.md).

1. **Informal settlement layer.** WRI's Global Intra-Urban Land Use (irregular settlements, CC BY 4.0) is only on Google Earth Engine. If you have an Earth Engine account, export the Nairobi tiles (asset `projects/wri-datalab/cities/urban_land_use/V1`) to `data/raw/` and the settlement comparison in prompt 02 Q7 can be added. Meanwhile I compared wards only (D9).
2. **Partner data.** No open Earthna or CIFF dataset on urban heat or Nairobi was found. Do you want to ask the organisers? WRI Cool Cities Lab layers are not downloadable from the site; you could write to WRI for the Nairobi surface temperature and heat risk layers.
3. **CBD and Industrial Area shapes (D12).** I used circles (750 m and 1 km). If you have preferred boundaries (for example the CBD as defined by the county), they can replace `comparison_areas.geojson` and F3 will update.
4. **Population in dense settlements.** WorldPop 2025 gives some dense wards very low numbers (Laini Saba about 3,300; Kangemi about 11,700). WorldPop may undercount the densest informal settlements. Would you like the 2019 KNBS census ward populations used for the ward table instead? (I did not find an open machine-readable ward table tonight.)
5. **Ward boundaries.** The 85 wards come from a community-made layer on geoBoundaries (Omare and Omare, CC BY 4.0), not directly from the IEBC. Is there an official layer you prefer?
6. **Headline.** Three options are in `site/SITE_REPORT.md`.
7. **Woodley/Kenyatta Golf Course population (v2, D29).** With the IEBC-based wards, WorldPop still puts 133,937 people (68 % of Kibra sub-county) in Woodley; the 2009 census in the same layer gives 35,355. This breaks the "no ward over 60 % of its sub-county" rule. Laini Saba (0.37 km², 6,032 people) and Nyayo Highrise (0.39 km², 4,365) are also small wards with under 10,000 WorldPop people, against 28,182 and 24,191 in the 2009 census. Should the ward table use 2019 KNBS census ward totals if you can get them, or should Woodley be shown with a note?
8. **City centre shape (v2, D30).** The city centre is now the Nairobi Central ward (3.15 km², larger than the v1 circle and reaching beyond the downtown grid). Is that the definition you want for the headline?
