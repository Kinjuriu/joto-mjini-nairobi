# Reference screenshots

Open every image in this folder before building (you can view PNG files). `nasa/` shows the look and behaviour Stephane wants, from NASA Earthdata's story "Fanning the Flames" (https://www.earthdata.nasa.gov/dashboard/stories/la-fires). `ours_v1/` shows the first version of Joto Mjini Nairobi and what is wrong with it.

## nasa/: what to copy

| File | What it shows | What to copy |
|---|---|---|
| `01_animated_wind_gif_beside_text.png` | An animated map (a GIF made in Python from model data, with its own title, timestamp, colour bar and credit) placed beside a block of text | Our animated maps: same layout, same "baked in" title, time stamp, colour bar and credit |
| `02_chart_with_highlighted_period.png` | A daily time series with one period shaded and labelled, hover tooltip | Our daily temperature chart with the El Niño months shaded |
| `03_text_beside_fullbleed_landcover_map.png` | Text column on the left while a full-width map fills the rest; a heatmap table (land cover by year) sits in the text | Text plus heatmap table beside a full-bleed map |
| `04_scroll_from_text_into_fullbleed_map.png` | Scrolling out of an article section into a full-screen map | The hand-over from the short intro into the full-screen map story |
| `05_overview_card_floating_over_landcover.png` | A white card with a short accent rule, a title and a bullet list of key numbers, floating over a full-screen map; date chip at the top centre; legend card at the bottom right | Our chapter cards, date chip and legend card |
| `06_true_colour_satellite_chapter.png` | Same place in true-colour satellite imagery, card still floating | The "Nairobi from space" chapter |
| `07_false_colour_chapter_vegetation_green.png` | The same view switched to a false-colour image where vegetation glows green | The "where the trees are" chapter using Sentinel-2 false colour |
| `08_zoomed_in_with_clear_place_labels.png` | Zoomed in to a town scale; crisp categorical colours; place labels drawn on top and fully readable | Label legibility over data at zoom 11 to 14 |
| `09_layer_switching_between_chapters.png` | A layer change between two chapters (land cover giving way to satellite imagery) | Smooth layer cross-fade when a chapter changes |
| `10_text_beside_satellite_map_figure.png` | Long explainer text, then a small interactive map figure beside text, with a date chip, layer card and scale bar | Small embedded maps beside explainer text |
| `11_static_figure_beside_text.png` | A static scientific figure beside a short explainer | Static figures from Python beside text |
| `12_bullets_beside_paired_maps.png` | Bulleted numbers beside a before-and-after pair of maps | A before-and-after pair (for example hot season and cool season) |
| `13_card_over_regional_landcover.png` | A wide regional view with a card and legend; dark ocean, vivid categorical data | The opening county-wide land cover chapter |

What makes NASA's maps look clear (copy all of these):

1. A crisp basemap: Mapbox satellite imagery or a clean Mapbox style, with Mapbox's label layers.
2. Data drawn **beneath** the place labels, so names are always readable.
3. Categorical data (land cover) with a few distinct, saturated colours; continuous data shown with enough colour range that places look different from each other.
4. Full-screen maps with small floating cards, so the map gets the whole screen.
5. A date chip at the top centre and a legend card at the bottom right on every map.
6. Each chapter moves the map to one place and changes one thing.

## ours_v1/: what is wrong (fix all of these)

| File | Problem |
|---|---|
| `01_population_chapter_blocky.png` | Big grey blocks; 100 m cells look like pixels; legend labels collide ("1,0003,000") |
| `02_heat_chapter_too_red_labels_lost.png` | Almost the whole map is red or brown, so nothing stands out; place labels are faint and get lost in the colour |
| `03_tree_cover_chapter.png` | Works reasonably; legend labels collide ("10 %25 %") |
| `04_difference_map_chapter.png` | Better colour idea (blue cooler, orange hotter) but blocky; white "holes" where the basemap shows through |
| `05_wards_chapter_no_ward_names.png` | Wards are all similar shades of red; no ward names; you cannot tell which ward is which |
| `06_growth_compare_map_faint.png` | Built-up growth is too faint on the grey basemap; hard to see what changed |
| `07_explorer_buildings.png` | The strongest view; keep the idea, make it crisper on a satellite base with readable labels |
| (all) | Map on one side and text on the other, so the map is small; NASA uses the full screen with floating cards |
