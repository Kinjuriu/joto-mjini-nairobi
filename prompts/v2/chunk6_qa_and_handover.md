# v2 chunk 6: QA and handover (budget about 1 hour)

Check the whole v2 site like a careful reviewer, fix what you can, and leave Stephane and her reviewer (Claude) everything they need to judge it quickly.

## 1. Automated checks (must)

1. Build the site (`npm run build`) and serve it with `npx vite preview`. Fix every build warning that points to a real problem.
2. With Playwright: load the page at 375 px and 1440 px, scroll slowly through the whole story, and record any console errors, failed requests and missing tiles (404s under `/tiles/`). Fix them.
3. Count Mapbox map instances on the page (aim for no more than four) and note it, since each counts as a map load.
4. Report the built site's total size and the size of `site/public/tiles/` and `site/public/media/`.
5. Re-run the notebooks and the analysis checks; confirm nothing broke.

## 2. Compare with NASA (must)

Make side-by-side comparison images with Python (Pillow): for each pairing below, NASA's screenshot on the left, yours on the right, same height, saved to `outputs/screenshots/v2/compare_with_nasa/`:

| NASA | Ours |
|---|---|
| `nasa/05_overview_card_floating_over_landcover.png` | chapter 3 (land cover) |
| `nasa/06_true_colour_satellite_chapter.png` | chapter 1 (Nairobi from space) |
| `nasa/07_false_colour_chapter_vegetation_green.png` | chapter 2 (where the trees are) |
| `nasa/08_zoomed_in_with_clear_place_labels.png` | chapter 5 (city centre and Industrial Area, heat on) |
| `nasa/01_animated_wind_gif_beside_text.png` | the "Every clear hot-season morning" interlude |
| `nasa/03_text_beside_fullbleed_landcover_map.png` | the land cover heatmap table interlude |
| `nasa/02_chart_with_highlighted_period.png` | the highlighted air temperature chart |

Look at each pair and write two honest lines per pair in the report: what now matches, and what still falls short.

## 3. Human-eye pass (must)

Using your screenshots: labels readable over every layer; hot and cool clearly different; no blocky pixels at zoom 13; cards never hide the place they describe; legends never collide; videos have posters, captions and working pause buttons; nothing appears twice; the explorer works on a phone. Run the pre-ship checklist from `prompts/04_qa_and_report.md` again and tick it honestly in `site/SITE_REPORT.md`.

## 4. Offline backup for the workshop (must)

Record a walkthrough video of the story with Playwright's video recording at 1440 by 900 (scroll at reading pace through both story blocks, pause on each chapter, show the explorer selecting two wards), saved as `outputs/demo/joto-mjini-walkthrough.webm`. If the internet fails at the workshop, Stephane can play this.

## 5. `MORNING_REPORT_v2.md` (must)

Under two screens, with these headings:

1. **Status:** what works, how to open it (`cd site && npm run dev`, then the local address, which includes `/joto-mjini-nairobi/`).
2. **What changed since v1,** chunk by chunk.
3. **Data fixes and changed numbers** from chunk 1: the ward boundary source, the new F3, the roof check result, and every headline number that moved.
4. **Screenshots to look at first:** the ten most telling, by path.
5. **What still falls short of NASA's look,** from the comparison pairs.
6. **Decisions I made for you** and **questions for you.**
7. **Suggested next run.**
8. **Time used** per chunk.

Commit "v2 chunk 6: QA and handover" and stop.
