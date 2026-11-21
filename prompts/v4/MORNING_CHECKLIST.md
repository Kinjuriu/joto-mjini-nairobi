# Morning check, 21 November 2026 (about 15 minutes)

Branch `workshop-schools-20nov` (commits 40d70d4c and 7d340965; nothing pushed). Mapbox was blocked in Claude's sandboxes, so the maps were built but not seen. Everything else (text, cards, charts, phone layout) was checked in headless Chrome; screenshots are in `prompts/v4/qa_20nov/`.

## Run it

```
cd ~/Desktop/joto-mjini/site
git checkout workshop-schools-20nov
npm run dev
```

Open http://localhost:5173/joto-mjini-nairobi/ in Chrome, once at full width and once with the window narrow (or Chrome's phone view, 375 px).

## Check the maps

- [ ] Map block 1 (heat divide): six steps, from "Nairobi from space" to "Five hot wards, five cool wards". "The city's cool islands" shows false colour with the three forests outlined.
- [ ] Map block 2 (children): "Who lives on the hottest ground", then "Where children go to school": every school is a dot coloured blue to red, with a legend titled "Each dot is a school...". Are the dots too big or too small at county zoom?
- [ ] Kangemi, Viwandani and Karen steps: the map flies to the ward, the ward is outlined, the dots sit over the heat layer, and the card does not cover the ward (phone: the ward shows above the card).
- [ ] Map block 3 (under "More on Nairobi's heat"): land cover, rooftops, Karura edge, Kawangware and Kileleshwa, people by heat, growth 1990 and 2020.
- [ ] Explorer: tick "Schools, by the heat around them": the dots appear on top of the heat layer and the legend changes; tick another layer and the schools stay. Search "Kangemi": the ward panel shows "Hotter half of Nairobi", the children, the schools and the tree cover.

## Decide

- [ ] The new headline (QUESTIONS 14) and the moved chapters (QUESTIONS 15).
- [ ] Read the text marked `DRAFT 20 Nov (Claude)` in `site/index.html` and `site/src/story/chapters.js`, and edit it in your voice.
- [ ] Then tell Claude: fixes, the slides, and whether to push and switch on GitHub Pages.
