# v2 chunk 5: the explorer dashboard (budget about 2 hours)

Build the interactive map at the bottom of the story: a small version of NASA's dashboard exploration view, where anyone can switch layers, compare two layers with a swipe, and find their own ward. It replaces the v1 "Find your ward" section.

## Layout (must)

- A full-width section titled "Explore the map" with one line of instruction under it.
- Desktop: a left panel about 320 px wide and the map filling the rest, about 80 % of the screen height. Phones: the map fills the screen width, and the panel becomes a bottom sheet with two tabs, "Layers" and "Ward".
- The date chip (top centre) and legend card (bottom right) from chunk 2.

## The layer panel (must)

- Basemap switch: "Satellite" and "Light".
- Layers in groups, each with an on/off switch (a real checkbox), an opacity slider, and an "i" button that opens the layer's description and source from `manifest.json`:
  - **Heat:** difference from the city median (on by default); surface temperature; hottest clear morning; cool season.
  - **Land:** Sentinel-2 true colour; Sentinel-2 false colour; land cover; tree cover.
  - **People and buildings:** population; buildings by heat (shown from zoom 14; say so in the panel).
  - **Change:** built-up area, with a year selector across the GHSL epochs (1975 to 2025) and a play button that steps through the years (paused by default).
- Only one heat layer at a time (switching one on switches the others off); land and people layers can sit beneath it.

## Swipe compare (must)

A "Compare" button that splits the map with a vertical swipe handle (mouse, touch and keyboard arrows), with a layer picker for each side (for example hot season on the left, cool season on the right, or 1990 and 2020 built-up). Both sides move together. Implement it with two synchronised Mapbox maps and a clip, or an equivalent tested method.

## Wards (must)

- A ward search box (an accessible combobox: type to filter, arrow keys, Enter to choose, Escape to close) listing all 85 wards.
- Choosing a ward, or clicking or tapping it on the map, zooms to it, outlines it, and fills the ward panel with its numbers as text: median surface temperature; difference from the city median; its rank, with the ranking named in words ("4th hottest of 85 by median surface temperature" and, separately, "1st of 85 where people live, weighted by population"); population (with the WorldPop caveat); tree cover; built-up share; cool-season median; and the roof caveat from chunk 1 where it applies.
- Before any ward is chosen, the panel shows the county summary and the five hottest wards by population-weighted surface temperature, as links.
- From zoom 14, clicking a building shows a small popup: its surface temperature difference, with the note "describes the area of about 100 m around this building".

## Shareable view (must)

Write the basemap, active layers, opacities, compare state, selected ward and map position into the URL hash, and restore them on load. Add a "Copy link" button and a "Reset view" button.

## Accessibility (must)

Everything works by keyboard; focus is always visible; nothing needs hover; the panel's numbers are plain text a screen reader can read; at 375 px nothing overlaps.

## Done when

Every control works at 375 px and 1440 px, by mouse, touch emulation and keyboard; screenshots of the default view, a selected ward, compare mode, the building popup and the phone bottom sheet are in `outputs/screenshots/v2/chunk5/`; the commit "v2 chunk 5: explorer dashboard" is made.
