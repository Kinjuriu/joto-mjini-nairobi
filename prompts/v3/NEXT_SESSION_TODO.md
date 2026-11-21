# What is still to do (16 November 2026)

Written by Claude after Opus's census and schools run (commit 984bb3c2). Workshop: Thursday 26 November; expression of interest closes Friday 20 November.

Rules for whoever picks this up: read CLAUDE.md, DESIGN_RULES.md (with the Joto Mjini palette at the bottom) and DECISIONS.md up to D55 first. Plain English, no em dashes, no "not X, but Y", every number from `analysis/results*.json` through `{{path|format}}`. Check every change in the browser at 1440 px and 375 px.

## A. Writing (the [[COPY]] placeholders)

Stephane wants these in her voice; draft them for her to edit, plainly marked as drafts.

1. `site/index.html` intro: the story section heading and two or three opening paragraphs (who feels Nairobi's heat, where, why it matters now).
2. `site/index.html` intro aside: four sentences on surface temperature versus air temperature.
3. Hot mornings animation: heading and two short paragraphs.
4. Ward cover table: heading.
5. Nairobi grows animation: heading and one paragraph on where the city filled in.
6. Day of heat chart: heading and two short paragraphs (warms fast after sunrise, peaks around midday, cools after 15:00; 3 km data shows the region, not neighbourhoods; at noon the plains around Nairobi were hotter than the county).
7. `site/src/story/chapters.js`: "Nairobi from space" card sentence; "City centre and Industrial Area" card (the downtown grid and the OSM Industrial Area); "Islands of cool" card.
8. Byline and citation: Stephane's surname, published and updated dates, the site URL (lines 34 and 324 of `index.html`).

## B. Headline and numbers (needs Stephane's answer to QUESTIONS 11)

9. Retire the pooled gap `q2.gap_c` (13.5 °C) and `q2.hot_areas_median_c`: the meta description (line 7), the H1 (line 32), the city centre card's "Difference" row and note (chapters.js lines 118 and 120). Suggested H1: "On hot mornings, the ground in Nairobi's Industrial Area is {{q2.industrial_gap_c|c}} hotter than its forests"; card rows "City centre: {{q2.cbd_gap_c|c}} hotter" and "Industrial Area: {{q2.industrial_gap_c|c}} hotter".
10. The forests card still lists City Park and "Half of the county's ground", which the map no longer shows; keep only the three outlined forests.
11. The day-of-heat chart title and caption type "26 °C" and "hotter at noon" by hand; move them into `results_extra.json` and use placeholders.

## C. Schools on the site (new, from Opus's data)

12. Add a story chapter or interlude: "How many schools sit on the hottest ground" (567 of 3,712, 15.3 %; 72.6 % on ground hotter than the median; Kangemi 92 of 127; Viwandani 33 of 40), with the caveats: ground temperature at about 10:43, not classroom temperature; the school list is a broad map, some Ministry points up to 300 m off.
13. Add a "Schools" layer to the explorer (points coloured by surface temperature), and school counts to the ward panel.
14. Add the schools and census files to the Resources section, and the sources (Ministry list via the World Bank, OpenStreetMap, KNBS 2019 census Volumes II to IV) to Methods.
15. If schools are on the site, the expression of interest's last sentence ("Next, I will map which schools…") can become "I have mapped…"; update `docs/application_draft.md`.

## D. Data decisions waiting for Stephane (QUESTIONS 10, 12, 13)

16. Scale WorldPop to census locations and switch the site's ward populations (fixes Woodley and Kangemi)? If yes, every population number and the ten-hottest list may change; re-run the ward block charts (`src/animations/ward_blocks.py`) and check the TOP10, HOT5 and COOL5 lists in `chapters.js`.
17. Push Volume IV to the public census repo once Stephane has checked it.
18. School register (KEMIS or NEMIS) to check the school map, if she can get it.

## E. Methods, credits and checks

19. Methods and Data list: add Copernicus hourly LST (CLMS), EOxCloudless 2025 imagery (CC BY-NC-SA 4.0), the census volumes, school sources, forests from OpenStreetMap; remove anything no longer used (Mapbox satellite unless it works again).
20. Re-run `analysis` checks and the build (`npm run build`), fix warnings, and confirm no `{{` or `[[COPY` is left in the built page.
21. Full QA pass from `prompts/04_qa_and_report.md` at 375 px and 1440 px: every story chapter, swipe map, explorer (layers, ward search, compare, copy link), videos with pause buttons, keyboard and reduced motion.
22. Re-record the offline walkthrough video (`outputs/demo/`) after the text is in, as the workshop backup.

## F. Going live and the workshop

23. GitHub Pages: switch it on for `Kinjuriu/joto-mjini-nairobi`, build with the Mapbox token supplied at build time (never committed), and check the live site. Add the live URL to the Mapbox token's URL restrictions.
24. Esri imagery: when `VITE_ESRI_KEY` is in `site/.env.local`, add Esri World Imagery as the sharper imagery option with "Powered by Esri" and its credit.
25. Mapbox account (QUESTIONS 9): satellite still refused with HTTP 429; Stephane to check Statistics and Billing.
26. Expression of interest: submit before 20 November (draft in `docs/application_draft.md`); consider emailing the organisers to ask what the day is for.
27. A ten-minute presentation for 26 November (outline in `docs/presentation_outline.md`) with static screenshots as an offline fallback.
28. After the workshop: research paper outline (heat exposure of residents, schools and health facilities; builds on Nkugwa and Loyo 2026), possibly with Stephane's sister for the health side.
